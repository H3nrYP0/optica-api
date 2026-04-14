import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config

def create_app():
    # ============================================================
    # 1. CREAR LA APLICACIÓN FLASK
    # ============================================================
    app = Flask(__name__)
    app.config.from_object(Config)  # Cargar configuración desde config.py

    # ============================================================
    # 2. CONFIGURACIÓN CORS (Permitir peticiones desde el frontend)
    # ============================================================
    CORS(app,
        origins=[
            "http://localhost:5173",  # Frontend local de React/Vite
            "http://localhost:3000",   # Frontend local alternativo
            os.getenv('FRONTEND_URL', '*')  # URL del frontend en producción
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Cache-Control"],
        supports_credentials=True  # Permitir cookies/autenticación
    )

    # ============================================================
    # 3. CONFIGURACIÓN DE BASE DE DATOS
    # ============================================================
    from app.database import init_db, db
    init_db(app)  # Inicializa la conexión a PostgreSQL

    # ============================================================
    # 4. CONFIGURACIÓN DE AUTENTICACIÓN (JWT)
    # ============================================================
    from app.auth import init_auth
    init_auth(app)  # Registra callbacks JWT y blueprint /auth

    # ============================================================
    # 5. REGISTRO DE BLUEPRINTS (Rutas de la API)
    # ============================================================
    from app.routes import main_bp          # Blueprint principal (todas las rutas CRUD)
    from app.auth.routes import auth_bp     # Blueprint de autenticación (/auth/*)
    
    app.register_blueprint(main_bp)                 # Rutas: /productos, /usuarios, etc.
    app.register_blueprint(auth_bp, url_prefix='/auth')  # Rutas: /auth/login, /auth/register

    # ============================================================
    # 6. MIDDLEWARE GLOBAL DE AUTENTICACIÓN
    # ============================================================
    # Lista de rutas que NO requieren token (públicas)
    RUTAS_PUBLICAS = {
        'auth.login',           # Iniciar sesión
        'auth.register',        # Registrarse
        'auth.verify_register', # Verificar código
        'auth.forgot_password', # Olvidé contraseña
        'auth.reset_password',  # Resetear contraseña
        'static',               # Archivos estáticos
    }

    @app.before_request
    def verificar_autenticacion():
        """
        🔒 MIDDLEWARE: Se ejecuta ANTES de cada petición.
        Verifica que el usuario tenga un token JWT válido.
        
        🔥 TEMPORALMENTE DESACTIVADO PARA PRUEBAS 🔥
        """
        
        # 🔥 DESACTIVADO: Comentar esta línea para volver a activar la seguridad
        return None  # <-- ESTO DESACTIVA TODA LA AUTENTICACIÓN
        
        # ========== CÓDIGO ORIGINAL (COMENTADO) ==========
        # Si la petición es OPTIONS (preflight de CORS), la permitimos sin autenticar
        # if request.method == 'OPTIONS':
        #     return None
        # 
        # # Si la ruta está en la lista de públicas, no verificar token
        # if request.endpoint in RUTAS_PUBLICAS:
        #     return None
        # 
        # # Verificar el token JWT
        # from flask_jwt_extended import verify_jwt_in_request
        # try:
        #     verify_jwt_in_request()
        # except Exception:
        #     # Si el token es inválido o no existe, devolver error 401
        #     return jsonify({
        #         "success": False,
        #         "error": "Token requerido o inválido",
        #         "message": "Debes iniciar sesión para acceder a este recurso"
        #     }), 401
        # 
        # return None
        # ========== FIN DEL CÓDIGO ORIGINAL ==========

    # ============================================================
    # 7. VERIFICAR BASE DE DATOS AL ARRANCAR
    # ============================================================
    with app.app_context():
        try:
            # Crear todas las tablas si no existen
            db.create_all()
            print("✅ Estructura de base de datos verificada.")
            
            # Probar conexión consultando un modelo
            from app.Models.models import Empleado
            count = Empleado.query.count()
            print(f"✅ Conexión exitosa. Empleados registrados: {count}")
        except Exception as e:
            print(f"❌ Error al verificar la base de datos: {e}")

    return app