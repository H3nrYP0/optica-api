from flask import Flask, jsonify
from flask_cors import CORS
from flask_mail import Mail
from config import Config

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Configuración de Mail ──
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME='eyessetting@gmail.com',
        MAIL_PASSWORD='anjw fbsu lsgp zrgp',
        MAIL_DEFAULT_SENDER='eyessetting@gmail.com'
    )
    mail.init_app(app)

    # ── Configuración de CORS (Abierto para desarrollo) ──
    CORS(app,
         origins=["http://localhost:5173", "http://localhost:3000"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "Cache-Control"],
         supports_credentials=True)

    # ── Inicializar Base de Datos ──
    from optica_app.database import init_db # Asegúrate de que la ruta coincida (app o optica_app)
    init_db(app)

    # ── Importación y Registro de Blueprints (Rutas) ──
    # Registro individual para mantener el control total
    from optica_app.routes.marca_routes      import marca_bp
    from optica_app.routes.categoria_routes  import categoria_bp
    from optica_app.routes.producto_routes   import producto_bp
    from optica_app.routes.cliente_routes    import cliente_bp
    from optica_app.routes.empleado_routes   import empleado_bp
    from optica_app.routes.proveedor_routes  import proveedor_bp
    from optica_app.routes.compra_routes     import compra_bp
    from optica_app.routes.cita_routes       import cita_bp
    from optica_app.routes.servicio_routes   import servicio_bp
    from optica_app.routes.pedido_routes     import pedido_bp
    from optica_app.routes.venta_routes      import venta_bp
    from optica_app.routes.usuario_routes    import usuario_bp
    from optica_app.routes.rol_routes        import rol_bp
    from optica_app.routes.multimedia_routes import multimedia_bp
    from optica_app.routes.horario_routes    import horario_bp
    from optica_app.routes.campana_routes    import campana_bp
    from optica_app.routes.historial_routes  import historial_bp
    from optica_app.routes.sistema_routes    import sistema_bp

    # ── Registro de Blueprints con sus prefijos ──
    app.register_blueprint(marca_bp,      url_prefix='/marcas')
    app.register_blueprint(categoria_bp,  url_prefix='/categorias')
    app.register_blueprint(producto_bp,   url_prefix='/productos')
    app.register_blueprint(cliente_bp,    url_prefix='/clientes')
    app.register_blueprint(empleado_bp,   url_prefix='/empleados')
    app.register_blueprint(proveedor_bp,  url_prefix='/proveedores')
    app.register_blueprint(compra_bp,     url_prefix='/compras')
    app.register_blueprint(cita_bp,       url_prefix='/citas')
    app.register_blueprint(servicio_bp,   url_prefix='/servicios')
    app.register_blueprint(pedido_bp,     url_prefix='/pedidos')
    app.register_blueprint(venta_bp,      url_prefix='/ventas')
    app.register_blueprint(usuario_bp,    url_prefix='/usuarios')
    app.register_blueprint(rol_bp,        url_prefix='/roles')
    app.register_blueprint(multimedia_bp, url_prefix='/multimedia')
    app.register_blueprint(horario_bp,    url_prefix='/horario')
    app.register_blueprint(campana_bp,    url_prefix='/campanas-salud')
    app.register_blueprint(historial_bp,  url_prefix='/historial-formula')
    app.register_blueprint(sistema_bp)    # El sistema no suele llevar prefijo
    # Ruta de bienvenida
    @app.route('/')
    def index():
        return jsonify({"message": "API Óptica - Modo Libre de Token", "status": "Ready"}), 200

    # ❌ COMENTADO: Bloqueo de seguridad para volver a la versión anterior
    # from optica_app.auth import init_auth
    # init_auth(app)

    # ── Creación de Tablas ──
    with app.app_context():
        from optica_app.database import db
        import optica_app.models 
        try:
            db.create_all()
            print("✅ Estructura verificada")
        except Exception as e:
            print(f"❌ Error: {e}")

    return app