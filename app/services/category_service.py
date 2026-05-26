from .. import db
from ..models import Categoria, Campo, Item
from ..dao.categoria_dao import get_active_categories, get_categoria_by_id, get_categoria_by_name


def list_active_categories():
    return get_active_categories()


def create_categoria(nombre, descripcion):
    if not nombre:
        return 'El nombre de la categoría es obligatorio', None

    if get_categoria_by_name(nombre):
        return 'La categoría ya existe', None

    categoria = Categoria(nombre=nombre, descripcion=descripcion)
    db.session.add(categoria)
    db.session.commit()
    return None, categoria


def get_categoria_or_404(categoria_id):
    return get_categoria_by_id(categoria_id)


def update_categoria(categoria, nombre, descripcion):
    if not categoria:
        return 'Categoría no encontrada'
    if not nombre:
        return 'El nombre es requerido'
    categoria.nombre = nombre
    categoria.descripcion = descripcion
    db.session.add(categoria)
    db.session.commit()
    return None


def add_campo_to_categoria(categoria, nombre, tipo, requerido, opciones):
    if not categoria:
        return 'Categoría no encontrada'
    if not nombre:
        return 'El nombre del campo es requerido'

    campo = Campo(
        categoria_id=categoria.id,
        nombre=nombre,
        tipo=tipo,
        requerido=requerido,
        opciones=opciones,
        orden=len(categoria.campos),
    )
    db.session.add(campo)
    db.session.commit()
    return None


def delete_campo_from_categoria(categoria, campo_id):
    if not categoria:
        return 'Categoría no encontrada'
    campo = Campo.query.get(campo_id)
    if not campo or campo.categoria_id != categoria.id:
        return 'Campo no encontrado'

    nombre_c = campo.nombre
    items = Item.query.filter_by(categoria_id=categoria.id).all()
    for item in items:
        if item.datos and nombre_c in item.datos:
            # make a copy so SQLAlchemy / the JSON column detects the change
            new_datos = dict(item.datos)
            new_datos.pop(nombre_c, None)
            item.datos = new_datos
            db.session.add(item)

    db.session.delete(campo)
    db.session.commit()
    return None
