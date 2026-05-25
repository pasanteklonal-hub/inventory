from ..models import Usuario
from .. import db
from ..dao.user_dao import get_by_username, get_by_email


def authenticate_user(username, password):
    if not username or not password:
        return None

    user = get_by_username(username)
    if user and user.check_password(password):
        return user
    return None


def get_user_by_id(user_id):
    if not user_id:
        return None
    return Usuario.query.get(int(user_id))


def register_user(username, email, password, password_confirm):
    if not username or not email or not password:
        return 'Todos los campos son obligatorios'

    if password != password_confirm:
        return 'Las contraseñas no coinciden'

    if len(password) < 6:
        return 'La contraseña debe tener al menos 6 caracteres'

    if get_by_username(username):
        return 'El usuario ya existe'

    if get_by_email(email):
        return 'El email ya existe'

    user = Usuario(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return None
