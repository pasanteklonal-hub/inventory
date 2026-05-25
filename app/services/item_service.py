from .. import db
from ..models import Item, Movimiento, Categoria
from ..dao.categoria_dao import get_active_categories


def list_categories():
    return get_active_categories()


def create_item(categoria_id, datos, usuario_id):
    item = Item(categoria_id=categoria_id, datos=datos)
    db.session.add(item)
    db.session.flush()
    movimiento = Movimiento(
        item_id=item.id,
        usuario_id=usuario_id,
        tipo='agregar',
        observacion='Item agregado al inventario',
    )
    db.session.add(movimiento)
    db.session.commit()
    return item


def get_item_or_404(item_id):
    return Item.query.get_or_404(item_id)


def update_item(item, datos, usuario_id):
    item.datos = datos
    db.session.add(item)
    movimiento = Movimiento(
        item_id=item.id,
        usuario_id=usuario_id,
        tipo='editar',
        observacion='Item modificado en inventario',
    )
    db.session.add(movimiento)
    db.session.commit()
    return item


def filter_items_by_categoria(categoria_id, filtros):
    items_q = Item.query.filter_by(categoria_id=categoria_id, deleted_at=None).all()
    if not filtros:
        return items_q

    def matches(item):
        datos = item.datos or {}
        for k, v in filtros.items():
            val = datos.get(k)
            if val is None:
                return False
            if v.lower() not in str(val).lower():
                return False
        return True

    return [item for item in items_q if matches(item)]


def list_items_for_consumption():
    categorias = list_categories()
    items_por_categoria = {
        cat.id: Item.query.filter_by(categoria_id=cat.id, deleted_at=None).all()
        for cat in categorias
    }
    return categorias, items_por_categoria


def get_items_for_inventory(categorias, selected, mostrar_consumidos):
    if not selected:
        seleccionadas = [c.id for c in categorias]
    else:
        seleccionadas = selected

    query = Item.query
    if mostrar_consumidos:
        query = query.filter(Item.categoria_id.in_(seleccionadas), Item.deleted_at.isnot(None))
    else:
        query = query.filter(Item.deleted_at.is_(None), Item.categoria_id.in_(seleccionadas))

    return query.all(), seleccionadas


def consume_item(item_id, usuario_id, destino, observacion):
    item = Item.query.get_or_404(item_id)
    item.deleted_at = db.func.now()
    movimiento = Movimiento(
        item_id=item.id,
        usuario_id=usuario_id,
        tipo='consumir',
        destino=destino,
        observacion=observacion,
    )
    db.session.add(movimiento)
    db.session.commit()
    return item
