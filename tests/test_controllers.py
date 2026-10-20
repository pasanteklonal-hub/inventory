from app import db
from app.models import Usuario, Categoria, Campo, Item, Movimiento


def login(client, username='testuser', password='password'):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def test_registration_logs_in_new_user(client):
    response = client.post('/registrar-usuario', data={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123',
        'password_confirm': 'password123',
    }, follow_redirects=True)

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert 'Bienvenido, newuser' in page
    assert 'href="/reporte-semanal">Reporte Semanal</a>' in page
    assert 'href="/reportes">Reporte de Movimientos</a>' in page
    with client.session_transaction() as session:
        assert session.get('_user_id') is not None


def test_failed_registration_does_not_log_in(client):
    response = client.post('/registrar-usuario', data={
        'username': 'invaliduser',
        'email': 'invaliduser@example.com',
        'password': 'password123',
        'password_confirm': 'different123',
    }, follow_redirects=True)

    assert response.status_code == 200
    assert 'Crear Cuenta' in response.get_data(as_text=True)
    with client.session_transaction() as session:
        assert session.get('_user_id') is None


def test_create_product_uses_selected_category_fields(client, app):
    with app.app_context():
        setup_user('creatoruser')
        categoria = Categoria(nombre='Dispositivos')
        db.session.add(categoria)
        db.session.flush()
        campo = Campo(
            categoria_id=categoria.id,
            nombre='Capacidad',
            tipo='select',
            opciones='480 GB, 1 TB',
            requerido=True,
        )
        db.session.add(campo)
        db.session.commit()
        categoria_id = categoria.id
        campo_id = campo.id

    login(client, username='creatoruser')

    response = client.get('/agregar-producto')
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'Primero, selecciona una categoría' in page
    assert 'name="descripcion"' not in page

    response = client.get(f'/agregar-producto?categoria_id={categoria_id}')
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'name="descripcion"' in page
    assert f'name="campo_{campo_id}"' in page
    assert 'required' in page

    response = client.post('/agregar-producto', data={
        'categoria_id': str(categoria_id),
        'descripcion': 'Disco SSD Kingston',
        'modelo': 'SA400S37/480G',
        f'campo_{campo_id}': '',
    })
    assert response.status_code == 200
    assert 'Capacidad' in response.get_data(as_text=True)
    assert 'es requerido' in response.get_data(as_text=True)
    assert Item.query.filter_by(categoria_id=categoria_id).count() == 0

    response = client.post('/agregar-producto', data={
        'categoria_id': str(categoria_id),
        'descripcion': 'Disco SSD Kingston',
        'modelo': 'SA400S37/480G',
        f'campo_{campo_id}': '480 GB',
    }, follow_redirects=True)
    assert response.status_code == 200
    producto = Item.query.filter_by(categoria_id=categoria_id).one()
    assert producto.datos == {
        'Descripción': 'Disco SSD Kingston',
        'Modelo': 'SA400S37/480G',
        'Capacidad': '480 GB',
    }
    assert producto.stock == 0


def test_delete_product_requires_post_and_hides_product(client, app):
    with app.app_context():
        usuario = setup_user('deleteuser')
        categoria = Categoria(nombre='Eliminación')
        db.session.add(categoria)
        db.session.flush()
        producto = Item(
            categoria_id=categoria.id,
            datos={'Descripción': 'Producto de prueba para eliminar'},
            stock=2,
        )
        db.session.add(producto)
        db.session.flush()
        movimiento = Movimiento(
            item_id=producto.id,
            usuario_id=usuario.id,
            tipo='agregar',
            cantidad=2,
        )
        db.session.add(movimiento)
        db.session.commit()
        producto_id = producto.id
        categoria_id = categoria.id
        movimiento_id = movimiento.id

    login(client, username='deleteuser')

    response = client.get('/inventario-general')
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'Producto de prueba para eliminar' in page
    assert '>Eliminar</button>' not in page

    response = client.get(f'/editar-producto/{producto_id}')
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert 'Eliminar producto' in page
    assert '¿Desea confirmar eliminar el producto' in page
    assert 'Producto de prueba para eliminar' in page
    assert 'Cancelar' in page

    response = client.post(
        f'/eliminar-producto/{producto_id}',
        data={'categoria_id': str(categoria_id)},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert 'eliminado' in response.get_data(as_text=True)
    assert Item.query.filter_by(id=producto_id).one().eliminado is True
    assert Movimiento.query.filter_by(id=movimiento_id).count() == 1
    assert response.get_data(as_text=True).count('Producto de prueba para eliminar') == 1


def setup_user(username='testuser'):
    u = Usuario(username=username, email=f'{username}@example.com')
    u.set_password('password')
    db.session.add(u)
    db.session.commit()
    return u


def test_full_controller_flow(client, app):
    # create user and login
    with app.app_context():
        setup_user()

    rv = login(client)
    assert rv.status_code == 200

    dashboard = client.get('/')
    dashboard_text = dashboard.get_data(as_text=True)
    assert 'Crear Producto' in dashboard_text
    assert 'Agregar al Stock' in dashboard_text
    assert 'Agregar Item' not in dashboard_text
    assert 'Agregar Stock' not in dashboard_text

    # create a category
    rv = client.post('/registrar', data={'nombre': 'CatCtrl', 'descripcion': 'desc'}, follow_redirects=True)
    text = rv.get_data(as_text=True)
    assert 'Categor' in text or rv.status_code == 200

    # grab category id
    cat = Categoria.query.filter_by(nombre='CatCtrl').first()
    assert cat is not None

    # add campo via crear_campos
    rv = client.post(f'/categoria/{cat.id}/campos', data={'nombre': 'Campo1', 'tipo': 'text', 'requerido': ''}, follow_redirects=True)
    text = rv.get_data(as_text=True)
    assert "Campo" in text or rv.status_code == 200

    campo = Campo.query.filter_by(categoria_id=cat.id, nombre='Campo1').first()
    assert campo is not None

    rv = client.post('/agregar-producto', data={
        'categoria_id': str(cat.id),
        'descripcion': 'Disco SSD 480 Kingston',
        'modelo': 'SA400S37/480G',
    }, follow_redirects=True)
    assert rv.status_code == 200
    product = Item.query.filter_by(categoria_id=cat.id).first()
    assert product.datos == {
        'Descripción': 'Disco SSD 480 Kingston',
        'Modelo': 'SA400S37/480G',
        'Campo1': '',
    }
    assert product.stock == 0

    rv = client.post('/agregar-stock', data={
        'item_id': product.id,
        'cantidad': '3',
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert product.stock == 3
    rv = client.post(f'/editar-item/{product.id}', data={
        f'campo_{campo.id}': 'Kingston',
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert product.datos == {
        'Descripción': 'Disco SSD 480 Kingston',
        'Modelo': 'SA400S37/480G',
        'Campo1': 'Kingston',
    }
    rv = client.post(f'/editar-producto/{product.id}', data={
        'descripcion': 'Disco SSD 480 Kingston KC600',
        'modelo': 'SKC600/512G',
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert product.datos == {
        'Descripción': 'Disco SSD 480 Kingston KC600',
        'Modelo': 'SKC600/512G',
        'Campo1': 'Kingston',
    }
    assert product.stock == 3

    rv = client.post('/agregar-item', data={
        'item_id': product.id,
        'cantidad': '4',
    }, follow_redirects=True)
    assert rv.status_code == 200
    item = product
    assert item.stock == 7

    # editar item
    rv = client.post(f'/editar-item/{item.id}', data={f'campo_{campo.id}': 'Nuevo'}, follow_redirects=True)
    text = rv.get_data(as_text=True)
    assert 'Item actualizado' in text or rv.status_code == 200
    assert item.datos['Modelo'] == 'SKC600/512G'

    # listar items
    rv = client.get(f'/items/{cat.id}')
    assert rv.status_code == 200
    text = rv.get_data(as_text=True)
    assert 'Items' in text

    # inventario general
    rv = client.get('/inventario-general')
    assert rv.status_code == 200

    # consumir item
    rv = client.post('/consumir-item', data={'item_id': item.id, 'destino': 'X', 'observacion': 'test'}, follow_redirects=True)
    text = rv.get_data(as_text=True)
    assert 'Item consumido' in text or rv.status_code == 200
    assert item.stock == 6

    rv = client.post('/consumir-item', data={
        'item_id': product.id,
        'cantidad': '2',
        'destino': 'Taller',
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert product.stock == 4

    rv = client.post('/consumir-item', data={'item_id': '', 'destino': ''}, follow_redirects=True)
    assert rv.status_code == 200

    rv = client.post('/consumir-item', data={
        'item_id': product.id,
        'cantidad': '4',
        'destino': 'Taller',
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert product.stock == 0
    assert product.deleted_at is None

    movimientos_antes = Movimiento.query.filter_by(
        item_id=product.id,
        tipo='consumir',
    ).count()
    rv = client.post('/consumir-item', data={
        'item_id': product.id,
        'cantidad': '1',
        'destino': 'Taller',
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert 'No hay stock suficiente' in rv.get_data(as_text=True)
    assert product.stock == 0
    assert Movimiento.query.filter_by(item_id=product.id, tipo='consumir').count() == movimientos_antes

    rv = client.get('/inventario-general')
    assert rv.status_code == 200
    assert 'Disco SSD 480 Kingston KC600' in rv.get_data(as_text=True)

    rv = client.post('/agregar-stock', data={
        'categoria_id': cat.id,
        'item_id': item.id,
        'cantidad': '2',
        'observacion': 'Reposición',
    }, follow_redirects=True)
    assert rv.status_code == 200
    assert item.stock == 2
    assert item.deleted_at is None

    # exportar json
    rv = client.get('/exportar-json')
    assert rv.status_code == 200
    assert 'json' in rv.content_type

    # importar json: create a small file
    import io, json
    payload = {'ImportCat': [{
        'categoria': 'ImportCat',
        'Field': 'V',
        '__inventory_stock__': 7,
    }]}
    bio = io.BytesIO(json.dumps(payload).encode('utf-8'))
    bio.name = 'import.json'
    rv = client.post('/importar-json', data={'file': (bio, 'import.json')}, follow_redirects=True)
    assert rv.status_code == 200
    imported_category_id = Categoria.query.filter_by(nombre='ImportCat').first().id
    imported = db.session.execute(
        db.select(Item.stock, Item.datos).where(Item.categoria_id == imported_category_id)
    ).first()
    assert imported.stock == 7
    assert imported.datos == {'Field': 'V'}
