from app.services.auth_service import register_user, authenticate_user, get_user_by_id
from app import db
from app.models import Usuario


def test_register_and_authenticate(app):
    # register
    err = register_user('usr1', 'u1@example.com', 'password', 'password')
    assert err is None

    # duplicate
    err = register_user('usr1', 'u1@example.com', 'password', 'password')
    assert err is not None

    # authenticate
    user = authenticate_user('usr1', 'password')
    assert user is not None

    # get by id
    found = get_user_by_id(user.id)
    assert found is not None
    assert found.username == 'usr1'
