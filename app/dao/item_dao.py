from ..models import Item


def get_item_by_id(item_id):
    return Item.query.filter_by(id=item_id, eliminado=False).first()


def get_items_by_categoria(categoria_id, active_only=True):
    query = Item.query.filter_by(categoria_id=categoria_id)
    if active_only:
        query = query.filter_by(deleted_at=None, eliminado=False)
    return query.all()


def get_items_for_inventory(seleccionadas, mostrar_consumidos):
    query = Item.query
    if mostrar_consumidos:
        query = query.filter(
            Item.categoria_id.in_(seleccionadas),
            Item.deleted_at.isnot(None),
            Item.eliminado.is_(False),
        )
    else:
        query = query.filter(
            Item.deleted_at.is_(None),
            Item.categoria_id.in_(seleccionadas),
            Item.eliminado.is_(False),
        )
    return query.all()


def get_active_items_by_categoria(categoria_id):
    return get_items_by_categoria(categoria_id, active_only=True)
