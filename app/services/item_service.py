from .. import db
from ..models import Item, Movimiento, Categoria, Campo
from ..dao.categoria_dao import get_active_categories
from ..dao.item_dao import sort_items_alphabetically
from sqlalchemy import or_
from datetime import datetime


def list_categories():
    return get_active_categories()


def validate_quantity(cantidad):
    if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad < 1:
        raise ValueError('La cantidad debe ser un número entero mayor que cero')
    return cantidad


def create_item(categoria_id, datos, usuario_id, cantidad=1):
    validate_quantity(cantidad)
    item = Item(categoria_id=categoria_id, datos=datos, stock=cantidad)
    db.session.add(item)
    db.session.flush()
    movimiento = Movimiento(
        item_id=item.id,
        usuario_id=usuario_id,
        tipo='agregar',
        cantidad=cantidad,
        observacion='Item agregado al inventario',
    )
    db.session.add(movimiento)
    db.session.commit()
    return item


def create_product(categoria_id, descripcion, modelo, usuario_id, campos_datos=None):
    descripcion = (descripcion or '').strip()
    if not descripcion:
        raise ValueError('La descripción del producto es obligatoria')

    modelo = (modelo or '').strip()
    categoria = Categoria.query.filter_by(id=categoria_id, deleted_at=None).first()
    if not categoria:
        raise ValueError('La categoría seleccionada no es válida')

    datos = {'Descripción': descripcion, 'Modelo': modelo}
    campos_datos = campos_datos or {}
    campos = Campo.query.filter_by(categoria_id=categoria.id).order_by(Campo.orden, Campo.id).all()
    for campo in campos:
        valor = (campos_datos.get(str(campo.id)) or '').strip()
        if campo.requerido and not valor:
            raise ValueError(f"El campo '{campo.nombre}' es requerido")
        if valor and campo.tipo == 'select' and campo.opciones:
            opciones = [opcion.strip() for opcion in campo.opciones.split(',') if opcion.strip()]
            if valor not in opciones:
                raise ValueError(f"Selecciona una opción válida para el campo '{campo.nombre}'")
        datos[campo.nombre] = valor

    item = Item(
        categoria_id=categoria.id,
        datos=datos,
        stock=0,
    )
    db.session.add(item)
    db.session.flush()
    db.session.add(Movimiento(
        item_id=item.id,
        usuario_id=usuario_id,
        tipo='crear_producto',
        cantidad=0,
        observacion='Producto creado, pendiente de agregar stock',
    ))
    db.session.commit()
    return item


def get_item_or_404(item_id):
    return Item.query.filter_by(id=item_id, eliminado=False).first_or_404()


def delete_product(item_id, usuario_id):
    item = get_item_or_404(item_id)
    item.eliminado = True
    db.session.add(Movimiento(
        item_id=item.id,
        usuario_id=usuario_id,
        tipo='eliminar_producto',
        cantidad=0,
        observacion='Producto eliminado del inventario',
    ))
    db.session.commit()
    return item


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
    items_q = Item.query.filter(
        Item.categoria_id == categoria_id,
        Item.eliminado.is_(False),
        or_(Item.deleted_at.is_(None), Item.stock == 0),
    ).all()
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
                # filter_val may be a list (multiple selections) or a single value
                selected = filter_val if isinstance(filter_val, (list, tuple, set)) else [filter_val]
                selected_norm = [str(s).strip().lower() for s in selected if s is not None and s != '']
                item_norm = str(item_val).strip().lower()
                # match if any selected equals the item value
                if not any(item_norm == s for s in selected_norm):
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
            if isinstance(filter_val, (list, tuple, set)):
                # accept if any of the provided filters matches as substring
                if not any(str(f).lower() in str(item_val).lower() for f in filter_val):
                    return False
            else:
                if str(filter_val).lower() not in str(item_val).lower():
                    return False

        return True

    return sort_items_alphabetically(item for item in items_q if matches(item))


def list_items_for_consumption():
    categorias = list_categories()
    items_por_categoria = {
        cat.id: sort_items_alphabetically(
            Item.query.filter_by(categoria_id=cat.id, deleted_at=None, eliminado=False)
            .filter(Item.stock > 0).all()
        )
        for cat in categorias
    }
    return categorias, items_por_categoria


def get_items_for_inventory(categorias, selected, mostrar_consumidos):
    if not selected:
        return [], []

    seleccionadas = selected
    query = Item.query
    if mostrar_consumidos:
        query = query.filter(
            Item.categoria_id.in_(seleccionadas),
            Item.eliminado.is_(False),
            Item.deleted_at.isnot(None),
            Item.stock > 0,
        )
    else:
        query = query.filter(
            Item.categoria_id.in_(seleccionadas),
            Item.eliminado.is_(False),
            or_(Item.deleted_at.is_(None), Item.stock == 0),
        )

    return sort_items_alphabetically(query.all()), seleccionadas


def add_stock(item_id, usuario_id, cantidad, observacion=None):
    validate_quantity(cantidad)
    item = get_item_or_404(item_id)
    item.stock = Item.stock + cantidad
    item.deleted_at = None
    db.session.add(Movimiento(
        item_id=item.id,
        usuario_id=usuario_id,
        tipo='agregar',
        cantidad=cantidad,
        observacion=observacion or 'Stock agregado',
    ))
    db.session.commit()
    return item


def consume_item(item_id, usuario_id, destino, observacion, cantidad=1):
    validate_quantity(cantidad)
    item = get_item_or_404(item_id)
    updated = Item.query.filter(
        Item.id == item.id,
        Item.deleted_at.is_(None),
        Item.stock >= cantidad,
    ).update(
        {Item.stock: Item.stock - cantidad},
        synchronize_session=False,
    )
    if not updated:
        raise ValueError('No hay stock suficiente para consumir esa cantidad')
    db.session.refresh(item)
    movimiento = Movimiento(
        item_id=item.id,
        usuario_id=usuario_id,
        tipo='consumir',
        cantidad=cantidad,
        destino=destino,
        observacion=observacion,
    )
    db.session.add(movimiento)
    db.session.commit()
    return item
