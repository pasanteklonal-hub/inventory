from ..models import Usuario


def get_by_username(username):
    if not username:
        return None
    return Usuario.query.filter_by(username=username, deleted_at=None).first()


def get_by_email(email):
    if not email:
        return None
    return Usuario.query.filter_by(email=email, deleted_at=None).first()


def get_by_id(user_id):
    if not user_id:
        return None
    return Usuario.query.get(int(user_id))
