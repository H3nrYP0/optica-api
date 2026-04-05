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
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    metodo_pago = db.Column(db.String(30))
    hora = db.Column(db.Time, nullable=False)
    duracion = db.Column(db.Integer)
    fecha = db.Column(db.Date, nullable=False)
    estado_cita_id = db.Column(db.Integer, db.ForeignKey('estado_cita.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'servicio_id': self.servicio_id,
            'empleado_id': self.empleado_id,
            'metodo_pago': self.metodo_pago,
            'hora': self.hora.isoformat() if self.hora else None,
            'duracion': self.duracion,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'estado_cita_id': self.estado_cita_id,
            'estado_nombre': self.estado_cita.nombre if self.estado_cita else None,
            'cliente_nombre': f"{self.cliente.nombre} {self.cliente.apellido}" if self.cliente else None,
            'servicio_nombre': self.servicio.nombre if self.servicio else None,
            'empleado_nombre': self.empleado.nombre if self.empleado else None
        }
