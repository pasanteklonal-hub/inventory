from app import create_app, db
from sqlalchemy import inspect, text


app = create_app()


def migrate_stock_columns():
    migrations = {
        'item': ('stock', 'INTEGER NOT NULL DEFAULT 1'),
        'movimiento': ('cantidad', 'INTEGER NOT NULL DEFAULT 1'),
    }
    inspector = inspect(db.engine)
    for table_name, (column_name, column_type) in migrations.items():
        columns = {column['name'] for column in inspector.get_columns(table_name)}
        if column_name not in columns:
            db.session.execute(text(
                f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'
            ))
            if table_name == 'item':
                db.session.execute(text(
                    'UPDATE item SET stock = 0 WHERE deleted_at IS NOT NULL'
                ))
    db.session.commit()


def init_db():
    with app.app_context():
        db.create_all()
        migrate_stock_columns()
        print("✓ Database tables created successfully.")
        print("✓ Models: Usuario, Categoria, Campo, Item, Movimiento (with stock quantities)")
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
