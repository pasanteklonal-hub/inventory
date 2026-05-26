from app.dao.campo_dao import get_campo_by_id
from app.dao.item_dao import get_items_by_categoria, get_active_items_by_categoria
from app.dao.movimiento_dao import list_movimientos
from app.dao.user_dao import get_by_username, get_by_email
from app import db
from app.models import Categoria, Campo, Item, Usuario, Movimiento


def test_campo_and_item_dao(app):
    cat = Categoria(nombre='DAOcat')
    db.session.add(cat)
    db.session.flush()

    campo = Campo(categoria_id=cat.id, nombre='F', tipo='text')
    db.session.add(campo)
    db.session.commit()

    got = get_campo_by_id(campo.id)
    assert got is not None

    item = Item(categoria_id=cat.id, datos={'F': 'V'})
    db.session.add(item)
    db.session.commit()

    items = get_items_by_categoria(cat.id)
    assert any(i.id == item.id for i in items)

    active = get_active_items_by_categoria(cat.id)
    assert any(i.id == item.id for i in active)


def test_movimiento_and_user_dao(app):
    u = Usuario(username='dao_user', email='dao@example.com')
    u.set_password('pass')
    db.session.add(u)
    db.session.flush()

    mov = Movimiento(item_id=0, usuario_id=u.id, tipo='test')
    db.session.add(mov)
    db.session.commit()

    users_by_name = get_by_username('dao_user')
    users_by_email = get_by_email('dao@example.com')
    assert users_by_name is not None
    assert users_by_email is not None

    movs = list_movimientos()
    assert isinstance(movs, list)
