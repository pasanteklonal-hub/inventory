from app.services.category_service import (
    create_categoria,
    update_categoria,
    add_campo_to_categoria,
    update_campo_de_categoria,
    delete_categoria,
    delete_campo_from_categoria,
)
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


def test_update_campo_renames_existing_item_data(app):
    categoria = Categoria(nombre='Categoría actualizar campo')
    db.session.add(categoria)
    db.session.flush()
    campo = Campo(
        categoria_id=categoria.id,
        nombre='Estado',
        tipo='text',
        requerido=False,
    )
    item = Item(
        categoria_id=categoria.id,
        datos={'Descripción': 'Monitor', 'Estado': 'Nuevo'},
    )
    db.session.add_all([campo, item])
    db.session.commit()

    error = update_campo_de_categoria(
        categoria,
        campo.id,
        'Condición',
        'select',
        True,
        'Nuevo, Usado',
    )

    assert error is None
    assert campo.nombre == 'Condición'
    assert campo.tipo == 'select'
    assert campo.requerido is True
    assert campo.opciones == 'Nuevo, Usado'
    assert item.datos == {'Descripción': 'Monitor', 'Condición': 'Nuevo'}


def test_update_campo_rejects_duplicate_name_without_changing_data(app):
    categoria = Categoria(nombre='Categoría campos duplicados')
    db.session.add(categoria)
    db.session.flush()
    campo = Campo(categoria_id=categoria.id, nombre='Estado', tipo='text')
    otro_campo = Campo(categoria_id=categoria.id, nombre='Condición', tipo='text')
    item = Item(categoria_id=categoria.id, datos={'Estado': 'Nuevo', 'Condición': 'Usado'})
    db.session.add_all([campo, otro_campo, item])
    db.session.commit()

    error = update_campo_de_categoria(
        categoria,
        campo.id,
        'Condición',
        'text',
        False,
        '',
    )

    assert error is not None
    assert campo.nombre == 'Estado'
    assert item.datos == {'Estado': 'Nuevo', 'Condición': 'Usado'}


def test_delete_categoria_without_products(app):
    categoria = Categoria(nombre='Categoría vacía para eliminar')
    db.session.add(categoria)
    db.session.flush()
    campo = Campo(categoria_id=categoria.id, nombre='Estado', tipo='text')
    db.session.add(campo)
    db.session.commit()
    categoria_id = categoria.id

    error = delete_categoria(categoria)

    assert error is None
    assert Categoria.query.filter_by(id=categoria_id).first() is None
    assert Campo.query.filter_by(id=campo.id).first() is None


def test_delete_categoria_rejects_categories_with_products(app):
    categoria = Categoria(nombre='Categoría con producto')
    db.session.add(categoria)
    db.session.flush()
    item = Item(categoria_id=categoria.id, datos={'Descripción': 'Producto eliminado'}, eliminado=True)
    db.session.add(item)
    db.session.commit()

    error = delete_categoria(categoria)

    assert error == 'No se puede eliminar la categoría porque tiene productos relacionados'
    assert Categoria.query.filter_by(id=categoria.id).first() is not None
    assert Item.query.filter_by(id=item.id).first() is not None
