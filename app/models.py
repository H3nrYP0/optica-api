from app.database import db
from datetime import datetime
import bcrypt

class Marca(db.Model):
    __tablename__ = 'marca'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(23), nullable=False, unique=True)
    descripcion = db.Column(db.String(100))
    estado = db.Column(db.Boolean, default=True)
    productos = db.relationship('Producto', backref='marca', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'total_productos': len(self.productos)
        }

class CategoriaProducto(db.Model):
    __tablename__ = 'categoria_producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(15), nullable=False, unique=True)
    descripcion = db.Column(db.String(100))
    estado = db.Column(db.Boolean, default=True)
    productos = db.relationship('Producto', backref='categoria', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'total_productos': len(self.productos)
        }

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    categoria_producto_id = db.Column(db.Integer, db.ForeignKey('categoria_producto.id'), nullable=False)
    marca_id = db.Column(db.Integer, db.ForeignKey('marca.id'), nullable=False)
    nombre = db.Column(db.String(20), nullable=False)
    precio_venta = db.Column(db.Float, nullable=False)
    precio_compra = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    descripcion = db.Column(db.String(120))
    estado = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    imagenes = db.relationship('Imagen', backref='producto', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'precio_venta': self.precio_venta,
            'precio_compra': self.precio_compra,
            'stock': self.stock,
            'stock_minimo': self.stock_minimo,
            'descripcion': self.descripcion,
            'estado': self.estado,
            'categoria': self.categoria.nombre,
            'marca': self.marca.nombre,
            'categoria_id': self.categoria_producto_id,
            'marca_id': self.marca_id,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'tiene_imagenes': len(self.imagenes) > 0,
            'alerta_stock': self.stock <= self.stock_minimo
        }

class Imagen(db.Model):
    __tablename__ = 'imagen'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    es_principal = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'url': self.url,
            'es_principal': self.es_principal,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }