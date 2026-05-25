from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from . import auth_bp
from .. import login_manager
from ..services.auth_service import authenticate_user, register_user, get_user_by_id


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(user_id)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = authenticate_user(username, password)
        if user:
            login_user(user)
            return redirect(url_for('main.index'))

        flash('Usuario o contraseña incorrectos', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/registrar-usuario', methods=['GET', 'POST'])
def registrar_usuario():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        error = register_user(username, email, password, password_confirm)
        if error:
            flash(error, 'danger')
            return redirect(url_for('auth.registrar_usuario'))

        flash('Usuario creado exitosamente. Por favor inicia sesión', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/registrar_usuario.html')
