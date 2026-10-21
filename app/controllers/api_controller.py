from flask import abort, jsonify, request
from flask_login import login_required

from . import main_bp
from ..models import Campo
from ..services.category_service import get_categoria_or_404


@main_bp.route('/api/campos/<int:categoria_id>')
@login_required
def api_campos(categoria_id):
    categoria = get_categoria_or_404(categoria_id)
    campos = [
        {
            'id': c.id,
            'nombre': c.nombre,
            'tipo': c.tipo,
            'requerido': c.requerido,
            'opciones': c.opciones.split(',') if c.opciones else [],
        }
        for c in categoria.campos
    ]
    return jsonify(campos)


@main_bp.route('/api/categorias/<int:categoria_id>/campos/<int:campo_id>/opciones')
@login_required
def api_campo_opciones(categoria_id, campo_id):
    categoria = get_categoria_or_404(categoria_id)
    campo = Campo.query.filter_by(id=campo_id, categoria_id=categoria.id).first_or_404()
    if campo.tipo != 'select':
        abort(404)

    query = request.args.get('q', '').strip().casefold()
    if len(query) < 2:
        return jsonify({'opciones': [], 'hay_mas': False})

    limite = 50
    coincidencias = (
        opcion.strip()
        for opcion in (campo.opciones or '').split(',')
        if query in opcion.strip().casefold()
    )
    opciones = []
    for opcion in coincidencias:
        opciones.append(opcion)
        if len(opciones) > limite:
            break

    return jsonify({
        'opciones': opciones[:limite],
        'hay_mas': len(opciones) > limite,
    })
