from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from . import main_bp
from ..services.item_service import (
    list_categories,
    create_item,
    get_item_or_404,
    update_item,
    filter_items_by_categoria,
    list_items_for_consumption,
    consume_item,
    get_items_for_inventory,
)
from ..services.category_service import get_categoria_or_404


@main_bp.route('/agregar-item', methods=['GET', 'POST'])
@login_required
def agregar_item():
    categorias = list_categories()

    if request.method == 'POST':
        categoria_id = request.form.get('categoria_id')
        categoria = get_categoria_or_404(categoria_id)

        datos = {}
        for campo in categoria.campos:
            valor = request.form.get(f'campo_{campo.id}')
            if campo.requerido and not valor:
                flash(f"El campo '{campo.nombre}' es requerido", 'danger')
                return redirect(url_for('main.agregar_item'))
            datos[campo.nombre] = valor

        create_item(categoria_id, datos, current_user.id)
        flash('Item agregado al inventario', 'success')
        return redirect(url_for('main.agregar_item'))

    return render_template('items/agregar_item.html', categorias=categorias)


@main_bp.route('/editar-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def editar_item(item_id):
    item = get_item_or_404(item_id)
    categoria = item.categoria

    if request.method == 'POST':
        datos = {}
        for campo in categoria.campos:
            valor = request.form.get(f'campo_{campo.id}')
            if campo.requerido and not valor:
                flash(f"El campo '{campo.nombre}' es requerido", 'danger')
                return redirect(url_for('main.editar_item', item_id=item_id))
            datos[campo.nombre] = valor

        update_item(item, datos, current_user.id)
        flash('Item actualizado correctamente', 'success')
        return redirect(url_for('main.inventario_general'))

    return render_template('items/editar_item.html', item=item, categoria=categoria)


@main_bp.route('/items/<int:categoria_id>')
@login_required
def listar_items(categoria_id):
    categoria = get_categoria_or_404(categoria_id)
    filtros = {}
    for campo in categoria.campos:
        val = request.args.get(f'f_{campo.id}')
        if val:
            filtros[campo.nombre] = val

    items = filter_items_by_categoria(categoria_id, filtros)
    return render_template('items/listar_items.html', categoria=categoria, items=items, filtros=filtros)


@main_bp.route('/inventario-general')
@login_required
def inventario_general():
    categorias = list_categories()
    selected = request.args.getlist('categoria_id', type=int)
    mostrar_consumidos = request.args.get('mostrar_consumidos') == '1'

    items, seleccionadas = get_items_for_inventory(categorias, selected, mostrar_consumidos)

    return render_template(
        'items/inventario_general.html',
        categorias=categorias,
        items=items,
        seleccionadas=seleccionadas,
        mostrar_consumidos=mostrar_consumidos,
    )


@main_bp.route('/consumir-item', methods=['GET', 'POST'])
@login_required
def consumir_item():
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        destino = request.form.get('destino')
        observacion = request.form.get('observacion')
        consume_item(item_id, current_user.id, destino, observacion)
        flash('Item consumido / retirado del inventario', 'success')
        return redirect(url_for('main.consumir_item'))

    categorias, items_por_categoria = list_items_for_consumption()
    return render_template('items/consumir_item.html', categorias=categorias, items_por_categoria=items_por_categoria)
