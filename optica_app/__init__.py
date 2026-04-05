from flask import Flask, jsonify
from flask_cors import CORS
from flask_mail import Mail
from config import Config

mail = Mail()

def create_app():
    optica_app = Flask(__name__)
    optica_app.config.from_object(Config)

    # Mail (usa Config)
    mail.init_app(optica_app)

    # CORS
    CORS(optica_app,
         origins=[
             "http://localhost:5173",
             "http://localhost:3000",
            #"" agrega dominio real aquí
         ],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "Cache-Control"],
         supports_credentials=True)

    from optica_app.database import init_db
    init_db(optica_app)

    # Blueprints
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

    optica_app.register_blueprint(marca_bp,      url_prefix='/marcas')
    optica_app.register_blueprint(categoria_bp,  url_prefix='/categorias')
    optica_app.register_blueprint(producto_bp,   url_prefix='/productos')
    optica_app.register_blueprint(cliente_bp,    url_prefix='/clientes')
    optica_app.register_blueprint(empleado_bp,   url_prefix='/empleados')
    optica_app.register_blueprint(proveedor_bp,  url_prefix='/proveedores')
    optica_app.register_blueprint(compra_bp,     url_prefix='/compras')
    optica_app.register_blueprint(cita_bp,       url_prefix='/citas')
    optica_app.register_blueprint(servicio_bp,   url_prefix='/servicios')
    optica_app.register_blueprint(pedido_bp,     url_prefix='/pedidos')
    optica_app.register_blueprint(venta_bp,      url_prefix='/ventas')
    optica_app.register_blueprint(usuario_bp,    url_prefix='/usuarios')
    optica_app.register_blueprint(rol_bp,        url_prefix='/roles')
    optica_app.register_blueprint(multimedia_bp, url_prefix='/multimedia')
    optica_app.register_blueprint(horario_bp,    url_prefix='/horario')
    optica_app.register_blueprint(campana_bp,    url_prefix='/campanas-salud')
    optica_app.register_blueprint(historial_bp,  url_prefix='/historial-formula')
    optica_app.register_blueprint(sistema_bp)

    @optica_app.route('/')
    def index():
        return jsonify({
            "message": "API Óptica Online",
            "status": "Ready",
            "version": "3.1"
        }), 200

    from optica_app.auth import init_auth
    init_auth(optica_app)

    with optica_app.app_context():
        from optica_app.database import db
        import optica_app.models
        try:
            db.create_all()
            print("✅ Estructura de base de datos verificada")
        except Exception as e:
            print(f"❌ Error en base de datos: {e}")

    return optica_app