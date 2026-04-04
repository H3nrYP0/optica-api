from app.database import db


class Servicio(db.Model):
    __tablename__ = 'servicio'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(65), nullable=False)
    duracion_min = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(200))
    estado = db.Column(db.Boolean, default=True)
    citas = db.relationship('Cita', backref='servicio', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'duracion_min': self.duracion_min,
            'precio': self.precio,
            'descripcion': self.descripcion,
            'estado': self.estado
        }
