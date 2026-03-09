from flask import Flask
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── CORS ──
    CORS(app, resources={
        r"/*": {
            "origins": "*", # Permite todas las fuentes (ajustar para luego poner el dominio)
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "Cache-Control"]
        }
    })

    # Inicializar base de datos
    from app.database import init_db
    init_db(app)

    # Blueprint principal PRIMERO
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Auth DESPUÉS — así no lo intercepta la ruta genérica
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