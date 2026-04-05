from optica_app.database import db

class Empleado(db.Model):
    __tablename__ = 'empleado'
    id = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.String(4))
    numero_documento = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    telefono = db.Column(db.String(10))
    direccion = db.Column(db.String(100))
    fecha_ingreso = db.Column(db.Date, nullable=False)
    cargo = db.Column(db.String(50))
    correo = db.Column(db.String(100))
    estado = db.Column(db.Boolean, default=True)
    citas = db.relationship('Cita', backref='empleado', lazy=True)
    horarios = db.relationship('Horario', backref='empleado', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'tipo_documento': self.tipo_documento,
            'numero_documento': self.numero_documento,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'correo': self.correo,
            'fecha_ingreso': self.fecha_ingreso.isoformat() if self.fecha_ingreso else None,
            'cargo': self.cargo,
            'estado': self.estado
        }

class Horario(db.Model):
    __tablename__ = 'horario'
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    dia = db.Column(db.Integer, nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_final = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'empleado_id': self.empleado_id,
            'dia': self.dia,
            'hora_inicio': self.hora_inicio.isoformat(),
            'hora_final': self.hora_final.isoformat(),
            'activo': self.activo
        }

class CampanaSalud(db.Model):
    __tablename__ = 'campana_salud'
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    empresa = db.Column(db.String(60), nullable=False)
    contacto = db.Column(db.String(15))
    fecha = db.Column(db.DateTime, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    direccion = db.Column(db.String(30))
    observaciones = db.Column(db.String(100))
    estado_cita_id = db.Column(db.Integer, db.ForeignKey('estado_cita.id'), nullable=False, default=1)
    empleado = db.relationship('Empleado', backref='campanas_salud', lazy=True)
    estado_cita = db.relationship('EstadoCita', backref='campanas_salud', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'empleado_id': self.empleado_id,
            'empleado_nombre': self.empleado.nombre if self.empleado else None,
            'empresa': self.empresa,
            'contacto': self.contacto,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'hora': self.hora.isoformat() if self.hora else None,
            'direccion': self.direccion,
            'observaciones': self.observaciones,
            'estado_cita_id': self.estado_cita_id,
            'estado_nombre': self.estado_cita.nombre if self.estado_cita else None
        }