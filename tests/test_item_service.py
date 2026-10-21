from app.models import Categoria, Campo, Item
from app import db
from app.services.item_service import (
    filter_items_by_categoria,
    get_items_for_inventory,
    create_item,
    create_product,
    consume_item,
    add_stock,
)
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

    # filter by date (YYYY-MM-DD) - should match both representations of the same date
    filtros = {'Fecha': '2023-06-01'}
    out = filter_items_by_categoria(cat.id, filtros)
    assert len(out) == 2
    descriptions = {i.datos['Descripcion'] for i in out}
    assert {'Laptop Dell', 'Monitor'}.issubset(descriptions)

    # filter by date (DD/MM/YYYY) - should behave the same (match by date)
    filtros = {'Fecha': '01/06/2023'}
    out = filter_items_by_categoria(cat.id, filtros)
    assert len(out) == 2
    descriptions = {i.datos['Descripcion'] for i in out}
    assert {'Laptop Dell', 'Monitor'}.issubset(descriptions)


def test_consume_item_and_create(app):
    cat = Categoria(nombre='Another')
    db.session.add(cat)
    db.session.commit()

    item = create_item(cat.id, {'Field': 'Value'}, usuario_id=1)
    assert item.id is not None

    consumed = consume_item(item.id, usuario_id=1, destino='Bodega', observacion='Prueba')
    assert consumed.deleted_at is None
    assert consumed.stock == 0
    assert consumed.estado == 'Sin stock'
    inventory_items, _ = get_items_for_inventory([cat], [cat.id], mostrar_consumidos=False)
    assert any(inventory_item.id == item.id for inventory_item in inventory_items)


def test_inventory_items_are_alphabetical(app):
    categoria = Categoria(nombre='Orden alfabetico de productos')
    db.session.add(categoria)
    db.session.flush()
    items = [
        Item(categoria_id=categoria.id, datos={'Descripción': 'Zebra'}),
        Item(categoria_id=categoria.id, datos={'Descripción': 'alfa'}),
        Item(categoria_id=categoria.id, datos={'Descripción': 'Beta'}),
    ]
    db.session.add_all(items)
    db.session.commit()

    ordered_items, _ = get_items_for_inventory(
        [categoria],
        [categoria.id],
        mostrar_consumidos=False,
    )

    assert [item.datos['Descripción'] for item in ordered_items] == ['alfa', 'Beta', 'Zebra']


def test_stock_can_be_added_and_consumed_in_quantities(app):
    cat = Categoria(nombre='Stock quantity test')
    db.session.add(cat)
    db.session.commit()

    item = create_item(cat.id, {'Producto': 'Tornillo'}, usuario_id=1, cantidad=5)
    assert item.stock == 5

    add_stock(item.id, usuario_id=1, cantidad=3, observacion='Reposición')
    assert item.stock == 8

    consume_item(item.id, usuario_id=1, destino='Taller', observacion='', cantidad=6)
    assert item.stock == 2
    assert item.deleted_at is None

    try:
        consume_item(item.id, usuario_id=1, destino='Taller', observacion='', cantidad=3)
        assert False, 'No se debe permitir consumir más stock del disponible'
    except ValueError as error:
        assert 'stock suficiente' in str(error)
    assert item.stock == 2

    consume_item(item.id, usuario_id=1, destino='Taller', observacion='', cantidad=2)
    assert item.stock == 0
    assert item.deleted_at is None
    inventory_items, _ = get_items_for_inventory([cat], [cat.id], mostrar_consumidos=False)
    assert any(inventory_item.id == item.id for inventory_item in inventory_items)

    add_stock(item.id, usuario_id=1, cantidad=4)
    assert item.stock == 4
    assert item.deleted_at is None


def test_create_product_starts_without_stock(app):
    cat = Categoria(nombre='New product test')
    db.session.add(cat)
    db.session.commit()

    product = create_product(cat.id, 'Disco SSD 480 Kingston', 'SA400S37/480G', usuario_id=1)

    assert product.datos == {
        'Descripción': 'Disco SSD 480 Kingston',
        'Modelo': 'SA400S37/480G',
    }
    assert product.stock == 0
    assert product.estado == 'Sin stock'
    add_stock(product.id, usuario_id=1, cantidad=3)
    assert product.stock == 3
    assert product.deleted_at is None
