from optica_app.database import db
from datetime import datetime

class Pedido(db.Model):
    __tablename__ = 'pedido'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(50))
    metodo_entrega = db.Column(db.String(50))
    direccion_entrega = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='pendiente')
    transferencia_comprobante = db.Column(db.String(255))
    cliente = db.relationship('Cliente', backref='pedidos')
    items = db.relationship('DetallePedido', backref='pedido', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'total': self.total,
            'metodo_pago': self.metodo_pago,
            'metodo_entrega': self.metodo_entrega,
            'direccion_entrega': self.direccion_entrega,
            'estado': self.estado,
            'transferencia_comprobante': self.transferencia_comprobante,
            'cliente_nombre': self.cliente.nombre if self.cliente else None,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }

class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedido'
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    precio_unitario = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    producto = db.relationship('Producto', backref='detalle_pedidos')

    def to_dict(self):
        return {
            'id': self.id,
            'pedido_id': self.pedido_id,
            'producto_id': self.producto_id,
            'producto_nombre': self.producto.nombre if self.producto else None,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'subtotal': self.subtotal
        }