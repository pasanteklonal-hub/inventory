from flask import render_template, request
from flask_login import login_required

from . import main_bp
from ..services.report_service import (
    build_reporte_semanal,
    export_reporte_semanal_xlsx,
    export_reporte_semanal_pdf,
    export_inventario_json,
    import_inventario_json,
    list_movimientos,
)


@main_bp.route('/reporte-semanal')
@login_required
def reporte_semanal():
    categorias, summary, items, selected = build_reporte_semanal(request)

    if request.args.get('export') == 'xlsx':
        return export_reporte_semanal_xlsx(summary, items)

    if request.args.get('export') == 'pdf':
        return export_reporte_semanal_pdf(summary, items)

    return render_template(
        'reports/reporte_semanal.html',
        categorias=categorias,
        summary=summary,
        items=items,
        selected=selected,
        total_stock=sum(row['stock'] for row in summary),
    )


@main_bp.route('/reportes')
@login_required
def reportes():
    movimientos = list_movimientos()
    return render_template('reports/reportes.html', movimientos=movimientos)


@main_bp.route('/exportar-json')
@login_required
def exportar_json():
    return export_inventario_json()


@main_bp.route('/importar-json', methods=['GET', 'POST'])
@login_required
def importar_json():
    response = import_inventario_json(request)
    if response is not None:
        return response
    return render_template('main/import_json.html')
