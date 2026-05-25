from flask import render_template
from flask_login import current_user

from . import main_bp


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return render_template("main/dashboard.html")
    return render_template("main/index.html")
