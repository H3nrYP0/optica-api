from optica_app.database import db

class Rol(db.Model):
    __tablename__ = 'rol'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(100))
    estado = db.Column(db.Boolean, default=True)
    usuarios = db.relationship('Usuario', backref='rol', lazy=True)
    permisos = db.relationship(
        'Permiso',
        secondary='permiso_por_rol',
        lazy=True
    )

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'permisos': [p.to_dict() for p in self.permisos],
            'estado': self.estado
        }

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id'), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    correo = db.Column(db.String(100), nullable=False)
    contrasenia = db.Column(db.String(255), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    cliente = db.relationship('Cliente', backref='usuario', lazy=True)
    estado = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'rol_id': self.rol_id,
            'nombre': self.nombre,
            'correo': self.correo,
            'contrasenia': self.contrasenia,
            'cliente_id': self.cliente_id,
            'estado': self.estado
        }

class Permiso(db.Model):
    __tablename__ = 'permiso'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre
        }

class PermisoPorRol(db.Model):
    __tablename__ = 'permiso_por_rol'
    id = db.Column(db.Integer, primary_key=True)
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id'), nullable=False)
    permiso_id = db.Column(db.Integer, db.ForeignKey('permiso.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'rol_id': self.rol_id,
            'permiso_id': self.permiso_id
        }