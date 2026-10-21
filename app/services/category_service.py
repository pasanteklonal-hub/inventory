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


def delete_categoria(categoria):
    if not categoria:
        return 'Categoría no encontrada'
    if Item.query.filter_by(categoria_id=categoria.id).first():
        return 'No se puede eliminar la categoría porque tiene productos relacionados'

    db.session.delete(categoria)
    db.session.commit()
    return None


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


def update_campo_de_categoria(categoria, campo_id, nombre, tipo, requerido, opciones):
    if not categoria:
        return 'Categoría no encontrada'

    campo = Campo.query.filter_by(id=campo_id, categoria_id=categoria.id).first()
    if not campo:
        return 'Campo no encontrado'

    nombre = (nombre or '').strip()
    if not nombre:
        return 'El nombre del campo es requerido'

    tipos_permitidos = {'text', 'number', 'date', 'email', 'select', 'textarea'}
    if tipo not in tipos_permitidos:
        return 'El tipo de dato seleccionado no es válido'

    nombre_existente = Campo.query.filter(
        Campo.categoria_id == categoria.id,
        Campo.id != campo.id,
        db.func.lower(Campo.nombre) == nombre.lower(),
    ).first()
    if nombre_existente:
        return 'Ya existe un campo con ese nombre en la categoría'

    nombre_anterior = campo.nombre
    if nombre_anterior != nombre:
        items = Item.query.filter_by(categoria_id=categoria.id).all()
        if any(nombre in (item.datos or {}) and nombre_anterior in (item.datos or {}) for item in items):
            return 'No se puede cambiar el nombre porque algunos productos ya tienen un dato con ese nombre'

        for item in items:
            datos = dict(item.datos or {})
            if nombre_anterior in datos:
                datos[nombre] = datos.pop(nombre_anterior)
                item.datos = datos

    campo.nombre = nombre
    campo.tipo = tipo
    campo.requerido = requerido
    campo.opciones = opciones if tipo == 'select' else ''
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
