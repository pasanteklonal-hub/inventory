from datetime import datetime
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Usuario {self.username}>"


class Categoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    descripcion = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    campos = db.relationship('Campo', backref='categoria', lazy=True, cascade='all, delete-orphan')
    items = db.relationship('Item', backref='categoria', lazy=True)

    @property
    def active_items_count(self):
        return Item.query.filter_by(categoria_id=self.id, deleted_at=None, eliminado=False).count()

    def __repr__(self):
        return f"<Categoria {self.nombre}>"


class Campo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # text, number, date, select, etc
    requerido = db.Column(db.Boolean, default=False)
    orden = db.Column(db.Integer, default=0)
    opciones = db.Column(db.Text, nullable=True)  # JSON con opciones para select
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Campo {self.nombre}>"


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    datos = db.Column(db.JSON, nullable=True)  # Almacena los datos dinámicos
    stock = db.Column(db.Integer, nullable=False, default=0)
    eliminado = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    movimientos = db.relationship('Movimiento', backref='item', lazy=True)

    @property
    def serial(self):
        if not self.datos:
            return ''
        for key, value in self.datos.items():
            normalized = key.strip().lower()
            if normalized in ['serial', 'serie', 'número de serie', 'numero de serie', 'no. serie', 'no serie']:
                return value or ''
        return ''

    @property
    def estado(self):
        if self.eliminado:
            return 'Eliminado'
        if self.stock == 0:
            return 'Sin stock'
        if self.deleted_at:
            return 'Consumido'
        return 'Activo'

    def __repr__(self):
        return f"<Item {self.id}>"


class Movimiento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # agregar, consumir
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    destino = db.Column(db.String(200), nullable=True)
    observacion = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    usuario = db.relationship('Usuario', backref='movimientos')

    def __repr__(self):
        return f"<Movimiento {self.tipo}>"


# Para compatibilidad hacia atrás con modelos anteriores
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipo = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    estado = db.Column(db.String(50), nullable=False, default='activo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Equipo {self.equipo}>"
