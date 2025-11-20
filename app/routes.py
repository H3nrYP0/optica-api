from flask import Blueprint, jsonify, request
from app.database import db
from app.models import (
    # Tablas existentes
    Marca, CategoriaProducto, Producto, Imagen,
    # Nuevas tablas principales
    Usuario, Rol, Cliente, Empleado, Proveedor, 
    Venta, Cita, Servicio, EstadoCita, EstadoVenta,
    DetalleVenta, Compra, DetalleCompra, HistorialFormula, Horario, Abono, Permiso,
    PermisoPorRol
)
from datetime import datetime

main_bp = Blueprint('main', __name__)

# ===== RUTA PRINCIPAL ACTUALIZADA =====
@main_bp.route('/')
def home():
    return jsonify({
        "message": "API Óptica - Sistema Completo", 
        "version": "3.0",
        "modulos_principales": {
            "clientes": "GET/POST /clientes",
            "empleados": "GET/POST /empleados", 
            "proveedores": "GET/POST /proveedores",
            "ventas": "GET/POST /ventas",
            "citas": "GET/POST /citas",
            "servicios": "GET/POST /servicios",
            "usuarios": "GET/POST /usuarios",
            "roles": "GET/POST /roles",
            "productos": "GET/POST /productos, /marcas, /categorias"
        },
        "modulos_secundarios": {
            "compras": "GET/POST /compras",
            "detalle_venta": "GET/POST /detalle-venta",
            "detalle_compra": "GET/POST /detalle-compra",
            "estado_cita": "GET/POST /estado-cita",
            "estado_venta": "GET/POST /estado-venta",
            "horario": "GET/POST /horario",
            "historial_formula": "GET/POST /historial-formula",
            "abono": "GET/POST /abono",
            "permiso": "GET/POST /permiso",
            "permiso_rol": "GET/POST /permiso-rol"
        },
        "relaciones": {
            "detalles_venta": "GET /ventas/{id}/detalles",
            "detalles_compra": "GET /compras/{id}/detalles", 
            "historial_cliente": "GET /clientes/{id}/historial",
            "horarios_empleado": "GET /empleados/{id}/horarios"
        },
        "utilidades": {
            "dashboard": "GET /dashboard/estadisticas",
            "elemento_especifico": "GET /{tabla}/{id}",
            "todos_endpoints": "GET /endpoints"
        },
        "documentacion_completa": "GET /endpoints para ver todos los endpoints disponibles"
    })

# ===== MÓDULO MARCAS - COMPLETAR CRUD =====
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

@main_bp.route('/marcas/<int:id>', methods=['PUT'])
def update_marca(id):
    try:
        marca = Marca.query.get(id)
        if not marca:
            return jsonify({"error": "Marca no encontrada"}), 404

        data = request.get_json()
        if 'nombre' in data:
            marca.nombre = data['nombre']

        db.session.commit()
        return jsonify({"message": "Marca actualizada", "marca": marca.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar marca"}), 500

@main_bp.route('/marcas/<int:id>', methods=['DELETE'])
def delete_marca(id):
    try:
        marca = Marca.query.get(id)
        if not marca:
            return jsonify({"error": "Marca no encontrada"}), 404

        db.session.delete(marca)
        db.session.commit()
        return jsonify({"message": "Marca eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar marca"}), 500

# ===== MÓDULO CATEGORÍAS - COMPLETAR CRUD =====
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

@main_bp.route('/categorias/<int:id>', methods=['PUT'])
def update_categoria(id):
    try:
        categoria = CategoriaProducto.query.get(id)
        if not categoria:
            return jsonify({"error": "Categoría no encontrada"}), 404

        data = request.get_json()
        if 'nombre' in data:
            categoria.nombre = data['nombre']
        if 'descripcion' in data:
            categoria.descripcion = data['descripcion']

        db.session.commit()
        return jsonify({"message": "Categoría actualizada", "categoria": categoria.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar categoría"}), 500

@main_bp.route('/categorias/<int:id>', methods=['DELETE'])
def delete_categoria(id):
    try:
        categoria = CategoriaProducto.query.get(id)
        if not categoria:
            return jsonify({"error": "Categoría no encontrada"}), 404

        db.session.delete(categoria)
        db.session.commit()
        return jsonify({"message": "Categoría eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar categoría"}), 500

# ===== MÓDULO PRODUCTOS - COMPLETAR CRUD =====
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

@main_bp.route('/productos/<int:id>', methods=['PUT'])
def update_producto(id):
    try:
        producto = Producto.query.get(id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            producto.nombre = data['nombre']
        if 'precio_venta' in data:
            producto.precio_venta = float(data['precio_venta'])
        if 'precio_compra' in data:
            producto.precio_compra = float(data['precio_compra'])
        if 'stock' in data:
            producto.stock = data['stock']
        if 'stock_minimo' in data:
            producto.stock_minimo = data['stock_minimo']
        if 'descripcion' in data:
            producto.descripcion = data['descripcion']
        if 'categoria_producto_id' in data:
            producto.categoria_producto_id = data['categoria_producto_id']
        if 'marca_id' in data:
            producto.marca_id = data['marca_id']

        db.session.commit()
        return jsonify({"message": "Producto actualizado", "producto": producto.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar producto"}), 500

@main_bp.route('/productos/<int:id>', methods=['DELETE'])
def delete_producto(id):
    try:
        producto = Producto.query.get(id)
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404

        db.session.delete(producto)
        db.session.commit()
        return jsonify({"message": "Producto eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar producto"}), 500

# ===== MÓDULO CLIENTES - COMPLETAR CRUD =====
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

@main_bp.route('/clientes/<int:id>', methods=['PUT'])
def update_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            cliente.nombre = data['nombre']
        if 'apellido' in data:
            cliente.apellido = data['apellido']
        if 'tipo_documento' in data:
            cliente.tipo_documento = data['tipo_documento']
        if 'numero_documento' in data:
            cliente.numero_documento = data['numero_documento']
        if 'fecha_nacimiento' in data:
            cliente.fecha_nacimiento = datetime.strptime(data['fecha_nacimiento'], '%Y-%m-%d').date()
        if 'genero' in data:
            cliente.genero = data['genero']
        if 'telefono' in data:
            cliente.telefono = data['telefono']
        if 'correo' in data:
            cliente.correo = data['correo']
        if 'municipio' in data:
            cliente.municipio = data['municipio']
        if 'direccion' in data:
            cliente.direccion = data['direccion']
        if 'ocupacion' in data:
            cliente.ocupacion = data['ocupacion']
        if 'telefono_emergencia' in data:
            cliente.telefono_emergencia = data['telefono_emergencia']

        db.session.commit()
        return jsonify({"message": "Cliente actualizado", "cliente": cliente.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar cliente"}), 500

@main_bp.route('/clientes/<int:id>', methods=['DELETE'])
def delete_cliente(id):
    try:
        cliente = Cliente.query.get(id)
        if not cliente:
            return jsonify({"error": "Cliente no encontrado"}), 404

        db.session.delete(cliente)
        db.session.commit()
        return jsonify({"message": "Cliente eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar cliente"}), 500

# ===== MÓDULO EMPLEADOS - COMPLETAR CRUD =====
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

@main_bp.route('/empleados/<int:id>', methods=['PUT'])
def update_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            empleado.nombre = data['nombre']
        if 'tipo_documento' in data:
            empleado.tipo_documento = data['tipo_documento']
        if 'numero_documento' in data:
            empleado.numero_documento = data['numero_documento']
        if 'telefono' in data:
            empleado.telefono = data['telefono']
        if 'direccion' in data:
            empleado.direccion = data['direccion']
        if 'fecha_ingreso' in data:
            empleado.fecha_ingreso = datetime.strptime(data['fecha_ingreso'], '%Y-%m-%d').date()
        if 'cargo' in data:
            empleado.cargo = data['cargo']

        db.session.commit()
        return jsonify({"message": "Empleado actualizado", "empleado": empleado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar empleado"}), 500

@main_bp.route('/empleados/<int:id>', methods=['DELETE'])
def delete_empleado(id):
    try:
        empleado = Empleado.query.get(id)
        if not empleado:
            return jsonify({"error": "Empleado no encontrado"}), 404

        db.session.delete(empleado)
        db.session.commit()
        return jsonify({"message": "Empleado eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar empleado"}), 500

# ===== MÓDULO PROVEEDORES - COMPLETAR CRUD =====
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

@main_bp.route('/proveedores/<int:id>', methods=['PUT'])
def update_proveedor(id):
    try:
        proveedor = Proveedor.query.get(id)
        if not proveedor:
            return jsonify({"error": "Proveedor no encontrado"}), 404

        data = request.get_json()
        if 'tipo_proveedor' in data:
            proveedor.tipo_proveedor = data['tipo_proveedor']
        if 'tipo_documento' in data:
            proveedor.tipo_documento = data['tipo_documento']
        if 'documento' in data:
            proveedor.documento = data['documento']
        if 'razon_social_o_nombre' in data:
            proveedor.razon_social_o_nombre = data['razon_social_o_nombre']
        if 'contacto' in data:
            proveedor.contacto = data['contacto']
        if 'telefono' in data:
            proveedor.telefono = data['telefono']
        if 'correo' in data:
            proveedor.correo = data['correo']
        if 'departamento' in data:
            proveedor.departamento = data['departamento']
        if 'municipio' in data:
            proveedor.municipio = data['municipio']
        if 'direccion' in data:
            proveedor.direccion = data['direccion']

        db.session.commit()
        return jsonify({"message": "Proveedor actualizado", "proveedor": proveedor.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar proveedor"}), 500

@main_bp.route('/proveedores/<int:id>', methods=['DELETE'])
def delete_proveedor(id):
    try:
        proveedor = Proveedor.query.get(id)
        if not proveedor:
            return jsonify({"error": "Proveedor no encontrado"}), 404

        db.session.delete(proveedor)
        db.session.commit()
        return jsonify({"message": "Proveedor eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar proveedor"}), 500

# ===== MÓDULO USUARIOS - COMPLETAR CRUD =====
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
            contrasenia=data['contrasenia'],
            rol_id=data['rol_id']
        )
        db.session.add(usuario)
        db.session.commit()
        return jsonify({"message": "Usuario creado", "usuario": usuario.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear usuario"}), 500

@main_bp.route('/usuarios/<int:id>', methods=['PUT'])
def update_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            usuario.nombre = data['nombre']
        if 'correo' in data:
            usuario.correo = data['correo']
        if 'contrasenia' in data:
            usuario.contrasenia = data['contrasenia']
        if 'rol_id' in data:
            usuario.rol_id = data['rol_id']

        db.session.commit()
        return jsonify({"message": "Usuario actualizado", "usuario": usuario.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar usuario"}), 500

@main_bp.route('/usuarios/<int:id>', methods=['DELETE'])
def delete_usuario(id):
    try:
        usuario = Usuario.query.get(id)
        if not usuario:
            return jsonify({"error": "Usuario no encontrado"}), 404

        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"message": "Usuario eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar usuario"}), 500

# ===== MÓDULO ROLES - COMPLETAR CRUD =====
@main_bp.route('/roles', methods=['GET'])
def get_roles():
    try:
        roles = Rol.query.all()
        return jsonify([rol.to_dict() for rol in roles])
    except Exception as e:
        return jsonify({"error": "Error al obtener roles"}), 500

@main_bp.route('/roles', methods=['POST'])
def create_rol():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        rol = Rol(
            nombre=data['nombre'],
            descripcion=data.get('descripcion', ''),
            estado=data.get('estado', True)
        )
        db.session.add(rol)
        db.session.commit()
        return jsonify({"message": "Rol creado", "rol": rol.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear rol"}), 500

@main_bp.route('/roles/<int:id>', methods=['PUT'])
def update_rol(id):
    try:
        rol = Rol.query.get(id)
        if not rol:
            return jsonify({"error": "Rol no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            rol.nombre = data['nombre']
        if 'descripcion' in data:
            rol.descripcion = data['descripcion']
        if 'estado' in data:
            rol.estado = data['estado']

        db.session.commit()
        return jsonify({"message": "Rol actualizado", "rol": rol.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar rol"}), 500

@main_bp.route('/roles/<int:id>', methods=['DELETE'])
def delete_rol(id):
    try:
        rol = Rol.query.get(id)
        if not rol:
            return jsonify({"error": "Rol no encontrado"}), 404

        db.session.delete(rol)
        db.session.commit()
        return jsonify({"message": "Rol eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar rol"}), 500

# ===== MÓDULO VENTAS - COMPLETAR CRUD =====
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

@main_bp.route('/ventas/<int:id>', methods=['PUT'])
def update_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404

        data = request.get_json()
        if 'cliente_id' in data:
            venta.cliente_id = data['cliente_id']
        if 'empleado_id' in data:
            venta.empleado_id = data['empleado_id']
        if 'estado_venta_id' in data:
            venta.estado_venta_id = data['estado_venta_id']
        if 'cita_id' in data:
            venta.cita_id = data['cita_id']
        if 'metodo_pago' in data:
            venta.metodo_pago = data['metodo_pago']
        if 'total_venta' in data:
            venta.total_venta = float(data['total_venta'])

        db.session.commit()
        return jsonify({"message": "Venta actualizada", "venta": venta.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar venta"}), 500

@main_bp.route('/ventas/<int:id>', methods=['DELETE'])
def delete_venta(id):
    try:
        venta = Venta.query.get(id)
        if not venta:
            return jsonify({"error": "Venta no encontrada"}), 404

        db.session.delete(venta)
        db.session.commit()
        return jsonify({"message": "Venta eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar venta"}), 500

# ===== MÓDULO CITAS - COMPLETAR CRUD =====
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

@main_bp.route('/citas/<int:id>', methods=['PUT'])
def update_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404

        data = request.get_json()
        if 'cliente_id' in data:
            cita.cliente_id = data['cliente_id']
        if 'servicio_id' in data:
            cita.servicio_id = data['servicio_id']
        if 'empleado_id' in data:
            cita.empleado_id = data['empleado_id']
        if 'estado_cita_id' in data:
            cita.estado_cita_id = data['estado_cita_id']
        if 'metodo_pago' in data:
            cita.metodo_pago = data['metodo_pago']
        if 'hora' in data:
            cita.hora = datetime.strptime(data['hora'], '%H:%M').time()
        if 'duracion' in data:
            cita.duracion = data['duracion']
        if 'fecha' in data:
            cita.fecha = datetime.strptime(data['fecha'], '%Y-%m-%d %H:%M')

        db.session.commit()
        return jsonify({"message": "Cita actualizada", "cita": cita.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar cita"}), 500

@main_bp.route('/citas/<int:id>', methods=['DELETE'])
def delete_cita(id):
    try:
        cita = Cita.query.get(id)
        if not cita:
            return jsonify({"error": "Cita no encontrada"}), 404

        db.session.delete(cita)
        db.session.commit()
        return jsonify({"message": "Cita eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar cita"}), 500

# ===== MÓDULO SERVICIOS - COMPLETAR CRUD =====
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

@main_bp.route('/servicios/<int:id>', methods=['PUT'])
def update_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            servicio.nombre = data['nombre']
        if 'duracion_min' in data:
            servicio.duracion_min = data['duracion_min']
        if 'precio' in data:
            servicio.precio = float(data['precio'])
        if 'descripcion' in data:
            servicio.descripcion = data['descripcion']

        db.session.commit()
        return jsonify({"message": "Servicio actualizado", "servicio": servicio.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar servicio"}), 500

@main_bp.route('/servicios/<int:id>', methods=['DELETE'])
def delete_servicio(id):
    try:
        servicio = Servicio.query.get(id)
        if not servicio:
            return jsonify({"error": "Servicio no encontrado"}), 404

        db.session.delete(servicio)
        db.session.commit()
        return jsonify({"message": "Servicio eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar servicio"}), 500

# ===== MÓDULO COMPRAS - COMPLETAR CRUD =====
@main_bp.route('/compras', methods=['GET'])
def get_compras():
    try:
        compras = Compra.query.all()
        return jsonify([compra.to_dict() for compra in compras])
    except Exception as e:
        return jsonify({"error": "Error al obtener compras"}), 500

@main_bp.route('/compras', methods=['POST'])
def create_compra():
    try:
        data = request.get_json()
        required_fields = ['proveedor_id', 'total']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        compra = Compra(
            proveedor_id=data['proveedor_id'],
            total=float(data['total']),
            estado_compra=data.get('estado_compra', True)
        )
        db.session.add(compra)
        db.session.commit()
        return jsonify({"message": "Compra creada", "compra": compra.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear compra"}), 500

@main_bp.route('/compras/<int:id>', methods=['PUT'])
def update_compra(id):
    try:
        compra = Compra.query.get(id)
        if not compra:
            return jsonify({"error": "Compra no encontrada"}), 404

        data = request.get_json()
        if 'proveedor_id' in data:
            compra.proveedor_id = data['proveedor_id']
        if 'total' in data:
            compra.total = float(data['total'])
        if 'estado_compra' in data:
            compra.estado_compra = data['estado_compra']

        db.session.commit()
        return jsonify({"message": "Compra actualizada", "compra": compra.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar compra"}), 500

@main_bp.route('/compras/<int:id>', methods=['DELETE'])
def delete_compra(id):
    try:
        compra = Compra.query.get(id)
        if not compra:
            return jsonify({"error": "Compra no encontrada"}), 404

        db.session.delete(compra)
        db.session.commit()
        return jsonify({"message": "Compra eliminada correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar compra"}), 500

# ===== TABLAS SECUNDARIAS - DETALLES VENTA - COMPLETAR CRUD =====
@main_bp.route('/detalle-venta', methods=['GET'])
def get_detalles_venta():
    try:
        detalles = DetalleVenta.query.all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de venta"}), 500

@main_bp.route('/detalle-venta', methods=['POST'])
def create_detalle_venta():
    try:
        data = request.get_json()
        required_fields = ['venta_id', 'producto_id', 'cantidad', 'precio_unitario']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        detalle = DetalleVenta(
            venta_id=data['venta_id'],
            producto_id=data['producto_id'],
            cantidad=data['cantidad'],
            precio_unitario=float(data['precio_unitario']),
            descuento=data.get('descuento', 0.0),
            subtotal=float(data['cantidad']) * float(data['precio_unitario']) - float(data.get('descuento', 0.0))
        )
        db.session.add(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de venta creado", "detalle": detalle.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear detalle de venta"}), 500

@main_bp.route('/detalle-venta/<int:id>', methods=['PUT'])
def update_detalle_venta(id):
    try:
        detalle = DetalleVenta.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de venta no encontrado"}), 404

        data = request.get_json()
        if 'venta_id' in data:
            detalle.venta_id = data['venta_id']
        if 'producto_id' in data:
            detalle.producto_id = data['producto_id']
        if 'cantidad' in data:
            detalle.cantidad = data['cantidad']
        if 'precio_unitario' in data:
            detalle.precio_unitario = float(data['precio_unitario'])
        if 'descuento' in data:
            detalle.descuento = float(data['descuento'])
        if 'cantidad' in data and 'precio_unitario' in data:
            detalle.subtotal = float(data['cantidad']) * float(data['precio_unitario']) - float(data.get('descuento', detalle.descuento))

        db.session.commit()
        return jsonify({"message": "Detalle de venta actualizado", "detalle": detalle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar detalle de venta"}), 500

@main_bp.route('/detalle-venta/<int:id>', methods=['DELETE'])
def delete_detalle_venta(id):
    try:
        detalle = DetalleVenta.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de venta no encontrado"}), 404

        db.session.delete(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de venta eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar detalle de venta"}), 500

# ===== TABLAS SECUNDARIAS - DETALLES COMPRA - COMPLETAR CRUD =====
@main_bp.route('/detalle-compra', methods=['GET'])
def get_detalles_compra():
    try:
        detalles = DetalleCompra.query.all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de compra"}), 500

@main_bp.route('/detalle-compra', methods=['POST'])
def create_detalle_compra():
    try:
        data = request.get_json()
        required_fields = ['compra_id', 'producto_id', 'cantidad', 'precio_unidad']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        detalle = DetalleCompra(
            compra_id=data['compra_id'],
            producto_id=data['producto_id'],
            cantidad=data['cantidad'],
            precio_unidad=float(data['precio_unidad']),
            subtotal=float(data['cantidad']) * float(data['precio_unidad'])
        )
        db.session.add(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de compra creado", "detalle": detalle.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear detalle de compra"}), 500

@main_bp.route('/detalle-compra/<int:id>', methods=['PUT'])
def update_detalle_compra(id):
    try:
        detalle = DetalleCompra.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de compra no encontrado"}), 404

        data = request.get_json()
        if 'compra_id' in data:
            detalle.compra_id = data['compra_id']
        if 'producto_id' in data:
            detalle.producto_id = data['producto_id']
        if 'cantidad' in data:
            detalle.cantidad = data['cantidad']
        if 'precio_unidad' in data:
            detalle.precio_unidad = float(data['precio_unidad'])
        if 'cantidad' in data and 'precio_unidad' in data:
            detalle.subtotal = float(data['cantidad']) * float(data['precio_unidad'])

        db.session.commit()
        return jsonify({"message": "Detalle de compra actualizado", "detalle": detalle.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar detalle de compra"}), 500

@main_bp.route('/detalle-compra/<int:id>', methods=['DELETE'])
def delete_detalle_compra(id):
    try:
        detalle = DetalleCompra.query.get(id)
        if not detalle:
            return jsonify({"error": "Detalle de compra no encontrado"}), 404

        db.session.delete(detalle)
        db.session.commit()
        return jsonify({"message": "Detalle de compra eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar detalle de compra"}), 500

# ===== TABLAS MAESTRAS - ESTADO CITA - COMPLETAR CRUD =====
@main_bp.route('/estado-cita', methods=['GET'])
def get_estados_cita():
    try:
        estados = EstadoCita.query.all()
        return jsonify([estado.to_dict() for estado in estados])
    except Exception as e:
        return jsonify({"error": "Error al obtener estados de cita"}), 500

@main_bp.route('/estado-cita', methods=['POST'])
def create_estado_cita():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        estado = EstadoCita(nombre=data['nombre'])
        db.session.add(estado)
        db.session.commit()
        return jsonify({"message": "Estado de cita creado", "estado": estado.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear estado de cita"}), 500

@main_bp.route('/estado-cita/<int:id>', methods=['PUT'])
def update_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de cita no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            estado.nombre = data['nombre']

        db.session.commit()
        return jsonify({"message": "Estado de cita actualizado", "estado": estado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar estado de cita"}), 500

@main_bp.route('/estado-cita/<int:id>', methods=['DELETE'])
def delete_estado_cita(id):
    try:
        estado = EstadoCita.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de cita no encontrado"}), 404

        db.session.delete(estado)
        db.session.commit()
        return jsonify({"message": "Estado de cita eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar estado de cita"}), 500

# ===== TABLAS MAESTRAS - ESTADO VENTA - COMPLETAR CRUD =====
@main_bp.route('/estado-venta', methods=['GET'])
def get_estados_venta():
    try:
        estados = EstadoVenta.query.all()
        return jsonify([estado.to_dict() for estado in estados])
    except Exception as e:
        return jsonify({"error": "Error al obtener estados de venta"}), 500

@main_bp.route('/estado-venta', methods=['POST'])
def create_estado_venta():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        estado = EstadoVenta(nombre=data['nombre'])
        db.session.add(estado)
        db.session.commit()
        return jsonify({"message": "Estado de venta creado", "estado": estado.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear estado de venta"}), 500

@main_bp.route('/estado-venta/<int:id>', methods=['PUT'])
def update_estado_venta(id):
    try:
        estado = EstadoVenta.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de venta no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            estado.nombre = data['nombre']

        db.session.commit()
        return jsonify({"message": "Estado de venta actualizado", "estado": estado.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar estado de venta"}), 500

@main_bp.route('/estado-venta/<int:id>', methods=['DELETE'])
def delete_estado_venta(id):
    try:
        estado = EstadoVenta.query.get(id)
        if not estado:
            return jsonify({"error": "Estado de venta no encontrado"}), 404

        db.session.delete(estado)
        db.session.commit()
        return jsonify({"message": "Estado de venta eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar estado de venta"}), 500

# ===== TABLAS DEL SISTEMA - HORARIO - COMPLETAR CRUD =====
@main_bp.route('/horario', methods=['GET'])
def get_horarios():
    try:
        horarios = Horario.query.all()
        return jsonify([horario.to_dict() for horario in horarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios"}), 500

@main_bp.route('/horario', methods=['POST'])
def create_horario():
    try:
        data = request.get_json()
        required_fields = ['empleado_id', 'hora_inicio', 'hora_final', 'dia']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        horario = Horario(
            empleado_id=data['empleado_id'],
            hora_inicio=datetime.strptime(data['hora_inicio'], '%H:%M').time(),
            hora_final=datetime.strptime(data['hora_final'], '%H:%M').time(),
            dia=data['dia']
        )
        db.session.add(horario)
        db.session.commit()
        return jsonify({"message": "Horario creado", "horario": horario.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear horario"}), 500

@main_bp.route('/horario/<int:id>', methods=['PUT'])
def update_horario(id):
    try:
        horario = Horario.query.get(id)
        if not horario:
            return jsonify({"error": "Horario no encontrado"}), 404

        data = request.get_json()
        if 'empleado_id' in data:
            horario.empleado_id = data['empleado_id']
        if 'hora_inicio' in data:
            horario.hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
        if 'hora_final' in data:
            horario.hora_final = datetime.strptime(data['hora_final'], '%H:%M').time()
        if 'dia' in data:
            horario.dia = data['dia']

        db.session.commit()
        return jsonify({"message": "Horario actualizado", "horario": horario.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar horario"}), 500

@main_bp.route('/horario/<int:id>', methods=['DELETE'])
def delete_horario(id):
    try:
        horario = Horario.query.get(id)
        if not horario:
            return jsonify({"error": "Horario no encontrado"}), 404

        db.session.delete(horario)
        db.session.commit()
        return jsonify({"message": "Horario eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar horario"}), 500

# ===== TABLAS DEL SISTEMA - HISTORIAL FORMULA - COMPLETAR CRUD =====
@main_bp.route('/historial-formula', methods=['GET'])
def get_historiales_formula():
    try:
        historiales = HistorialFormula.query.all()
        return jsonify([historial.to_dict() for historial in historiales])
    except Exception as e:
        return jsonify({"error": "Error al obtener historial de fórmulas"}), 500

@main_bp.route('/historial-formula', methods=['POST'])
def create_historial_formula():
    try:
        data = request.get_json()
        if not data.get('cliente_id'):
            return jsonify({"error": "El cliente_id es requerido"}), 400

        historial = HistorialFormula(
            cliente_id=data['cliente_id'],
            descripcion=data.get('descripcion', ''),
            od_esfera=data.get('od_esfera'),
            od_cilindro=data.get('od_cilindro'),
            od_eje=data.get('od_eje'),
            oi_esfera=data.get('oi_esfera'),
            oi_cilindro=data.get('oi_cilindro'),
            oi_eje=data.get('oi_eje')
        )
        db.session.add(historial)
        db.session.commit()
        return jsonify({"message": "Historial de fórmula creado", "historial": historial.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear historial de fórmula"}), 500

@main_bp.route('/historial-formula/<int:id>', methods=['PUT'])
def update_historial_formula(id):
    try:
        historial = HistorialFormula.query.get(id)
        if not historial:
            return jsonify({"error": "Historial de fórmula no encontrado"}), 404

        data = request.get_json()
        if 'cliente_id' in data:
            historial.cliente_id = data['cliente_id']
        if 'descripcion' in data:
            historial.descripcion = data['descripcion']
        if 'od_esfera' in data:
            historial.od_esfera = data['od_esfera']
        if 'od_cilindro' in data:
            historial.od_cilindro = data['od_cilindro']
        if 'od_eje' in data:
            historial.od_eje = data['od_eje']
        if 'oi_esfera' in data:
            historial.oi_esfera = data['oi_esfera']
        if 'oi_cilindro' in data:
            historial.oi_cilindro = data['oi_cilindro']
        if 'oi_eje' in data:
            historial.oi_eje = data['oi_eje']

        db.session.commit()
        return jsonify({"message": "Historial de fórmula actualizado", "historial": historial.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar historial de fórmula"}), 500

@main_bp.route('/historial-formula/<int:id>', methods=['DELETE'])
def delete_historial_formula(id):
    try:
        historial = HistorialFormula.query.get(id)
        if not historial:
            return jsonify({"error": "Historial de fórmula no encontrado"}), 404

        db.session.delete(historial)
        db.session.commit()
        return jsonify({"message": "Historial de fórmula eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar historial de fórmula"}), 500

# ===== TABLAS DEL SISTEMA - ABONO - COMPLETAR CRUD =====
@main_bp.route('/abono', methods=['GET'])
def get_abonos():
    try:
        abonos = Abono.query.all()
        return jsonify([abono.to_dict() for abono in abonos])
    except Exception as e:
        return jsonify({"error": "Error al obtener abonos"}), 500

@main_bp.route('/abono', methods=['POST'])
def create_abono():
    try:
        data = request.get_json()
        required_fields = ['venta_id', 'monto_abonado']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        abono = Abono(
            venta_id=data['venta_id'],
            monto_abonado=float(data['monto_abonado'])
        )
        db.session.add(abono)
        db.session.commit()
        return jsonify({"message": "Abono creado", "abono": abono.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear abono"}), 500

@main_bp.route('/abono/<int:id>', methods=['PUT'])
def update_abono(id):
    try:
        abono = Abono.query.get(id)
        if not abono:
            return jsonify({"error": "Abono no encontrado"}), 404

        data = request.get_json()
        if 'venta_id' in data:
            abono.venta_id = data['venta_id']
        if 'monto_abonado' in data:
            abono.monto_abonado = float(data['monto_abonado'])

        db.session.commit()
        return jsonify({"message": "Abono actualizado", "abono": abono.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar abono"}), 500

@main_bp.route('/abono/<int:id>', methods=['DELETE'])
def delete_abono(id):
    try:
        abono = Abono.query.get(id)
        if not abono:
            return jsonify({"error": "Abono no encontrado"}), 404

        db.session.delete(abono)
        db.session.commit()
        return jsonify({"message": "Abono eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar abono"}), 500

# ===== TABLAS DE PERMISOS - PERMISO - COMPLETAR CRUD =====
@main_bp.route('/permiso', methods=['GET'])
def get_permisos():
    try:
        permisos = Permiso.query.all()
        return jsonify([permiso.to_dict() for permiso in permisos])
    except Exception as e:
        return jsonify({"error": "Error al obtener permisos"}), 500

@main_bp.route('/permiso', methods=['POST'])
def create_permiso():
    try:
        data = request.get_json()
        if not data.get('nombre'):
            return jsonify({"error": "El nombre es requerido"}), 400

        permiso = Permiso(nombre=data['nombre'])
        db.session.add(permiso)
        db.session.commit()
        return jsonify({"message": "Permiso creado", "permiso": permiso.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear permiso"}), 500

@main_bp.route('/permiso/<int:id>', methods=['PUT'])
def update_permiso(id):
    try:
        permiso = Permiso.query.get(id)
        if not permiso:
            return jsonify({"error": "Permiso no encontrado"}), 404

        data = request.get_json()
        if 'nombre' in data:
            permiso.nombre = data['nombre']

        db.session.commit()
        return jsonify({"message": "Permiso actualizado", "permiso": permiso.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar permiso"}), 500

@main_bp.route('/permiso/<int:id>', methods=['DELETE'])
def delete_permiso(id):
    try:
        permiso = Permiso.query.get(id)
        if not permiso:
            return jsonify({"error": "Permiso no encontrado"}), 404

        db.session.delete(permiso)
        db.session.commit()
        return jsonify({"message": "Permiso eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar permiso"}), 500

# ===== TABLAS DE PERMISOS - PERMISO POR ROL - COMPLETAR CRUD =====
@main_bp.route('/permiso-rol', methods=['GET'])
def get_permisos_rol():
    try:
        permisos_rol = PermisoPorRol.query.all()
        return jsonify([permiso.to_dict() for permiso in permisos_rol])
    except Exception as e:
        return jsonify({"error": "Error al obtener permisos por rol"}), 500

@main_bp.route('/permiso-rol', methods=['POST'])
def create_permiso_rol():
    try:
        data = request.get_json()
        required_fields = ['rol_id', 'permiso_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"El campo {field} es requerido"}), 400

        permiso_rol = PermisoPorRol(
            rol_id=data['rol_id'],
            permiso_id=data['permiso_id']
        )
        db.session.add(permiso_rol)
        db.session.commit()
        return jsonify({"message": "Permiso por rol creado", "permiso_rol": permiso_rol.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al crear permiso por rol"}), 500

@main_bp.route('/permiso-rol/<int:id>', methods=['PUT'])
def update_permiso_rol(id):
    try:
        permiso_rol = PermisoPorRol.query.get(id)
        if not permiso_rol:
            return jsonify({"error": "Permiso por rol no encontrado"}), 404

        data = request.get_json()
        if 'rol_id' in data:
            permiso_rol.rol_id = data['rol_id']
        if 'permiso_id' in data:
            permiso_rol.permiso_id = data['permiso_id']

        db.session.commit()
        return jsonify({"message": "Permiso por rol actualizado", "permiso_rol": permiso_rol.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al actualizar permiso por rol"}), 500

@main_bp.route('/permiso-rol/<int:id>', methods=['DELETE'])
def delete_permiso_rol(id):
    try:
        permiso_rol = PermisoPorRol.query.get(id)
        if not permiso_rol:
            return jsonify({"error": "Permiso por rol no encontrado"}), 404

        db.session.delete(permiso_rol)
        db.session.commit()
        return jsonify({"message": "Permiso por rol eliminado correctamente"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar permiso por rol"}), 500

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
            'categorias': CategoriaProducto,
            'compras': Compra,
            'estado-cita': EstadoCita,
            'estado-venta': EstadoVenta,
            'roles': Rol,
            'detalle-venta': DetalleVenta,
            'detalle-compra': DetalleCompra,
            'horario': Horario,
            'historial-formula': HistorialFormula,
            'abono': Abono,
            'permiso': Permiso,
            'permiso-rol': PermisoPorRol
        }
        
        if tabla not in modelos:
            return jsonify({"error": "Tabla no encontrada"}), 404
            
        elemento = modelos[tabla].query.get(id)
        if not elemento:
            return jsonify({"error": f"{tabla[:-1]} no encontrado"}), 404
            
        return jsonify(elemento.to_dict())
    except Exception as e:
        return jsonify({"error": "Error al obtener elemento"}), 500

# ===== RUTAS DE RELACIONES =====
@main_bp.route('/ventas/<int:venta_id>/detalles', methods=['GET'])
def get_detalles_venta_especifica(venta_id):
    try:
        detalles = DetalleVenta.query.filter_by(venta_id=venta_id).all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de la venta"}), 500

@main_bp.route('/compras/<int:compra_id>/detalles', methods=['GET'])
def get_detalles_compra_especifica(compra_id):
    try:
        detalles = DetalleCompra.query.filter_by(compra_id=compra_id).all()
        return jsonify([detalle.to_dict() for detalle in detalles])
    except Exception as e:
        return jsonify({"error": "Error al obtener detalles de la compra"}), 500

@main_bp.route('/clientes/<int:cliente_id>/historial', methods=['GET'])
def get_historial_cliente(cliente_id):
    try:
        historiales = HistorialFormula.query.filter_by(cliente_id=cliente_id).all()
        return jsonify([historial.to_dict() for historial in historiales])
    except Exception as e:
        return jsonify({"error": "Error al obtener historial del cliente"}), 500

@main_bp.route('/empleados/<int:empleado_id>/horarios', methods=['GET'])
def get_horarios_empleado(empleado_id):
    try:
        horarios = Horario.query.filter_by(empleado_id=empleado_id).all()
        return jsonify([horario.to_dict() for horario in horarios])
    except Exception as e:
        return jsonify({"error": "Error al obtener horarios del empleado"}), 500

# ===== ACTUALIZAR LA RUTA DE ENDPOINTS PARA INCLUIR PUT Y DELETE =====
@main_bp.route('/endpoints', methods=['GET'])
def get_all_endpoints():
    return jsonify({
        "modulos_principales": {
            "clientes": "GET/POST /clientes, PUT/DELETE /clientes/{id}",
            "empleados": "GET/POST /empleados, PUT/DELETE /empleados/{id}",
            "proveedores": "GET/POST /proveedores, PUT/DELETE /proveedores/{id}",
            "ventas": "GET/POST /ventas, PUT/DELETE /ventas/{id}",
            "citas": "GET/POST /citas, PUT/DELETE /citas/{id}",
            "servicios": "GET/POST /servicios, PUT/DELETE /servicios/{id}",
            "usuarios": "GET/POST /usuarios, PUT/DELETE /usuarios/{id}",
            "productos": "GET/POST /productos, PUT/DELETE /productos/{id}",
            "marcas": "GET/POST /marcas, PUT/DELETE /marcas/{id}",
            "categorias": "GET/POST /categorias, PUT/DELETE /categorias/{id}",
            "compras": "GET/POST /compras, PUT/DELETE /compras/{id}",
            "roles": "GET/POST /roles, PUT/DELETE /roles/{id}"
        },
        "modulos_secundarios": {
            "detalle_venta": "GET/POST /detalle-venta, PUT/DELETE /detalle-venta/{id}",
            "detalle_compra": "GET/POST /detalle-compra, PUT/DELETE /detalle-compra/{id}",
            "estado_cita": "GET/POST /estado-cita, PUT/DELETE /estado-cita/{id}",
            "estado_venta": "GET/POST /estado-venta, PUT/DELETE /estado-venta/{id}",
            "horario": "GET/POST /horario, PUT/DELETE /horario/{id}",
            "historial_formula": "GET/POST /historial-formula, PUT/DELETE /historial-formula/{id}",
            "abono": "GET/POST /abono, PUT/DELETE /abono/{id}",
            "permiso": "GET/POST /permiso, PUT/DELETE /permiso/{id}",
            "permiso_rol": "GET/POST /permiso-rol, PUT/DELETE /permiso-rol/{id}"
        },
        "relaciones": {
            "detalles_venta": "GET /ventas/{id}/detalles",
            "detalles_compra": "GET /compras/{id}/detalles",
            "historial_cliente": "GET /clientes/{id}/historial",
            "horarios_empleado": "GET /empleados/{id}/horarios"
        },
        "utilidades": {
            "dashboard": "GET /dashboard/estadisticas",
            "elemento_especifico": "GET /{tabla}/{id}",
            "todos_endpoints": "GET /endpoints"
        }
    })