from app.models import Categoria, Campo, Item
from app import db
from app.services.item_service import filter_items_by_categoria, create_item, consume_item
from datetime import datetime


def test_filter_by_options_and_text(app):
    # arrange
    cat = Categoria(nombre='TestCat')
    db.session.add(cat)
    db.session.flush()

    campo_sel = Campo(categoria_id=cat.id, nombre='Estado', tipo='select', opciones='Nuevo,Usado', requerido=False)
    campo_txt = Campo(categoria_id=cat.id, nombre='Descripcion', tipo='text', requerido=False)
    campo_date = Campo(categoria_id=cat.id, nombre='Fecha', tipo='date', requerido=False)
    db.session.add_all([campo_sel, campo_txt, campo_date])
    db.session.commit()

    item1 = Item(categoria_id=cat.id, datos={'Estado': 'Nuevo', 'Descripcion': 'Laptop Dell', 'Fecha': '2023-06-01'})
    item2 = Item(categoria_id=cat.id, datos={'Estado': 'Usado', 'Descripcion': 'Monitor', 'Fecha': '01/06/2023'})
    item3 = Item(categoria_id=cat.id, datos={'Estado': 'Nuevo', 'Descripcion': 'Cable', 'Fecha': '2023-06-02'})
    db.session.add_all([item1, item2, item3])
    db.session.commit()

    # act & assert: filter by select option
    filtros = {'Estado': 'Nuevo'}
    out = filter_items_by_categoria(cat.id, filtros)
    assert len(out) == 2
    assert all(i.datos['Estado'] == 'Nuevo' for i in out)

    # filter by text substring
    filtros = {'Descripcion': 'lap'}
    out = filter_items_by_categoria(cat.id, filtros)
    assert len(out) == 1
    assert out[0].datos['Descripcion'] == 'Laptop Dell'

    # filter by date (YYYY-MM-DD)
    filtros = {'Fecha': '2023-06-01'}
    out = filter_items_by_categoria(cat.id, filtros)
    assert len(out) == 1
    assert out[0].datos['Descripcion'] == 'Laptop Dell'

    # filter by date (DD/MM/YYYY)
    filtros = {'Fecha': '01/06/2023'}
    out = filter_items_by_categoria(cat.id, filtros)
    assert len(out) == 1
    assert out[0].datos['Descripcion'] == 'Monitor'


def test_consume_item_and_create(app):
    cat = Categoria(nombre='Another')
    db.session.add(cat)
    db.session.commit()

    item = create_item(cat.id, {'Field': 'Value'}, usuario_id=1)
    assert item.id is not None

    consumed = consume_item(item.id, usuario_id=1, destino='Bodega', observacion='Prueba')
    assert consumed.deleted_at is not None
