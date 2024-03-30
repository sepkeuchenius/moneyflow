# Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

from firebase_functions import https_fn
from firebase_admin import initialize_app
from bunq_utils import (
    _get_serialized_accounts,
    _get_user_access_token,
    _get_auth_url,
    _ensure_api_context,
    _get_access_token_by_code,
    _get_serialized_payments,
    get_payment_features,
    get_saved_payments_with_annotation,
    get_saved_payments_with_features,
    BUNQ_CLIENT_SECRET,
    BUNQ_OAUTH_CLIENT_ID,
    AUTH_PARAMS
)
from db_utils import _user_ref, _ensure_user_account
import info_model

app = initialize_app()


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def get_auth_url(req: https_fn.CallableRequest):
    return _get_auth_url()


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def save_user(req: https_fn.CallableRequest):
    _ensure_user_account(req.auth.uid)
    _user_ref(req.auth.uid).set(
        {
            "google_access_token": req.data["google_access_token"],
        }
    )
    return "OK"


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def save_token(req: https_fn.CallableRequest):
    return _get_access_token_by_code(req.auth.uid, req.data.get("code"))


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def has_saved_access_token(req: https_fn.CallableRequest):
    print(AUTH_PARAMS)
    _ensure_user_account(req.auth.uid)
    return _get_user_access_token(req.auth.uid) is not None


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def get_accounts(req: https_fn.CallableRequest):
    _ensure_api_context(req.auth.uid)
    return _get_serialized_accounts()


def _get_usable_accounts(uid):
    return _user_ref(uid).get().get("accounts")


def _get_start_date(uid):
    import datetime

    return datetime.datetime.fromisoformat(_user_ref(uid).get().get("start_date"))


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def get_payments(req: https_fn.CallableRequest):
    _ensure_api_context(req.auth.uid)
    _ensure_user_account(req.auth.uid)
    payments = _get_serialized_payments(
        _get_usable_accounts(req.auth.uid), _get_start_date(req.auth.uid)
    )
    payments_in_timeframe = _get_payments_in_timeframe(
        payments, req.data.get("begin"), req.data.get("end")
    )
    user_payments = _user_ref(req.auth.uid).child("payments")
    for payment in payments_in_timeframe:
        user_payments.child(str(payment.get("id"))).update(
            {
                "account": payment.get("monetary_account_id"),
                "features": payment.get("features"),
            }
        )
    return payments


@https_fn.on_call(region="europe-west1")
def get_options(req: https_fn.CallableRequest):
    return info_model.generate_list_of_categories(
        info_model.OUTGOING_INFORMATION_MODEL, []
    )


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def set_usable_accounts(req: https_fn.CallableRequest):
    _ensure_user_account(req.auth.uid)
    _user_ref(req.auth.uid).update(
        {"accounts": req.data.get("accounts"), "start_date": req.data.get("start_date")}
    )
    return "OK"


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def get_payment_prediction(req: https_fn.CallableRequest):
    if features := get_payment_features(req.auth.uid, req.data):
        counterparty_name = features.get("counterparty_name")
        for payment in get_saved_payments_with_features(req.auth.uid):
            if (
                payment.get("features").get("counterparty_name") == counterparty_name
                and "annotation" in payment
            ):
                return payment.get("annotation")

    return None


@https_fn.on_call(region="europe-west1")
def get_payment_annotation(req: https_fn.CallableRequest):
    if (
        payment_annotation := _user_ref(req.auth.uid)
        .get()
        .get("payments", {})
        .get(req.data)
    ):
        return payment_annotation.get("annotation")
    return None


@https_fn.on_call(region="europe-west1")
def set_payment_annotation(req: https_fn.CallableRequest):
    import datetime

    _ensure_user_account(req.auth.uid)
    _user_ref(req.auth.uid).child("payments").update(
        {
            req.data.get("id"): {
                "annotation": req.data.get("annotation"),
                "annotated_at": datetime.datetime.now().isoformat(),
                "features": get_payment_features(req.auth.uid, req.data.get("id")),
            }
        }
    )
    return "OK"


def _get_date(payment):
    import datetime

    return datetime.datetime.fromisoformat(payment.get("features").get("created"))


@https_fn.on_call(region="europe-west1")
def get_chart(req: https_fn.CallableRequest):
    from create_chart_text import create_chart

    _user_ref(req.auth.uid).child("payments").get()
    payments = get_saved_payments_with_annotation(req.auth.uid)
    payments_in_timeframe = _get_payments_in_timeframe(
        payments, req.data.get("begin"), req.data.get("end")
    )
    sorted(payments_in_timeframe, key=_get_date)
    start_date = _get_date(payments_in_timeframe[0]).strftime("%Y-%m-%d")
    end_date = _get_date(payments_in_timeframe[-1]).strftime("%Y-%m-%d")
    return {
        "chart": create_chart(payments_in_timeframe),
        "begin": start_date,
        "end": end_date,
    }


def _get_payments_in_timeframe(payments, begin: str, end: str):
    import datetime

    payments_in_timeframe = []
    if begin or end:
        begin_time = datetime.datetime.fromisoformat(begin) if begin else None
        end_time = datetime.datetime.fromisoformat(end) if end else None
        for payment in payments:
            payment_date = _get_date(payment)
            if ((not begin_time) or payment_date > begin_time) and (
                (not end_time) or payment_date < end_time
            ):
                payments_in_timeframe.append(payment)
    else:
        payments_in_timeframe = payments
    return payments_in_timeframe
