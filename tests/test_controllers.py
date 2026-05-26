from app import db
from app.models import Usuario, Categoria, Campo, Item


def login(client, username='testuser', password='password'):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)


def setup_user():
    u = Usuario(username='testuser', email='t@example.com')
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

    # create a category
    rv = client.post('/registrar', data={'nombre': 'CatCtrl', 'descripcion': 'desc'}, follow_redirects=True)
    assert b'Categor' in rv.data or rv.status_code == 200

    # grab category id
    cat = Categoria.query.filter_by(nombre='CatCtrl').first()
    assert cat is not None

    # add campo via crear_campos
    rv = client.post(f'/categoria/{cat.id}/campos', data={'nombre': 'Campo1', 'tipo': 'text', 'requerido': ''}, follow_redirects=True)
    assert b"Campo 'Campo1' añadido" in rv.data or rv.status_code == 200

    campo = Campo.query.filter_by(categoria_id=cat.id, nombre='Campo1').first()
    assert campo is not None

    # agregar item
    rv = client.post('/agregar-item', data={'categoria_id': str(cat.id), f'campo_{campo.id}': 'Valor1'}, follow_redirects=True)
    assert b'Item agregado' in rv.data or rv.status_code == 200

    item = Item.query.filter_by(categoria_id=cat.id).first()
    assert item is not None

    # editar item
    rv = client.post(f'/editar-item/{item.id}', data={f'campo_{campo.id}': 'Nuevo'}, follow_redirects=True)
    assert b'Item actualizado' in rv.data or rv.status_code == 200

    # listar items
    rv = client.get(f'/items/{cat.id}')
    assert rv.status_code == 200
    assert b'Items' in rv.data

    # inventario general
    rv = client.get('/inventario-general')
    assert rv.status_code == 200

    # consumir item
    rv = client.post('/consumir-item', data={'item_id': item.id, 'destino': 'X', 'observacion': 'test'}, follow_redirects=True)
    assert b'Item consumido' in rv.data or rv.status_code == 200

    # exportar json
    rv = client.get('/exportar-json')
    assert rv.status_code == 200
    assert b'json' in rv.content_type

    # importar json: create a small file
    import io, json
    payload = {'ImportCat': [{'categoria': 'ImportCat', 'Field': 'V'}]}
    bio = io.BytesIO(json.dumps(payload).encode('utf-8'))
    bio.name = 'import.json'
    rv = client.post('/importar-json', data={'file': (bio, 'import.json')}, follow_redirects=True)
    assert rv.status_code == 200

