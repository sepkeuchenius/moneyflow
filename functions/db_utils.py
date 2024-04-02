def _user_ref(uid):
    from firebase_admin import db

    return db.reference("users").child(uid)


def _ensure_user_account(user_id):
    from firebase_admin import db

    db.reference("users").child(user_id).update(
        {
            "user_id": user_id,
        }
    )


def _payments_ref():
    from firebase_admin import db

    return db.reference("payments")
