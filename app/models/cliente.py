from app.database import db

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.String(4))
    numero_documento = db.Column(db.String(20), nullable=True)
    nombre = db.Column(db.String(25), nullable=False)
    apellido = db.Column(db.String(20), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    genero = db.Column(db.String(10))
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(30))
    municipio = db.Column(db.String(15))
    direccion = db.Column(db.String(30))
    ocupacion = db.Column(db.String(20))
    telefono_emergencia = db.Column(db.String(20))
    estado = db.Column(db.Boolean, default=True)
    citas = db.relationship('Cita', backref='cliente', lazy=True)
    historiales = db.relationship('HistorialFormula', backref='cliente', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'tipo_documento': self.tipo_documento,
            'numero_documento': self.numero_documento,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'genero': self.genero,
            'telefono': self.telefono,
            'correo': self.correo,
            'municipio': self.municipio,
            'direccion': self.direccion,
            'ocupacion': self.ocupacion,
            'telefono_emergencia': self.telefono_emergencia,
            'estado': self.estado
        }

class HistorialFormula(db.Model):
    __tablename__ = 'historial_formula'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    descripcion = db.Column(db.String(100))
    od_esfera = db.Column(db.String(10))
    od_cilindro = db.Column(db.String(10))
    od_eje = db.Column(db.String(10))
    oi_esfera = db.Column(db.String(10))
    oi_cilindro = db.Column(db.String(10))
    oi_eje = db.Column(db.String(10))
    fecha = db.Column(db.DateTime, default=__import__('datetime').datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'descripcion': self.descripcion,
            'fecha': self.fecha.isoformat()
        }