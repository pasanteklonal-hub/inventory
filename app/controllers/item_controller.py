from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from . import main_bp
from ..models import Item
from ..services.item_service import (
    list_categories,
    create_product,
    get_item_or_404,
    delete_product,
    update_item,
    filter_items_by_categoria,
    list_items_for_consumption,
    consume_item,
    add_stock,
    get_items_for_inventory,
)
from ..services.category_service import get_categoria_or_404


@main_bp.route('/agregar-producto', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    categorias = list_categories()

    if request.method == 'POST':
        categoria_id = request.form.get('categoria_id', type=int)
        categoria = next((cat for cat in categorias if cat.id == categoria_id), None)
        if not categoria:
            flash('Selecciona una categoría válida', 'danger')
            return render_template('items/agregar_producto.html', categorias=categorias)
        campos = sorted(categoria.campos, key=lambda campo: (campo.orden or 0, campo.id))
        try:
            producto = create_product(
                categoria.id,
                request.form.get('descripcion', ''),
                request.form.get('modelo', ''),
                current_user.id,
                {
                    str(campo.id): request.form.get(f'campo_{campo.id}', '')
                    for campo in campos
                },
            )
        except ValueError as error:
            flash(str(error), 'danger')
            return render_template(
                'items/agregar_producto.html',
                categorias=categorias,
                categoria_seleccionada=categoria,
                campos=campos,
            )
        flash('Producto creado. Ahora puedes agregarle stock.', 'success')
        return redirect(url_for('main.agregar_item', producto_id=producto.id))

    categoria_id = request.args.get('categoria_id', type=int)
    categoria = next((cat for cat in categorias if cat.id == categoria_id), None)
    campos = sorted(categoria.campos, key=lambda campo: (campo.orden or 0, campo.id)) if categoria else []
    return render_template(
        'items/agregar_producto.html',
        categorias=categorias,
        categoria_seleccionada=categoria,
        campos=campos,
    )


@main_bp.route('/editar-item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def editar_item(item_id):
    item = get_item_or_404(item_id)
    categoria = item.categoria

    if request.method == 'POST':
        campos_editables = {campo.nombre for campo in categoria.campos}
        datos = {
            clave: valor
            for clave, valor in (item.datos or {}).items()
            if clave not in campos_editables
        }
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


@main_bp.route('/editar-producto/<int:item_id>', methods=['GET', 'POST'])
@login_required
def editar_producto(item_id):
    item = get_item_or_404(item_id)

    if request.method == 'POST':
        descripcion = request.form.get('descripcion', '').strip()
        if not descripcion:
            flash('La descripción del producto es obligatoria', 'danger')
            return redirect(url_for('main.editar_producto', item_id=item.id))

        datos = dict(item.datos or {})
        datos['Descripción'] = descripcion
        datos['Modelo'] = request.form.get('modelo', '').strip()
        update_item(item, datos, current_user.id)
        flash('Producto actualizado correctamente', 'success')
        return redirect(url_for('main.inventario_general'))

    return render_template('items/editar_producto.html', item=item)


@main_bp.route('/eliminar-producto/<int:item_id>', methods=['POST'])
@login_required
def eliminar_producto(item_id):
    item = delete_product(item_id, current_user.id)
    categoria_id = request.form.get('categoria_id', type=int)
    flash(f"Producto '{(item.datos or {}).get('Descripción', f'#{item.id}')}' eliminado.", 'success')
    if categoria_id == item.categoria_id:
        return redirect(url_for('main.listar_items', categoria_id=categoria_id))
    return redirect(url_for('main.inventario_general'))


@main_bp.route('/items/<int:categoria_id>')
@login_required
def listar_items(categoria_id):
    categoria = get_categoria_or_404(categoria_id)
    filtros = {}
    for campo in categoria.campos:
        # for campos con opciones allow multiple selections
        if campo.opciones:
            vals = request.args.getlist(f'f_{campo.id}')
            # normalize empty list
            if vals:
                filtros[campo.nombre] = [v for v in vals if v != '']
        else:
            val = request.args.get(f'f_{campo.id}')
            if val:
                filtros[campo.nombre] = val

    items = filter_items_by_categoria(categoria_id, filtros)
    # prepare options for each campo: prefer Campo.opciones, otherwise derive from items
    campo_options = {}
    for campo in categoria.campos:
        if campo.opciones:
            opts = [o.strip() for o in (campo.opciones or '').split(',') if o.strip()]
        else:
            vals = set()
            for it in items:
                if it.datos and campo.nombre in it.datos and it.datos.get(campo.nombre) is not None:
                    vals.add(str(it.datos.get(campo.nombre)).strip())
            opts = sorted(v for v in vals if v != '')
        campo_options[campo.id] = opts

    return render_template('items/listar_items.html', categoria=categoria, items=items, filtros=filtros, campo_options=campo_options)


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
        if not item_id or not destino or not destino.strip():
            flash('Selecciona un producto e indica el destino', 'danger')
            return redirect(url_for('main.consumir_item'))
        try:
            cantidad = int(request.form.get('cantidad', '1'))
        except (TypeError, ValueError):
            flash('La cantidad debe ser un número entero mayor que cero', 'danger')
            return redirect(url_for('main.consumir_item'))
        try:
            consume_item(item_id, current_user.id, destino, observacion, cantidad)
        except ValueError as error:
            flash(str(error), 'danger')
            return redirect(url_for('main.consumir_item'))
        flash('Item consumido / retirado del inventario', 'success')
        return redirect(url_for('main.consumir_item'))

    categorias, items_por_categoria = list_items_for_consumption()
    return render_template('items/consumir_item.html', categorias=categorias, items_por_categoria=items_por_categoria)


@main_bp.route('/agregar-item', methods=['GET', 'POST'], endpoint='agregar_item')
@main_bp.route('/agregar-stock', methods=['GET', 'POST'], endpoint='agregar_stock')
@login_required
def agregar_stock():
    if request.method == 'POST':
        item_id = request.form.get('item_id', type=int)
        if not item_id:
            flash('Selecciona un producto', 'danger')
            return redirect(url_for(request.endpoint))
        try:
            cantidad = int(request.form.get('cantidad', ''))
        except (TypeError, ValueError):
            flash('La cantidad debe ser un número entero mayor que cero', 'danger')
            return redirect(url_for(request.endpoint))
        try:
            add_stock(
                item_id,
                current_user.id,
                cantidad,
                request.form.get('observacion'),
            )
        except ValueError as error:
            flash(str(error), 'danger')
            return redirect(url_for(request.endpoint))
        flash('Stock del producto actualizado correctamente', 'success')
        return redirect(url_for(request.endpoint))

    categorias = list_categories()
    items_por_categoria = {
        categoria.id: Item.query.filter_by(categoria_id=categoria.id, eliminado=False).all()
        for categoria in categorias
    }
    producto_id = request.args.get('producto_id', type=int)
    producto = Item.query.filter_by(id=producto_id, eliminado=False).first() if producto_id else None
    return render_template(
        'items/agregar_stock.html',
        categorias=categorias,
        items_por_categoria=items_por_categoria,
        producto_id=producto.id if producto else None,
        producto_categoria_id=producto.categoria_id if producto else None,
    )
