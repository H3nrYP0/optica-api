from flask import Flask, jsonify
from flask_cors import CORS
from flask_mail import Mail
from config import Config

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Mail (usa Config)
    mail.init_app(app)

    # CORS
    CORS(app,
         origins=[
             "http://localhost:5173",
             "http://localhost:3000",
            #"" agrega dominio real aquí
         ],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization", "Cache-Control"],
         supports_credentials=True)

    from app.database import init_db
    init_db(app)

    # Blueprints
    from app.routes.marca_routes      import marca_bp
    from app.routes.categoria_routes  import categoria_bp
    from app.routes.producto_routes   import producto_bp
    from app.routes.cliente_routes    import cliente_bp
    from app.routes.empleado_routes   import empleado_bp
    from app.routes.proveedor_routes  import proveedor_bp
    from app.routes.compra_routes     import compra_bp
    from app.routes.cita_routes       import cita_bp
    from app.routes.servicio_routes   import servicio_bp
    from app.routes.pedido_routes     import pedido_bp
    from app.routes.venta_routes      import venta_bp
    from app.routes.usuario_routes    import usuario_bp
    from app.routes.rol_routes        import rol_bp
    from app.routes.multimedia_routes import multimedia_bp
    from app.routes.horario_routes    import horario_bp
    from app.routes.campana_routes    import campana_bp
    from app.routes.historial_routes  import historial_bp
    from app.routes.sistema_routes    import sistema_bp

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
    app.register_blueprint(sistema_bp)

    @app.route('/')
    def index():
        return jsonify({
            "message": "API Óptica Online",
            "status": "Ready",
            "version": "3.1"
        }), 200

    from app.auth import init_auth
    init_auth(app)

    with app.app_context():
        from app.database import db
        import app.models
        try:
            db.create_all()
            print("✅ Estructura de base de datos verificada")
        except Exception as e:
            print(f"❌ Error en base de datos: {e}")

    return app