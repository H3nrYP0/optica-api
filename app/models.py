from app.database import db
from datetime import datetime

# ===== TABLAS DE ROLES Y USUARIOS =====
class Rol(db.Model):
    __tablename__ = 'rol'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(25), nullable=False)
    descripcion = db.Column(db.String(60))
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
    nombre = db.Column(db.String(25), nullable=False)
    correo = db.Column(db.String(27), nullable=False)
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
    nombre = db.Column(db.String(23), nullable=False)

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

# ===== TABLAS DE PRODUCTOS =====
class Marca(db.Model):
    __tablename__ = 'marca'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(23), nullable=False)
    estado = db.Column(db.Boolean, default=True)  
    productos = db.relationship('Producto', backref='marca', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'estado': self.estado, 
        }


# ===== MODIFICACIÓN DEL MODELO IMAGEN (POLIMÓRFICO) =====
class Imagen(db.Model):

    __tablename__ = 'imagen'
    
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, nullable=False) 
    url = db.Column(db.String(255), nullable=False)     
    
    def to_dict(self):
        return {
            'id': self.id,
            'producto_id': self.producto_id,
            'url': self.url
        }


class CategoriaProducto(db.Model):
    __tablename__ = 'categoria_producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(15), nullable=False)
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
    
    # Mantener todos los campos como están
    id = db.Column(db.Integer, primary_key=True)
    categoria_producto_id = db.Column(db.Integer, db.ForeignKey('categoria_producto.id'), nullable=False)
    marca_id = db.Column(db.Integer, db.ForeignKey('marca.id'), nullable=False)
    nombre = db.Column(db.String(20), nullable=False)
    precio_venta = db.Column(db.Float, nullable=False)
    precio_compra = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=0)
    descripcion = db.Column(db.String(120)) 
    estado = db.Column(db.Boolean, default=True)
    
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
            'marca_id': self.marca_id
        }


# ===== TABLA DE PEDIDOS ===== #

class Pedido(db.Model):
    __tablename__ = 'pedido'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)  # Usuario que hizo el pedido
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    metodo_pago = db.Column(db.String(20))  # 'efectivo', 'transferencia'
    metodo_entrega = db.Column(db.String(20))  # 'tienda', 'domicilio'
    direccion_entrega = db.Column(db.String(255))
    estado = db.Column(db.String(20), default='pendiente')  # 'pendiente', 'confirmado', 'en_preparacion', 'enviado', 'entregado', 'cancelado'
    transferencia_comprobante = db.Column(db.String(255))  # URL de la imagen del comprobante
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=True)  # Relación con venta cuando se procesa
    
    cliente = db.relationship('Cliente', backref='pedidos')
    usuario = db.relationship('Usuario', backref='pedidos')
    venta = db.relationship('Venta', backref='pedido', uselist=False)
    items = db.relationship('DetallePedido', backref='pedido', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'usuario_id': self.usuario_id,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'total': self.total,
            'metodo_pago': self.metodo_pago,
            'metodo_entrega': self.metodo_entrega,
            'direccion_entrega': self.direccion_entrega,
            'estado': self.estado,
            'transferencia_comprobante': self.transferencia_comprobante,
            'venta_id': self.venta_id,
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

# ===== TABLAS DE PROVEEDORES Y COMPRAS =====
class Proveedor(db.Model):
    __tablename__ = 'proveedor'
    id = db.Column(db.Integer, primary_key=True)
    tipo_proveedor = db.Column(db.String(20))  # 'Persona Natural', 'Persona Jurídica'
    tipo_documento = db.Column(db.String(4))
    documento = db.Column(db.String(20))
    razon_social_o_nombre = db.Column(db.String(30), nullable=False)
    contacto = db.Column(db.String(20))
    telefono = db.Column(db.String(10))
    correo = db.Column(db.String(50))
    departamento = db.Column(db.String(15))
    municipio = db.Column(db.String(15))
    direccion = db.Column(db.String(30))
    estado = db.Column(db.Boolean, default=True)
    compras = db.relationship('Compra', backref='proveedor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'tipo_proveedor': self.tipo_proveedor,
            'documento': self.documento,
            'razon_social_o_nombre': self.razon_social_o_nombre,
            'telefono': self.telefono,
            'correo': self.correo,
            'estado': self.estado
        }

class Compra(db.Model):
    __tablename__ = 'compra'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedor.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)  # Cambié de bool a Float como es lógico
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

# ===== TABLAS DE SERVICIOS Y CITAS =====
class Servicio(db.Model):
    __tablename__ = 'servicio'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(20), nullable=False)
    duracion_min = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(120))
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

class EstadoCita(db.Model):
    __tablename__ = 'estado_cita'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(23), nullable=False)
    citas = db.relationship('Cita', backref='estado_cita', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre
        }

# ===== TABLAS DE EMPLEADOS Y CLIENTES =====
class Empleado(db.Model):
    __tablename__ = 'empleado'
    id = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.String(4))
    numero_documento = db.Column(db.String(20), nullable=False)
    nombre = db.Column(db.String(20), nullable=False)
    telefono = db.Column(db.String(10))
    direccion = db.Column(db.String(30))
    fecha_ingreso = db.Column(db.Date, nullable=False)
    cargo = db.Column(db.String(10))
    estado = db.Column(db.Boolean, default=True)
    citas = db.relationship('Cita', backref='empleado', lazy=True)
    ventas = db.relationship('Venta', backref='empleado', lazy=True)
    horarios = db.relationship('Horario', backref='empleado', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'tipo_documento': self.tipo_documento,
            'numero_documento': self.numero_documento,
            'telefono': self.telefono,
            'direccion': self.direccion,
            'fecha_ingreso': self.fecha_ingreso.isoformat() if self.fecha_ingreso else None,
            'cargo': self.cargo,
            'estado': self.estado
        }

class Cliente(db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    tipo_documento = db.Column(db.String(4))
    numero_documento = db.Column(db.String(20), nullable=True)  # Cambié a String
    nombre = db.Column(db.String(25), nullable=False)
    apellido = db.Column(db.String(20), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=True)
    genero = db.Column(db.String(10))  # 'Masculino', 'Femenino', 'Otro'
    telefono = db.Column(db.String(20))
    correo = db.Column(db.String(30))
    municipio = db.Column(db.String(15))
    direccion = db.Column(db.String(30))
    ocupacion = db.Column(db.String(20))
    telefono_emergencia = db.Column(db.String(20))  # Cambié a String
    estado = db.Column(db.Boolean, default=True)
    citas = db.relationship('Cita', backref='cliente', lazy=True)
    ventas = db.relationship('Venta', backref='cliente', lazy=True)
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

# ===== TABLAS DE CITAS =====
class Cita(db.Model):
    __tablename__ = 'cita'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    servicio_id = db.Column(db.Integer, db.ForeignKey('servicio.id'), nullable=False)
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    metodo_pago = db.Column(db.String(15))  # 'Efectivo', 'Tarjeta', 'Transferencia'
    hora = db.Column(db.Time, nullable=False)  # ← Hacer NOT NULL
    duracion = db.Column(db.Integer)
    fecha = db.Column(db.Date, nullable=False)  # ← Cambiar de DateTime a Date
    estado_cita_id = db.Column(db.Integer, db.ForeignKey('estado_cita.id'), nullable=False)
    ventas = db.relationship('Venta', backref='cita', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'servicio_id': self.servicio_id,
            'empleado_id': self.empleado_id,
            'metodo_pago': self.metodo_pago,
            'hora': self.hora.isoformat() if self.hora else None,  # ← Agregar hora
            'duracion': self.duracion,
            'fecha': self.fecha.isoformat() if self.fecha else None,  # ← Solo fecha
            'estado_cita_id': self.estado_cita_id,
            'estado_nombre': self.estado_cita.nombre if self.estado_cita else None,
            'cliente_nombre': f"{self.cliente.nombre} {self.cliente.apellido}" if self.cliente else None,
            'servicio_nombre': self.servicio.nombre if self.servicio else None,
            'empleado_nombre': self.empleado.nombre if self.empleado else None
        }

# ===== TABLAS DE VENTAS =====
class EstadoVenta(db.Model):
    __tablename__ = 'estado_venta'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(23), nullable=False)
    ventas = db.relationship('Venta', backref='estado_venta', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre
        }

class Venta(db.Model):
    __tablename__ = 'venta'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    estado_venta_id = db.Column(db.Integer, db.ForeignKey('estado_venta.id'), nullable=False)
    cita_id = db.Column(db.Integer, db.ForeignKey('cita.id'))
    empleado_id = db.Column(db.Integer, db.ForeignKey('empleado.id'), nullable=False)
    metodo_pago = db.Column(db.String(30))  # Métodos de pago combinados
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    total_venta = db.Column(db.Float, nullable=False)
    detalles = db.relationship('DetalleVenta', backref='venta', lazy=True)
    abonos = db.relationship('Abono', backref='venta', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'total_venta': self.total_venta,
            'metodo_pago': self.metodo_pago,
            'fecha': self.fecha.isoformat()
        }

class DetalleVenta(db.Model):
    __tablename__ = 'detalle_venta'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'), nullable=False)
    venta_id = db.Column(db.Integer, db.ForeignKey('venta.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)
    descuento = db.Column(db.Float, default=0.0)
    subtotal = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'venta_id': self.venta_id,
            'producto_id': self.producto_id,
            'cantidad': self.cantidad,
            'precio_unitario': self.precio_unitario,
            'descuento': self.descuento,
            'subtotal': self.subtotal
        }

# ===== TABLAS ADICIONALES =====
class Horario(db.Model):
    __tablename__ = 'horario'
    id = db.Column(db.Integer, primary_key=True)
    empleado_id = db.Column(
        db.Integer,
        db.ForeignKey('empleado.id'),
        nullable=False
    )
    dia = db.Column(db.Integer, nullable=False)  # 0-6
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_final = db.Column(db.Time, nullable=False)
    activo = db.Column(db.Boolean, default=True)  # recomendado

    def to_dict(self):
        return {
            'id': self.id,
            'empleado_id': self.empleado_id,
            'dia': self.dia,
            'hora_inicio': self.hora_inicio.isoformat(),
            'hora_final': self.hora_final.isoformat(),
            'activo': self.activo
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
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'descripcion': self.descripcion,
            'fecha': self.fecha.isoformat()
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
            'fecha': self.fecha.isoformat()
        }
    
class Multimedia(db.Model):
    """Para: categorías, comprobantes y otros"""
    __tablename__ = 'multimedia'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)  # Cloudinary URL
    
    # Categorías
    categoria_id = db.Column(db.Integer, nullable=True)
    
    # Comprobantes
    pedido_id = db.Column(db.Integer, nullable=True)
    
    # Tipo (OBLIGATORIO)
    tipo = db.Column(db.String(20), nullable=False)  # 'categoria', 'comprobante', 'otro'
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'categoria_id': self.categoria_id,
            'pedido_id': self.pedido_id,
            'tipo': self.tipo
        }