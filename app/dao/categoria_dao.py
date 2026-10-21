from sqlalchemy import func

from ..models import Categoria


def get_active_categories():
    return Categoria.query.filter_by(deleted_at=None).order_by(
        func.lower(Categoria.nombre),
        Categoria.id,
    ).all()


def get_categoria_by_id(categoria_id):
    return Categoria.query.get_or_404(categoria_id)


def get_categoria_by_name(nombre):
    if not nombre:
        return None
    return Categoria.query.filter_by(nombre=nombre, deleted_at=None).first()
