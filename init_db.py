from app import create_app, db


app = create_app()


def init_db():
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully.")
        print("✓ Models: Usuario, Categoria, Campo, Item, Movimiento")
        print("")
        print("Próximos pasos:")
        print("  1. Crea un usuario: python")
        print("     from app import db")
        print("     from app.models import Usuario")
        print("     u = Usuario(username='admin', email='admin@example.com')")
        print("     u.set_password('password')")
        print("     db.session.add(u)")
        print("     db.session.commit()")
        print("  2. Inicia la aplicación y accede a /login")


if __name__ == '__main__':
    init_db()
