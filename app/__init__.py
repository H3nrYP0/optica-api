import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request
from config import Config
from app.auth.decorators import get_usuario_actual

# Instancias globales
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS
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

    # JWT
    jwt = JWTManager(app)

    # ============================================================
    # MIDDLEWARE GLOBAL - Se ejecuta antes de cada request
    # ============================================================
    @app.before_request
    def verificar_autenticacion():
        # Rutas públicas (no requieren token)
        rutas_publicas = [
            'auth.login', 
            'auth.register', 
            'auth.verify_register',
            'auth.forgot_password', 
            'auth.reset_password',
            'static'  # archivos estáticos
        ]
        
        # Si es ruta pública, dejar pasar
        if request.endpoint in rutas_publicas:
            return None
        
        # Verificar JWT
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({"success": False, "error": "Token requerido o inválido"}), 401
        

    # ============================================================
    # Inicializar Base de Datos
    # ============================================================
    from app.database import init_db, db
    init_db(app)

    # ============================================================
    # Registrar Blueprints
    # ============================================================
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # ============================================================
    # Inicializar Autenticación
    # ============================================================
    from app.auth import init_auth
    init_auth(app)

    # ============================================================
    # Verificar Base de Datos
    # ============================================================
    with app.app_context():
        try:
            db.create_all()
            print("✅ Estructura de base de datos verificada.")
            
            from app.Models.models import Empleado
            count = Empleado.query.count()
            print(f"✅ Conexión exitosa. Empleados registrados: {count}")
            
        except Exception as e:
            print(f"❌ Error al verificar la base de datos: {e}")
    
    return app