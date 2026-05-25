from flask import jsonify
from flask_login import login_required

from . import main_bp
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
