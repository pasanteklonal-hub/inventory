from .. import db
from ..models import Item, Movimiento, Categoria, Campo
from ..dao.categoria_dao import get_active_categories
from datetime import datetime


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

    # map field name -> Campo for type/options checks
    campos = {c.nombre: c for c in Campo.query.filter_by(categoria_id=categoria_id).all()}

    def try_parse_date(value):
        if not value:
            return None
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
            try:
                return datetime.strptime(value, fmt).date()
            except Exception:
                continue
        return None

    def matches(item):
        datos = item.datos or {}
        for field_name, filter_val in filtros.items():
            # skip empty filters
            if not filter_val:
                continue

            campo = campos.get(field_name)
            item_val = datos.get(field_name)

            if item_val is None:
                return False

            # If campo has fixed options, match exact (case-insensitive)
            if campo and campo.opciones:
                opts = [o.strip() for o in (campo.opciones or '').split(',') if o.strip()]
                if str(filter_val).strip().lower() not in [o.lower() for o in opts]:
                    # allow matching against the stored value as well
                    if str(item_val).strip().lower() != str(filter_val).strip().lower():
                        return False
                else:
                    if str(item_val).strip().lower() != str(filter_val).strip().lower():
                        return False
                continue

            # Date fields: try to parse both and compare date equality
            if campo and campo.tipo and campo.tipo.lower() == 'date':
                f_date = try_parse_date(filter_val)
                i_date = try_parse_date(str(item_val))
                if f_date is None or i_date is None or f_date != i_date:
                    return False
                continue

            # Default: substring case-insensitive match
            if str(filter_val).lower() not in str(item_val).lower():
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
