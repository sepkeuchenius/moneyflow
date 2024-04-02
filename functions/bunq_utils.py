from bunq.sdk.model.generated import endpoint
from bunq.sdk.http.pagination import Pagination
from typing import List, Generator, Union
import datetime
from bunq.sdk.json.converter import serialize
from bunq.sdk.context.api_context import ApiEnvironmentType, ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from db_utils import _user_ref, _payments_ref
from firebase_functions import params

ENVIRONMENT_TYPE = ApiEnvironmentType.PRODUCTION
# API_KEY = "28f154a0578d1ba0aa1e880d3549ad8c77eaea66340d6559dd78ccbaf5bad008"
DEVICE_DESCRIPTION = "firebase"

OAUTH_URL = "https://oauth.bunq.com"
OAUTH_API_URL = "https://api.oauth.bunq.com/v1"
AUTH_URL = f"{OAUTH_URL}/auth"
TOKEN_URL = f"{OAUTH_API_URL}/token"
CALLBACK_URL = "https://moneyflow-e831b.web.app/auth"
BUNQ_OAUTH_CLIENT_ID = params.SecretParam("BUNQ_OAUTH_CLIENT_ID")
BUNQ_CLIENT_SECRET = params.SecretParam("BUNQ_CLIENT_SECRET")

AUTH_PARAMS = {
    "response_type": "code",
    "redirect_uri": CALLBACK_URL,
    "client_id": BUNQ_OAUTH_CLIENT_ID.value,
}
PAYMENT_TO_ACCOUNT = {}


def _get_auth_url():
    import urllib.parse

    return f"{AUTH_URL}?{urllib.parse.urlencode(AUTH_PARAMS)}"


def _get_user_context_blob(context_description):
    from firebase_admin import storage

    bucket = storage.bucket("moneyflow-e831b.appspot.com")
    return bucket.blob(f"{context_description}.json")


def _get_user_context_description(uid):
    return f"{DEVICE_DESCRIPTION}-{uid}"


def _get_api_context(uid):
    context_description = _get_user_context_description(uid)
    context_blob = _get_user_context_blob(context_description)
    if context_blob.exists():
        context_json = context_blob.download_as_text()
        return ApiContext.from_json(context_json)
    else:
        return _create_api_context(_get_user_access_token(uid), uid)


def _create_api_context(token, uid):
    context_description = _get_user_context_description(uid)
    context_blob = _get_user_context_blob(context_description)
    api_context = ApiContext.create(
        ENVIRONMENT_TYPE, token, context_description, all_permitted_ip=["*"]
    )
    api_context.ensure_session_active()
    api_context.save(context_description)
    context_blob.upload_from_string(api_context.to_json())
    return api_context


def generate_payments(
    subaccount_id,
) -> Generator[endpoint.Payment, None, None]:
    pagination = Pagination()
    pagination.count = 200
    pagination_params = pagination.url_params_count_only
    while True:
        page = endpoint.Payment.list(
            params=pagination_params, monetary_account_id=subaccount_id
        )
        yield from page.value
        if not page.pagination.has_previous_page():
            break
        pagination_params = page.pagination.url_params_previous_page


def get_payment_features(uid, payment_id):
    if saved_features := get_saved_payment_features(payment_id):
        return saved_features
    payment_account = _get_payment_account(uid, payment_id)
    return _get_payment_features(
        endpoint.Payment.get(payment_id, monetary_account_id=payment_account).value
    )


def get_saved_payments_with_features(uid) -> list:
    return [
        _payments_ref().get(payment_id).get()
        for payment_id in _user_ref(uid).child("payments").get()
    ]


def get_all_payments(uid) -> dict:
    return {
        payment_id: _payments_ref().get(payment_id).get()
        for payment_id in _user_ref(uid).child("payments").get()
    }


def get_saved_payments_with_annotation(uid):
    if payments := _user_ref(uid).child("payments").get():
        return [
            payment
            for payment_id, payment in payments.items()
            if "annotation" in payment
        ]
    return []


def get_saved_payment_features(payment_id):
    return _get_saved_payment_info(payment_id).get("features")


def _get_saved_payment_info(payment_id):
    return _payments_ref().child(payment_id).get()


def _get_payment_features(payment: endpoint.Payment):
    return {
        "amount": payment.amount.value,
        "counterparty_name": payment.counterparty_alias.pointer.name,
        "description": payment.description,
        "counterparty_iban": payment.counterparty_alias.pointer.value,
        "user_id": payment._counterparty_alias._determine_user_id(),
        "counterparty_monetary_account_id": payment._counterparty_alias._determine_monetary_account_id(),
        "created": payment.created,
    }


def _get_date(payment: endpoint.Payment) -> datetime.datetime:
    return datetime.datetime.fromisoformat(payment.created)


def _get_payments_for_accounts(
    account_ids: list, start_date: datetime.datetime
) -> List[endpoint.Payment]:
    global PAYMENT_TO_ACCOUNT
    payments = []
    for account_id in account_ids:
        for payment in generate_payments(account_id):
            PAYMENT_TO_ACCOUNT[payment.id_] = account_id
            if _get_date(payment) > start_date:
                if payment.counterparty_alias.pointer.value not in _own_ibans():
                    payments.append(payment)
            else:
                break
    return sorted(payments, key=_get_date)


def _get_serialized_accounts():
    return [serialize(account) for account in _get_accounts()]


def _own_ibans():
    return []


def _get_accounts():
    # list our own ibans
    account_ids: List[endpoint.MonetaryAccount] = endpoint.MonetaryAccount.list().value
    accounts = []
    for account_id in account_ids:
        try:
            account: Union[
                endpoint.MonetaryAccountBank, endpoint.MonetaryAccountJoint
            ] = account_id.get_referenced_object()
            accounts.append(account)
        except Exception as e:
            print(e)
            continue
    return accounts


def _get_user_access_token(uid):
    from firebase_admin import db

    return db.reference("users").child(uid).get().get("bunq_access_token")


def _get_access_token(code):
    import requests

    token_request = requests.post(
        TOKEN_URL,
        params={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": CALLBACK_URL,
            "client_id": BUNQ_OAUTH_CLIENT_ID.value,
            "client_secret": BUNQ_CLIENT_SECRET.value,
        },
    )
    if token_request.ok:
        print(token_request.text)
        response: dict = token_request.json()
        access_token = response.get("access_token")
        return access_token
    else:
        print("Something went wrong getting access token")
        print(token_request.status_code)
        print(token_request.text)
        return None


def _ensure_api_context(uid):
    api_context = _get_api_context(uid)
    api_context.ensure_session_active()
    BunqContext.load_api_context(api_context)


def _get_access_token_by_code(uid, code):
    from firebase_admin import db

    bunq_access_token = _get_access_token(code)
    if bunq_access_token:
        _create_api_context(bunq_access_token, uid)
        db.reference("users").child(uid).update(
            {
                "bunq_access_token": bunq_access_token,
            }
        )

        return "OK"
    else:
        raise ValueError("Could not get access token")


def get_serialized_payments(accounts: List[str], start_date: datetime.datetime):
    payments = []
    for payment in _get_payments_for_accounts(accounts, start_date):
        payment_info = serialize(payment)
        payment_info.update({"features": _get_payment_features(payment)})
        payments.append(payment_info)
    return payments


def _get_payment_account(uid, payment_id):
    return _user_ref(uid).child("payments").child(str(payment_id)).get().get("account")
