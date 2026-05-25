from ..models import Campo


def get_campo_by_id(campo_id):
    return Campo.query.get(campo_id)


def delete_campo(campo):
    if not campo:
        return
    from .. import db
    db.session.delete(campo)
    db.session.commit()
