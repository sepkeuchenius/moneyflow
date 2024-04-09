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
    get_serialized_payments,
    get_payment_features,
    get_saved_payments_with_annotation,
    get_saved_payments_with_features,
    get_all_payments,
    BUNQ_CLIENT_SECRET,
    BUNQ_OAUTH_CLIENT_ID,
    AUTH_PARAMS,
)
from db_utils import _user_ref, _ensure_user_account, _payments_ref
import info_model
import datetime

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
    _user_ref(req.auth.uid).update(
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
    all_accounts = _get_serialized_accounts()
    usable_accounts = _get_usable_accounts(req.auth.uid) or []
    for account in all_accounts:
        account["usable"] = str(account.get("id")) in usable_accounts
    return all_accounts


def _get_usable_accounts(uid):
    return _user_ref(uid).get().get("accounts")


def _get_selected_date(date_type: str, selected_iso: str, uid) -> datetime.datetime:
    if selected_iso:
        time = datetime.datetime.fromisoformat(selected_iso)
        _user_ref(uid).child(date_type).set(time.isoformat())
        return time
    elif user_saved_date := _user_ref(uid).child(date_type).get():
        return datetime.datetime.fromisoformat(user_saved_date)
    elif date_type == "start_date":
        return datetime.datetime.now() - datetime.timedelta(days=3)
    else:
        return datetime.datetime.now()


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def get_payments(req: https_fn.CallableRequest):
    _ensure_api_context(req.auth.uid)
    _ensure_user_account(req.auth.uid)
    if usable_accounts := _get_usable_accounts(req.auth.uid):
        payments = get_serialized_payments(
            usable_accounts,
            _get_selected_date("start_date", req.data.get("begin"), req.auth.uid),
        )
        if payments_in_timeframe := _filter_payments_in_timeframe(
            payments, req.data.get("begin"), req.data.get("end"), req.auth.uid
        ):
            for payment in payments:
                _payments_ref().child(str(payment.get("id"))).update(
                    {
                        "account": payment.get("monetary_account_id"),
                        "features": payment.get("features"),
                    }
                )
                _user_ref(req.auth.uid).child("payments").push(payment.get("id"))
                start_date = _get_date(payments_in_timeframe[0]).strftime("%Y-%m-%d")
                end_date = _get_date(payments_in_timeframe[-1]).strftime("%Y-%m-%d")
                for payment in payments:
                    _user_ref(req.auth.uid).child("payments").child(
                        str(payment.get("id"))
                    ).update(
                        {
                            "account": payment.get("monetary_account_id"),
                            "features": payment.get("features"),
                        }
                    )
                return {
                    "payments": payments_in_timeframe,
                    "begin": start_date,
                    "end": end_date,
                }
    return {
        "payments": [],
        "begin": _get_selected_date("start_date", req.data.get("begin"), req.auth.uid).strftime("%Y-%m-%d"),
        "end": _get_selected_date("end_date", req.data.get("end"), req.auth.uid).strftime("%Y-%m-%d"),
    }


@https_fn.on_call(region="europe-west1")
def get_options(req: https_fn.CallableRequest):
    [incoming_info_model, outgoing_info_model] = info_model.get_user_model(
        req.auth.uid
    ).values()
    outgoing_categories = info_model.generate_list_of_categories(
        incoming_info_model, []
    )
    incoming_categories = info_model.generate_list_of_categories(
        outgoing_info_model, []
    )
    return outgoing_categories + incoming_categories + info_model.SPECIAL_CATEGORIES


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def set_usable_accounts(req: https_fn.CallableRequest):
    _ensure_user_account(req.auth.uid)
    _user_ref(req.auth.uid).update({"accounts": req.data.get("accounts")})
    return "OK"


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def get_usable_accounts(req: https_fn.CallableRequest):
    _ensure_user_account(req.auth.uid)
    return _user_ref(req.auth.uid).child("accounts").get()


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


@https_fn.on_call(
    region="europe-west1", secrets=[BUNQ_OAUTH_CLIENT_ID, BUNQ_CLIENT_SECRET]
)
def get_batch_prediction(req: https_fn.CallableRequest):
    all_payments = get_all_payments(req.auth.uid)
    predictions = []
    for payment_id in req.data:
        if features := all_payments.get(payment_id).get("features"):
            counterparty_name = features.get("counterparty_name")
            for payment in all_payments:
                if (
                    payment.get("features", {}).get("counterparty_name")
                    == counterparty_name
                    and "annotation" in payment
                ):
                    predictions.append(payment.get("annotation"))
                    break
        predictions.append(None)
    return predictions


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
    payments_in_timeframe = _filter_payments_in_timeframe(
        payments, req.data.get("begin"), req.data.get("end"), req.auth.uid
    )
    sorted(payments_in_timeframe, key=_get_date)
    if len(payments_in_timeframe) > 0:
        start_date = _get_date(payments_in_timeframe[0]).strftime("%Y-%m-%d")
        end_date = _get_date(payments_in_timeframe[-1]).strftime("%Y-%m-%d")
        return {
            "chart": create_chart(payments_in_timeframe, req.auth.uid),
            "begin": start_date,
            "end": end_date,
        }
    return {"chart": None, "begin": None, "end": None}


@https_fn.on_call(region="europe-west1")
def get_user_model(req: https_fn.CallableRequest):
    return info_model.get_user_model(req.auth.uid)


@https_fn.on_call(region="europe-west1")
def set_user_model(req: https_fn.CallableRequest):
    import json

    model = json.loads(req.data)
    if model.get("in") and model.get("out"):
        return _user_ref(req.auth.uid).child("model").set(req.data)


def _filter_payments_in_timeframe(
    payments, selected_begin_iso: str, selected_end_iso: str, uid
):
    begin_time = _get_selected_date(
        date_type="start_date", selected_iso=selected_begin_iso, uid=uid
    )
    end_time = _get_selected_date(
        date_type="end_date", selected_iso=selected_end_iso, uid=uid
    )
    payments_in_timeframe = []
    for payment in payments:
        payment_date = _get_date(payment)
        if ((not begin_time) or payment_date > begin_time) and (
            (not end_time) or payment_date < end_time
        ):
            payments_in_timeframe.append(payment)
    return payments_in_timeframe
