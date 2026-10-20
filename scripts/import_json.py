import argparse
import json
import sys
from app import create_app, db
from app.models import Categoria, Campo, Item, Movimiento
from app.services.item_service import validate_quantity


def import_from_file(path, dry_run=False):
    app = create_app()
    with app.app_context():
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error leyendo JSON: {e}")
            return 2

        if dry_run:
            print(f"Dry run: se parsearon {len(data)} categorías")
            return 0

        try:
            stock_by_category = {
                categoria_name: [
                    validate_quantity(item.get('__inventory_stock__', 1))
                    for item in items
                ]
                for categoria_name, items in data.items()
            }
        except (AttributeError, TypeError, ValueError) as error:
            print(f"Cantidad de stock incorrecta en JSON: {error}")
            return 2

        # Borrar datos existentes (movimientos -> items -> campos -> categorias)
        # Nota: esta importación está pensada para poblar la base eliminando datos de prueba.
        # No se crearán registros de movimiento para los items importados.
        print("Eliminando movimientos, items, campos y categorías existentes...")
        Movimiento.query.delete()
        Item.query.delete()
        Campo.query.delete()
        Categoria.query.delete()
        db.session.commit()

        for categoria_name, items in data.items():
            print(f"Creando categoría: {categoria_name}")
            categoria = Categoria(nombre=categoria_name, descripcion='Importada desde JSON')
            db.session.add(categoria)
            db.session.flush()  # para obtener id

            # Determinar campos únicos por categoría
            campos_nombres = []
            for it in items:
                for k in it.keys():
                    if k.strip().lower() == 'categoria' or k == '__inventory_stock__':
                        continue
                    if k not in campos_nombres:
                        campos_nombres.append(k)

            for idx, nombre in enumerate(campos_nombres):
                campo = Campo(categoria_id=categoria.id, nombre=nombre, tipo='text', requerido=False, orden=idx)
                db.session.add(campo)

            for it, stock in zip(items, stock_by_category[categoria_name]):
                item_data = {
                    k: v for k, v in it.items()
                    if k.strip().lower() != 'categoria' and k != '__inventory_stock__'
                }
                item = Item(categoria_id=categoria.id, datos=item_data, stock=stock)
                db.session.add(item)

        db.session.commit()
        print("Importación completada correctamente.")
        return 0


def main():
    parser = argparse.ArgumentParser(description='Importar JSON a la base de datos de la app')
    parser.add_argument('file', help='Ruta al archivo .json a importar')
    parser.add_argument('--dry-run', action='store_true', help='Solo parsear sin modificar la BD')
    args = parser.parse_args()

    sys.exit(import_from_file(args.file, dry_run=args.dry_run))


if __name__ == '__main__':
    main()
