from app.services.category_service import create_categoria, update_categoria, add_campo_to_categoria, delete_campo_from_categoria
from app.dao.categoria_dao import get_categoria_by_name
from app import db
from app.models import Categoria, Campo, Item


def test_create_and_update_categoria(app):
    err, cat = create_categoria('CatA', 'Desc')
    assert err is None
    assert cat.nombre == 'CatA'

    # duplicate
    err, _ = create_categoria('CatA', 'X')
    assert err is not None

    # update
    err = update_categoria(cat, 'CatA-ed', 'Desc2')
    assert err is None
    c = get_categoria_by_name('CatA-ed')
    assert c is not None


def test_add_and_delete_campo_cleans_items(app):
    cat = Categoria(nombre='CatB')
    db.session.add(cat)
    db.session.commit()

    # add campo
    err = add_campo_to_categoria(cat, 'Modelo', 'text', False, '')
    assert err is None
    campo = Campo.query.filter_by(categoria_id=cat.id, nombre='Modelo').first()
    assert campo is not None

    # add item with that field
    item = Item(categoria_id=cat.id, datos={'Modelo': 'X100'})
    db.session.add(item)
    db.session.commit()

    # delete campo
    err = delete_campo_from_categoria(cat, campo.id)
    assert err is None

    # item should have datos without that key
    it = Item.query.get(item.id)
    assert 'Modelo' not in (it.datos or {})
