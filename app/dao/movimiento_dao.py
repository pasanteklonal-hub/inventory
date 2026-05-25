from ..models import Movimiento


def list_movimientos():
    return Movimiento.query.order_by(Movimiento.created_at.desc()).all()


def save_movimiento(movimiento):
    from .. import db
    db.session.add(movimiento)
    db.session.commit()
    return movimiento
