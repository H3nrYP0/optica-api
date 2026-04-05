from app.database import db
from datetime import datetime

class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id = db.Column(db.Integer, primary_key=True)
    tipo_proveedor = db.Column(db.String(20))
    tipo_documento = db.Column(db.String(4))
    documento = db.Column(db.String(20))
    razon_social_o_nombre = db.Column(db.String(30), nullable=False)
    contacto = db.Column(db.String(20))
    telefono = db.Column(db.String(10))
    correo = db.Column(db.String(50))
    departamento = db.Column(db.String(15))
    municipio = db.Column(db.String(100))
    direccion = db.Column(db.String(30))
    estado = db.Column(db.Boolean, default=True)
    compras = db.relationship('Compra', backref='proveedor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'tipo_proveedor': self.tipo_proveedor,
            'tipo_documento': self.tipo_documento,
            'documento': self.documento,
            'razon_social_o_nombre': self.razon_social_o_nombre,
            'contacto': self.contacto,
            'telefono': self.telefono,
            'correo': self.correo,
            'departamento': self.departamento,
            'municipio': self.municipio,
            'direccion': self.direccion,
            'estado': self.estado
        }

class Compra(db.Model):
    __tablename__ = 'compra'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    estado_compra = db.Column(db.Boolean, default=True)
    detalles = db.relationship('DetalleCompra', backref='compra', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'proveedor_id': self.proveedor_id,
            'total': self.total,
            'fecha': self.fecha.isoformat(),
            'estado_compra': self.estado_compra
        }

class DetalleCompra(db.Model):
    __tablename__ = 'detalle_compra'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compra.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    precio_unidad = db.Column(db.Float, nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'compra_id': self.compra_id,
            'producto_id': self.producto_id,
            'precio_unidad': self.precio_unidad,
            'cantidad': self.cantidad,
            'subtotal': self.subtotal
        }