from optica_app.database import db


class EstadoCita(db.Model):
    __tablename__ = 'estado_cita'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    citas = db.relationship('Cita', backref='estado_cita', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre
        }


class Cita(db.Model):
    __tablename__ = 'cita'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    fecha_cita = db.Column(db.DateTime, nullable=False)
    motivo = db.Column(db.String(200))
    estado = db.Column(db.String(20), default='Pendiente') # Pendiente, Completada, Cancelada
    activo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'empleado_id': self.empleado_id,
            'fecha_cita': self.fecha_cita.isoformat(),
            'motivo': self.motivo,
            'estado': self.estado,
            'activo': self.activo,
            # Agregamos info extra para que el Front no tenga que buscar nombres
            'nombre_cliente': self.cliente.nombre if self.cliente else "N/A",
            'nombre_empleado': self.empleado.nombre if self.empleado else "N/A"
        }