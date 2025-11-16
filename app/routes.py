from flask import Blueprint, jsonify, request
from app.database import db
from app.models import (
    # Tablas existentes
    Marca, CategoriaProducto, Producto, Imagen,
    # Nuevas tablas principales
    Usuario, Rol, Cliente, Empleado, Proveedor, 
    Venta, Cita, Servicio, EstadoCita, EstadoVenta,
    DetalleVenta, Compra, DetalleCompra
)
from datetime import datetime

main_bp = Blueprint('main', __name__)

# ===== RUTA PRINCIPAL ACTUALIZADA =====
@main_bp.route('/')
def home():
    return jsonify({
        "message": "API Óptica - Sistema Completo", 
        "version": "2.0",
        "modulos": {
            "productos": "GET /productos, /marcas, /categorias",
            "clientes": "GET /clientes",
            "empleados": "GET /empleados", 
            "proveedores": "GET /proveedores",
            "ventas": "GET /ventas",
            "citas": "GET /citas",
            "servicios": "GET /servicios",
            "usuarios": "GET /usuarios"
        }
    })

# ===== MÓDULO PRODUCTOS (EXISTENTE) =====
@main_bp.route('/marcas', methods=['GET'])
def get_marcas():
    try:
        marcas = Marca.query.all()
        return jsonify([marca.to_dict() for marca in marcas])
    except Exception as e:
        return jsonify({"error": "Error al obtener marcas"}), 500

@main_bp.route('/marcas', methods=['POST'])
def create_marca():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        
        marca = Marca(nombre=data['nombre'])
        db.session.add(marca)
        db.session.commit()
        return jsonify({"message": "Marca creada", "marca": marca.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear marca"}), 500

@main_bp.route('/categorias', methods=['GET'])
def get_categorias():
    try:
        categorias = CategoriaProducto.query.all()
        return jsonify([categoria.to_dict() for categoria in categorias])
    except Exception as e:
        return jsonify({"error": "Error al obtener categorías"}), 500

@main_bp.route('/categorias', methods=['POST'])
def create_categoria():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400
        
        categoria = CategoriaProducto(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', '')
        )
        db.session.add(categoria)
        db.session.commit()
        return jsonify({"message": "Categoría creada", "categoria": categoria.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear categoría"}), 500

@main_bp.route('/productos', methods=['GET'])
def get_productos():
    try:
        productos = Producto.query.all()
        return jsonify([producto.to_dict() for producto in productos])
    except Exception as e:
        return jsonify({"error": "Error al obtener productos"}), 500

@main_bp.route('/productos', methods=['POST'])
def create_producto():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'precio_venta', 'precio_compra', 'categoria_producto_id', 'marca_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        producto = Producto(
            nombre=data['nombre'],
            precio_venta=float(data['precio_venta']),
            precio_compra=float(data['precio_compra']),
            stock=data.get('stock', 0),
            stock_minimo=data.get('stock_minimo', 5),
            descripcion=data.get('descripcion', ''),
            categoria_producto_id=data['categoria_producto_id'],
            marca_id=data['marca_id']
        )
        db.session.add(producto)
        db.session.commit()
        return jsonify({"message": "Producto creado", "producto": producto.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear producto"}), 500

# ===== MÓDULO CLIENTES =====
@main_bp.route('/clientes', methods=['GET'])
def get_clientes():
    try:
        clientes = Cliente.query.all()
        return jsonify([cliente.to_dict() for cliente in clientes])
    except Exception as e:
        return jsonify({"error": "Error al obtener clientes"}), 500

@main_bp.route('/clientes', methods=['POST'])
def create_cliente():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'apellido', 'numero_documento', 'fecha_nacimiento']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        cliente = Cliente(
            nombre=data['nombre'],
            apellido=data['apellido'],
            tipo_documento=data.get('tipo_documento'),
            numero_documento=data['numero_documento'],
            fecha_nacimiento=datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date(),
            genero=data.get('genero'),
            telefono=data.get('telefono'),
            correo=data.get('correo'),
            municipio=data.get('municipio'),
            direccion=data.get('direccion'),
            ocupacion=data.get('ocupacion'),
            telefono_emergencia=data.get('telefono_emergencia')
        )
        db.session.add(cliente)
        db.session.commit()
        return jsonify({"message": "Cliente creado", "cliente": cliente.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear cliente"}), 500

# ===== MÓDULO EMPLEADOS =====
@main_bp.route('/empleados', methods=['GET'])
def get_empleados():
    try:
        empleados = Empleado.query.all()
        return jsonify([empleado.to_dict() for empleado in empleados])
    except Exception as e:
        return jsonify({"error": "Error al obtener empleados"}), 500

@main_bp.route('/empleados', methods=['POST'])
def create_empleado():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'numero_documento', 'fecha_ingreso']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        empleado = Empleado(
            nombre=data['nombre'],
            tipo_documento=data.get('tipo_documento'),
            numero_documento=data['numero_documento'],
            telefono=data.get('telefono'),
            direccion=data.get('direccion'),
            fecha_ingreso=datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date(),
            cargo=data.get('cargo')
        )
        db.session.add(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado creado", "empleado": empleado.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear empleado"}), 500

# ===== MÓDULO PROVEEDORES =====
@main_bp.route('/proveedores', methods=['GET'])
def get_proveedores():
    try:
        proveedores = Proveedor.query.all()
        return jsonify([proveedor.to_dict() for proveedor in proveedores])
    except Exception as e:
        return jsonify({"error": "Error al obtener proveedores"}), 500

@main_bp.route('/proveedores', methods=['POST'])
def create_proveedor():
    try:
        data = request.get_json()
        if not data.get('razon_social_o_nombre'):
            return jsonify({"error": "La razón social o nombre es requerido"}), 400

        proveedor = Proveedor(
            tipo_proveedor=data.get('tipo_proveedor'),
            tipo_documento=data.get('tipo_documento'),
            documento=data.get('documento'),
            razon_social_o_nombre=data['razon_social_o_nombre'],
            contacto=data.get('contacto'),
            telefono=data.get('telefono'),
            correo=data.get('correo'),
            departamento=data.get('departamento'),
            municipio=data.get('municipio'),
            direccion=data.get('direccion')
        )
        db.session.add(proveedor)
        db.session.commit()
        return jsonify({"message": "Proveedor creado", "proveedor": proveedor.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear proveedor"}), 500

# ===== MÓDULO VENTAS =====
@main_bp.route('/ventas', methods=['GET'])
def get_ventas():
    try:
        ventas = Venta.query.all()
        return jsonify([venta.to_dict() for venta in ventas])
    except Exception as e:
        return jsonify({"error": "Error al obtener ventas"}), 500

@main_bp.route('/ventas', methods=['POST'])
def create_venta():
    try:
        data = request.get_json()
        required_fields = ['cliente_id', 'empleado_id', 'total_venta', 'estado_venta_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        venta = Venta(
            cliente_id=data['cliente_id'],
            empleado_id=data['empleado_id'],
            estado_venta_id=data['estado_venta_id'],
            cita_id=data.get('cita_id'),
            metodo_pago=data.get('metodo_pago'),
            total_venta=float(data['total_venta'])
        )
        db.session.add(venta)
        db.session.commit()
        return jsonify({"message": "Venta creada", "venta": venta.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear venta"}), 500

# ===== MÓDULO CITAS =====
@main_bp.route('/citas', methods=['GET'])
def get_citas():
    try:
        citas = Cita.query.all()
        return jsonify([cita.to_dict() for cita in citas])
    except Exception as e:
        return jsonify({"error": "Error al obtener citas"}), 500

@main_bp.route('/citas', methods=['POST'])
def create_cita():
    try:
        data = request.get_json()
        required_fields = ['cliente_id', 'servicio_id', 'empleado_id', 'fecha', 'estado_cita_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        cita = Cita(
            cliente_id=data['cliente_id'],
            servicio_id=data['servicio_id'],
            empleado_id=data['empleado_id'],
            estado_cita_id=data['estado_cita_id'],
            metodo_pago=data.get('metodo_pago'),
            hora=datetime.strptime(data['hora'], '%H:%M').time() if data.get('hora') else None,
            duracion=data.get('duracion'),
            fecha=datetime.strptime(data['fecha'], '%Y-%m-%d %H:%M')
        )
        db.session.add(cita)
        db.session.commit()
        return jsonify({"message": "Cita creada", "cita": cita.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear cita"}), 500

# ===== MÓDULO SERVICIOS =====
@main_bp.route('/servicios', methods=['GET'])
def get_servicios():
    try:
        servicios = Servicio.query.all()
        return jsonify([servicio.to_dict() for servicio in servicios])
    except Exception as e:
        return jsonify({"error": "Error al obtener servicios"}), 500

@main_bp.route('/servicios', methods=['POST'])
def create_servicio():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'duracion_min', 'precio']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        servicio = Servicio(
            nombre=data['nombre'],
            duracion_min=data['duracion_min'],
            precio=float(data['precio']),
            descripcion=data.get('descripcion', '')
        )
        db.session.add(servicio)
        db.session.commit()
        return jsonify({"message": "Servicio creado", "servicio": servicio.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear servicio"}), 500

# ===== MÓDULO USUARIOS =====
@main_bp.route('/usuarios', methods=['GET'])
def get_usuarios():
    try:
        usuarios = Usuario.query.all()
        return jsonify([usuario.to_dict() for usuario in usuarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener usuarios"}), 500

@main_bp.route('/usuarios', methods=['POST'])
def create_usuario():
    try:
        data = request.get_json()
        required_fields = ['nombre', 'correo', 'contrasenia', 'rol_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        usuario = Usuario(
            nombre=data['nombre'],
            correo=data['correo'],
            contrasenia=data['contrasenia'],  # En producción, hashear esta contraseña
            rol_id=data['rol_id']
        )
        db.session.add(usuario)
        db.session.commit()
        return jsonify({"message": "Usuario creado", "usuario": usuario.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear usuario"}), 500

# ===== RUTAS PARA OBTENER UN ELEMENTO ESPECÍFICO =====
@main_bp.route('/<tabla>/<int:id>', methods=['GET'])
def get_elemento(tabla, id):
    try:
        modelos = {
            'productos': Producto,
            'clientes': Cliente,
            'empleados': Empleado,
            'proveedores': Proveedor,
            'ventas': Venta,
            'citas': Cita,
            'servicios': Servicio,
            'usuarios': Usuario,
            'marcas': Marca,
            'categorias': CategoriaProducto
        }
        
        if tabla not in modelos:
            return jsonify({"error": "Tabla no encontrada"}), 404
            
        elemento = modelos[tabla].query.get(id)
        if not elemento:
            return jsonify({"error": f"{tabla[:-1]} no encontrado"}), 404
            
        return jsonify(elemento.to_dict())
    except Exception as e:
        return jsonify({"error": "Error al obtener elemento"}), 500

# ===== ESTADÍSTICAS GENERALES =====
@main_bp.route('/dashboard/estadisticas', methods=['GET'])
def get_estadisticas():
    try:
        total_clientes = Cliente.query.count()
        total_empleados = Empleado.query.count()
        total_productos = Producto.query.count()
        total_ventas = Venta.query.count()
        total_citas = Cita.query.count()
        
        return jsonify({
            "total_clientes": total_clientes,
            "total_empleados": total_empleados,
            "total_productos": total_productos,
            "total_ventas": total_ventas,
            "total_citas": total_citas
        })
    except Exception as e:
        return jsonify({"error": "Error al obtener estadísticas"}), 500