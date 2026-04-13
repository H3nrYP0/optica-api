import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── CORS ──────────────────────────────────────────────────
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

    # ── Base de datos ─────────────────────────────────────────
    from app.database import init_db, db
    init_db(app)

    # ── Autenticación (JWT + callbacks + blueprint /auth) ─────
    from app.auth import init_auth
    init_auth(app)

    # ── Blueprints de la app ──────────────────────────────────
    from app.routes import main_bp
    from app.auth.routes import auth_bp  
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')   

    # ── Middleware global de autenticación ────────────────────
    RUTAS_PUBLICAS = {
        'auth.login',
        'auth.register',
        'auth.verify_register',
        'auth.forgot_password',
        'auth.reset_password',
        'static',
    }

    @app.before_request
    def verificar_autenticacion():
        if request.method == 'OPTIONS':
            return None
        if request.endpoint in RUTAS_PUBLICAS:
            return None
        from flask_jwt_extended import verify_jwt_in_request
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({
                "success": False,
                "error": "Token requerido o inválido",
                "message": "Debes iniciar sesión para acceder a este recurso"
            }), 401
        return None

    # ── Verificar base de datos al arrancar ───────────────────
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