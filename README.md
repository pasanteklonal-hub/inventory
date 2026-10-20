# Proyecto Flask inicial

Estructura mínima creada para ejecutar una aplicación Flask:

- `app/` - paquete con la aplicación y rutas
- `run.py` - punto de entrada
- `requirements.txt` - dependencias

Instrucciones rápidas:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py
```

La ruta principal está en `/` y devuelve un mensaje de comprobación.

Conexión a Postgres
--------------------

La app usa `SQLALCHEMY_DATABASE_URI` tomado de la variable de entorno `DATABASE_URL`.
Ejemplo de URL para Postgres:

```
export DATABASE_URL=postgresql://user:password@localhost:5432/mydb
```

Crear tablas:

```bash
source venv/bin/activate
python init_db.py
```

Al iniciar, `init_db.py` también incorpora las columnas de stock y eliminación lógica a bases de datos
existentes: los productos activos parten con stock 1 y los ya consumidos con stock 0.

Desde **Crear Producto** se registra la descripción, el modelo/referencia y la categoría del producto;
queda disponible con stock cero para agregarle unidades desde **Agregar al Stock**.
El nombre del producto se puede modificar con **Editar producto** desde el inventario
o el listado de su categoría; esta edición conserva su categoría, stock y otros detalles.
La opción **Eliminar** solicita confirmación antes de ocultar el producto del inventario;
sus movimientos históricos se conservan.
**Agregar al Stock** incrementa el stock de un producto existente; **Consumir Item**
registra la cantidad retirada, sin permitir que el stock quede negativo. Al agotarse,
el producto sigue visible en el inventario con stock cero. Las exportaciones JSON incluyen la cantidad
en el metadato `__inventory_stock__`, que se restaura al importar; los archivos
anteriores siguen importándose con una unidad por producto.

Si no se define `DATABASE_URL`, la app usará `sqlite:///dev.db` por defecto.

Docker
------

Arrancar la app y una base Postgres con Docker Compose:

```bash
cd flask_app
docker compose up --build
```

La app quedará disponible en http://localhost:5000 y la variable `DATABASE_URL` dentro
del contenedor `web` ya está apuntando a `postgresql://user:password@db:5432/mydb`.

Nota: el contenedor `web` ejecuta automáticamente `init_db.py` y `create_admin.py` durante
el arranque (espera a que Postgres esté listo). Esto crea las tablas y un usuario `admin`
por defecto (`admin@example.com` / `password123`).

Para crear las tablas desde el contenedor (una vez levantado):

```bash
docker compose exec web python init_db.py
```

Importar datos desde JSON
-------------------------

La aplicación incluye una herramienta para poblar la base de datos desde un archivo JSON.

- CLI: `scripts/import_json.py` — borra las categorías/items/campos/movimientos existentes y crea los nuevos.
	- Dry-run:

```bash
python scripts/import_json.py datos.json --dry-run
```

	- Ejecutar import real:

```bash
python scripts/import_json.py datos.json
```

- UI: iniciar sesión, abrir el menú de usuario -> `Importar JSON` y subir el archivo.

Notas importantes:
- La importación reemplaza datos existentes (incluye eliminación de históricos), está pensada
	para poblar entornos de prueba o inicializar datos.
- No se crearán registros de `Movimiento` al importar — la importación solo crea `Categoria`,
	`Campo` e `Item`.

Si prefieres usar Docker sólo para la base de datos y mantener tu entorno local, exporta
`DATABASE_URL` apuntando al host o configura credenciales compatibles.
# mi-inventario
