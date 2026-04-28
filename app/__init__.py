import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ============================================================
    # 1. CONFIGURACIÓN CORS
    # ============================================================
    CORS(app,
        origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            "http://localhost:5500",
            os.getenv('FRONTEND_URL', '*')
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Cache-Control"],
        supports_credentials=True
    )

    # ============================================================
    # 2. BASE DE DATOS
    # ============================================================
    from app.database import init_db, db
    init_db(app)

    # ============================================================
    # 3. AUTENTICACIÓN (JWT)
    # ============================================================
    from app.auth import init_auth
    init_auth(app)

    # ============================================================
    # 4. REGISTRO DE BLUEPRINTS
    # ============================================================
    from app.routes import main_bp
    from app.auth.routes import auth_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # ============================================================
    # 5. MIDDLEWARE GLOBAL DE AUTENTICACIÓN
    # ============================================================
    @app.before_request
    def verificar_autenticacion():
        # Permitir OPTIONS (preflight de CORS)
        if request.method == 'OPTIONS':
            return None

        # ========================================================
        # RUTAS PÚBLICAS - accesibles SIN token
        # ========================================================
        RUTAS_PUBLICAS = {
            # Auth
            'auth.login',
            'auth.register',
            'auth.verify_register',
            'auth.forgot_password',
            'auth.reset_password',

            # Clientes desde landing (público)
            'main.get_clientes_publico',
            'main.create_cliente_publico',
            'main.update_cliente_publico',
            'main.delete_cliente_publico',

            # Catálogo landing
            'main.get_productos',
            'main.get_categorias',
            'main.get_marcas',
            'main.get_servicios',

            # Imágenes y multimedia públicas
            'main.get_imagenes',
            'main.get_imagen',
            'main.get_imagenes_por_producto',
            'main.obtener_comprobante_pedido',

            # Agendamiento desde landing
            'main.get_estados_cita',
            'main.verificar_disponibilidad',
            'main.verificar_disponibilidad_multiple',

            # Utilidades
            'static',
            'main.home',
            'main.get_all_endpoints',
            'main.get_elemento',
        }

        # Si es ruta pública, permitir acceso
        if not request.endpoint or request.endpoint in RUTAS_PUBLICAS:
            return None

        # ========================================================
        # RUTAS PROTEGIDAS - requieren JWT
        # ========================================================
        from flask_jwt_extended import verify_jwt_in_request
        
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({
                "success": False,
                "error": "Token requerido",
                "message": "Debes iniciar sesión para acceder a este recurso"
            }), 401

        # ========================================================
        # VERIFICACIÓN ADICIONAL: Clientes NO pueden acceder a rutas admin
        # ========================================================
        from flask_jwt_extended import get_jwt
        
        claims = get_jwt()
        es_cliente = claims.get('es_cliente', False)
        endpoint = request.endpoint or ''
        
        # Rutas que NO deben ser accesibles por clientes
        RUTAS_ADMIN = [
            'admin.crear_producto', 'admin.actualizar_producto', 'admin.eliminar_producto',
            'admin.get_usuarios', 'admin.create_usuario', 'admin.update_usuario', 'admin.delete_usuario',
            'admin.get_clientes', 'admin.create_cliente', 'admin.update_cliente', 'admin.delete_cliente',
            'admin.get_historial_cliente', 'admin.create_historial_formula', 'admin.delete_historial_formula',
            'empleados.get_empleados', 'empleados.create_empleado', 'empleados.update_empleado', 'empleados.delete_empleado',
            'main.get_empleados_sin_usuario', 'main.get_empleados_con_usuario',
            'main.get_horarios', 'main.create_horario', 'main.update_horario', 'main.delete_horario',
            'main.get_novedades', 'main.create_novedad', 'main.update_novedad', 'main.delete_novedad',
            'main.get_proveedores', 'main.create_proveedor', 'main.update_proveedor', 'main.delete_proveedor',
            'main.get_compras', 'main.create_compra', 'main.update_compra', 'main.delete_compra',
            'main.get_roles', 'main.create_rol', 'main.update_rol', 'main.delete_rol',
            'main.get_permisos', 'main.get_permisos_por_rol', 'main.asignar_permiso_rol', 'main.remover_permiso_rol',
        ]
        
        # Si es cliente y trata de acceder a ruta admin, denegar
        if es_cliente and any(ruta in endpoint for ruta in RUTAS_ADMIN):
            return jsonify({
                "success": False,
                "error": "Acceso denegado",
                "message": "Notienes permiso para acceder a este recurso"
            }), 403

    # ============================================================
    # 6. MANEJADORES DE ERRORES GLOBALES
    # ============================================================
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": "Recurso no encontrado",
            "message": "La ruta solicitada no existe"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": "Método no permitido",
            "message": "El método HTTP no está permitido para esta ruta"
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": "Error interno del servidor",
            "message": "Ocurrió un error inesperado. Intenta de nuevo más tarde"
        }), 500

    # ============================================================
    # 7. VERIFICACIÓN DE BASE DE DATOS AL INICIAR
    # ============================================================
    with app.app_context():
        try:
            db.create_all()
            print("✅ Base de datos conectada y estructura verificada")
            
            # Crear roles por defecto si no existen
            from app.Models.models import Rol, Permiso, PermisoPorRol
            
            # Roles del sistema
            roles_default = [
                {'nombre': 'Admin', 'descripcion': 'Administrador del sistema - Acceso total'},
                {'nombre': 'Optometra', 'descripcion': 'Optómetra - Gestión de citas y pacientes'},
                {'nombre': 'Asesor', 'descripcion': 'Asesor de ventas - Gestión de productos y ventas'},
                {'nombre': 'Cliente', 'descripcion': 'Cliente registrado desde landing page'},
            ]
            
            for rol_data in roles_default:
                if not Rol.query.filter_by(nombre=rol_data['nombre']).first():
                    rol = Rol(
                        nombre=rol_data['nombre'],
                        descripcion=rol_data['descripcion'],
                        estado=True
                    )
                    db.session.add(rol)
            
            # Permisos del sistema
            permisos_default = [
                'dashboard', 'citas', 'servicios', 'clientes', 'empleados',
                'pedidos', 'productos', 'proveedores', 'compras', 'ventas',
                'usuarios', 'roles', 'configuracion'
            ]
            
            for permiso_nombre in permisos_default:
                if not Permiso.query.filter_by(nombre=permiso_nombre).first():
                    permiso = Permiso(nombre=permiso_nombre)
                    db.session.add(permiso)
            
            db.session.commit()
            print("✅ Roles y permisos verificados")
            
        except Exception as e:
            print(f"⚠️ Error al conectar con la base de datos: {e}")

    return app