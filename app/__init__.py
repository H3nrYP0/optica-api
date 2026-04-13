import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Configuración de CORS
    CORS(app, 
        origins=[
            "http://localhost:5173", 
            "http://localhost:3000",
            os.getenv('FRONTEND_URL', '*')
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Cache-Control"],
        supports_credentials=True
    )

    # 2. Inicializar JWT 
    jwt = JWTManager(app)

    # 3. Inicializar Base de Datos
    from app.database import init_db, db
    init_db(app)

    # 4. Registro de Blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # 5. Inicializar Autenticación (JWT callbacks + blueprint /auth)
    from app.auth import init_auth
    init_auth(app)

    # 6. Verificación de Contexto y Tablas
    with app.app_context():
        try:
            db.create_all()
            print("✅ Estructura de PostgreSQL verificada.")
            
            from app.Models.models import Empleado
            count = Empleado.query.count()
            print(f"✅ Conexión exitosa. Empleados registrados: {count}")
            
        except Exception as e:
            print(f"❌ Error al verificar la base de datos: {e}")
      
    return app