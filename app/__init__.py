from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from config import Config

mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Mail ──
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'eyessetting@gmail.com'
    app.config['MAIL_PASSWORD'] = 'anjw fbsu lsgp zrgp'
    app.config['MAIL_DEFAULT_SENDER'] = 'eyessetting@gmail.com'

    mail.init_app(app)

    # ── CORS ──
    CORS(app, 
        origins=[
            "http://localhost:5173",
            "http://localhost:3000",
            #"" ← agrega tu dominio real cuando subas
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Cache-Control"],
        supports_credentials=True
    )   

    # Inicializar base de datos
    from app.database import init_db
    init_db(app)

    # Blueprint principal PRIMERO
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Auth DESPUÉS
    from app.auth import init_auth
    init_auth(app)

    with app.app_context():
        from app.database import db
        try:
            db.create_all()
            print("✅ Tablas creadas/verificadas en PostgreSQL")
            from app.models import Empleado
            count = Empleado.query.count()
            print(f"✅ Conexión exitosa. Empleados en BD: {count}")
        except Exception as e:
            print(f"❌ Error creando tablas: {e}")

    return app