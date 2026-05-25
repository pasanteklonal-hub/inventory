from flask import Blueprint

main_bp = Blueprint("main", __name__)
auth_bp = Blueprint("auth", __name__)

# Import controllers so route handlers attach to the blueprints
from . import auth_controller  # noqa: F401, E402
from . import category_controller  # noqa: F401, E402
from . import item_controller  # noqa: F401, E402
from . import report_controller  # noqa: F401, E402
from . import api_controller  # noqa: F401, E402
from . import main_controller  # noqa: F401, E402


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
