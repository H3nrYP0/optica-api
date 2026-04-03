from app.database import db
from datetime import datetime

class EstadoVenta(db.Model):
    __tablename__ = 'estado_venta'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(23), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre
        }

class Venta(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False, unique=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    fecha_pedido = db.Column(db.DateTime)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(20))
    metodo_entrega = db.Column(db.String(20))
    direccion_entrega = db.Column(db.String(255))
    transferencia_comprobante = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='completada')
    cliente = db.relationship('Cliente', backref='ventas')
    pedido = db.relationship('Pedido', backref='venta', uselist=False)
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True, cascade='all, delete-orphan')
    abonos = db.relationship('Abono', backref='venta', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'pedido_id': self.pedido_id,
            'cliente_id': self.cliente_id,
            'cliente_nombre': self.cliente.nombre if self.cliente else None,
            'fecha_pedido': self.fecha_pedido.isoformat() if self.fecha_pedido else None,
            'fecha_venta': self.fecha_venta.isoformat() if self.fecha_venta else None,
            'total': self.total,
            'metodo_pago': self.metodo_pago,
            'metodo_entrega': self.metodo_entrega,
            'direccion_entrega': self.direccion_entrega,
            'transferencia_comprobante': self.transferencia_comprobante,
            'estado': self.estado,
            'detalles': [d.to_dict() for d in self.detalles] if self.detalles else [],
            'abonos': [a.to_dict() for a in self.abonos] if self.abonos else []
        }

class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, nullable=False)
    producto = db.relationship('Producto', backref='detalle_ventas')

    def to_dict(self):
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'producto_id': self.producto_id,
            'producto_nombre': self.producto.nombre if self.producto else None,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'descuento': self.descuento,
            'subtotal': self.subtotal
        }

class Abono(db.Model):
    __tablename__ = 'abono'
    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    monto_abonado = db.Column(db.Float, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'monto_abonado': self.monto_abonado,
            'fecha': self.fecha.isoformat() if self.fecha else None
        }