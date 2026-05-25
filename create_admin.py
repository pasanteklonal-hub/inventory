#!/usr/bin/env python
"""Script para crear un usuario administrador de prueba"""
from app import create_app, db
from app.models import Usuario

app = create_app()

with app.app_context():
    # Verificar si ya existe
    if Usuario.query.filter_by(username='admin').first():
        print("✓ Usuario 'admin' ya existe.")
    else:
        # Crear usuario
        u = Usuario(username='admin', email='admin@example.com')
        u.set_password('password123')
        db.session.add(u)
        db.session.commit()
        print("✓ Usuario 'admin' creado exitosamente")
        print("  Email: admin@example.com")
        print("  Contraseña: password123")

    # Crear categorías por defecto
    from app.models import Categoria
    categorias_default = [
        {'nombre': 'Impresoras', 'descripcion': 'Impresoras y escáneres'},
        {'nombre': 'Monitores', 'descripcion': 'Monitores y pantallas'},
        {'nombre': 'Almacenamiento', 'descripcion': 'Discos, SSDs, memorias'},
        {'nombre': 'Cámaras', 'descripcion': 'Cámaras digitales y accesorios'},
        {'nombre': 'Periféricos', 'descripcion': 'Teclados, ratones, etc'},
        {'nombre': 'Red', 'descripcion': 'Routers, switches, cables'},
        {'nombre': 'Zebra Insumos', 'descripcion': 'Insumos para impresoras Zebra'},
    ]

    for cat_data in categorias_default:
        if not Categoria.query.filter_by(nombre=cat_data['nombre']).first():
            cat = Categoria(**cat_data)
            db.session.add(cat)
            print(f"✓ Categoría '{cat_data['nombre']}' creada")

    db.session.commit()
    print("\n✓ Base de datos preparada correctamente")
