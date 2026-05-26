from app.dao.categoria_dao import get_active_categories
from app import db
from app.models import Categoria


def test_get_active_categories(app):
    # ensure clean
    Categoria.query.delete()
    db.session.commit()

    c1 = Categoria(nombre='C1')
    c2 = Categoria(nombre='C2')
    db.session.add_all([c1, c2])
    db.session.commit()

    out = get_active_categories()
    assert len(out) >= 2
