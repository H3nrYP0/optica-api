from flask import Flask
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    
    # Configuración desde config.py
    app.config.from_object(Config)
    
    # CORS
    CORS(app)
    
    # Inicializar base de datos
    from app.database import init_db
    init_db(app)
    
    # Registrar blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Crear tablas después de inicializar
    with app.app_context():
        from app.database import db
        try:
            db.create_all()
            print("✅ Tablas creadas/verificadas en PostgreSQL")
            
            # Verificar conexión contando empleados
            from app.models import Empleado
            count = Empleado.query.count()
            print(f"✅ Conexión exitosa. Empleados en BD: {count}")
            
        except Exception as e:
            print(f"❌ Error creando tablas: {e}")
    
    return app