from app.database import db

class Marca(db.Model):
    __tablename__ = 'marca'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.Boolean, default=True)
    productos = db.relationship('Producto', backref='marca', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'estado': self.estado,
        }

class CategoriaProducto(db.Model):
    __tablename__ = 'categoria_producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(100))
    estado = db.Column(db.Boolean, default=True)
    productos = db.relationship('Producto', backref='categoria', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'estado': self.estado,
        }

class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    categoria_producto_id = db.Column(db.Integer, db.ForeignKey('categoria_producto.id'), nullable=False)
    marca_id = db.Column(db.Integer, db.ForeignKey('marca.id'), nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    precio_venta = db.Column(db.Float, nullable=False)
    precio_compra = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    descripcion = db.Column(db.String(120))
    estado = db.Column(db.Boolean, default=True)
    imagenes = db.relationship('Imagen', back_populates='producto', lazy=True, cascade='all, delete-orphan')

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
            'categoria_id': self.categoria_producto_id,
            'marca_id': self.marca_id,
            'imagenes': [img.to_dict() for img in self.imagenes] if self.imagenes else []
        }

class Imagen(db.Model):
    __tablename__ = 'imagen'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    producto = db.relationship('Producto', back_populates='imagenes')

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'producto_id': self.producto_id
        }