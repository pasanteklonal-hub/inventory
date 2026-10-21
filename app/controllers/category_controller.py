from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required

from . import main_bp
from ..services.category_service import (
    list_active_categories,
    create_categoria,
    get_categoria_or_404,
    delete_categoria,
    update_categoria,
    add_campo_to_categoria,
    update_campo_de_categoria,
    delete_campo_from_categoria,
)


@main_bp.route('/equipos')
@login_required
def equipos():
    categorias = list_active_categories()
    return render_template('categorias/equipos.html', categorias=categorias)


@main_bp.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')

        error, categoria = create_categoria(nombre, descripcion)
        if error:
            flash(error, 'danger')
            return redirect(url_for('main.registrar'))

        flash(f"Categoría '{nombre}' creada exitosamente", 'success')
        return redirect(url_for('main.crear_campos', categoria_id=categoria.id))

    return render_template('categorias/registrar_categoria.html')


@main_bp.route('/categoria/<int:categoria_id>/eliminar', methods=['POST'])
@login_required
def eliminar_categoria(categoria_id):
    categoria = get_categoria_or_404(categoria_id)
    nombre = categoria.nombre
    error = delete_categoria(categoria)
    if error:
        flash(error, 'danger')
    else:
        flash(f"Categoría '{nombre}' eliminada", 'success')
    return redirect(url_for('main.equipos'))


@main_bp.route('/categoria/<int:categoria_id>/campos', methods=['GET', 'POST'])
@login_required
def crear_campos(categoria_id):
    categoria = get_categoria_or_404(categoria_id)

    if request.method == 'POST':
        action = request.form.get('action', 'add')

        if action == 'edit_categoria':
            nombre = request.form.get('nombre_categoria')
            descripcion = request.form.get('descripcion_categoria')
            error = update_categoria(categoria, nombre, descripcion)
            if error:
                flash(error, 'danger')
            else:
                flash('Categoría actualizada', 'success')
            return redirect(url_for('main.crear_campos', categoria_id=categoria_id))

        if action == 'edit_campo':
            campo_id = request.form.get('campo_id', type=int)
            nombre_campo = request.form.get('nombre_campo')
            tipo_campo = request.form.get('tipo_campo')
            requerido = request.form.get('requerido') == 'on'
            opciones = request.form.get('opciones', '')
            error = update_campo_de_categoria(
                categoria,
                campo_id,
                nombre_campo,
                tipo_campo,
                requerido,
                opciones,
            )
            if error:
                flash(error, 'danger')
            else:
                flash(f"Campo '{nombre_campo}' actualizado", 'success')
            return redirect(url_for('main.crear_campos', categoria_id=categoria_id))

        if action == 'delete_campo':
            campo_id = request.form.get('campo_id')
            error = delete_campo_from_categoria(categoria, campo_id)
            if error:
                flash(error, 'danger')
            else:
                flash(f"Campo eliminado y datos limpios", 'success')
            return redirect(url_for('main.crear_campos', categoria_id=categoria_id))

        nombre_campo = request.form.get('nombre')
        tipo_campo = request.form.get('tipo')
        requerido = request.form.get('requerido') == 'on'
        opciones = request.form.get('opciones', '')

        error = add_campo_to_categoria(categoria, nombre_campo, tipo_campo, requerido, opciones)
        if error:
            flash(error, 'danger')
        else:
            flash(f"Campo '{nombre_campo}' añadido", 'success')
        return redirect(url_for('main.crear_campos', categoria_id=categoria_id))

    campos = categoria.campos
    return render_template('categorias/crear_campos.html', categoria=categoria, campos=campos)
