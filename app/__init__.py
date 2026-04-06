import os
from flask import Flask
from flask_cors import CORS
from flask_mail import Mail
from config import Config

# Instancias globales
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 1. Configuración de Mail
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv('MAIL_USERNAME', 'eyessetting@gmail.com'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD', 'anjw fbsu lsgp zrgp'),
        MAIL_DEFAULT_SENDER=os.getenv('MAIL_USERNAME', 'eyessetting@gmail.com')
    )
    mail.init_app(app)

    # 2. Configuración de CORS
    # Permitimos localhost para desarrollo y una variable de entorno para producción
    CORS(app, 
        origins=[
            "http://localhost:5173", 
            "http://localhost:3000",
            os.getenv('FRONTEND_URL', '*') # Permite configurar la URL de Render después
        ],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Cache-Control"],
        supports_credentials=True
    )

    # 3. Inicializar Base de Datos
    from app.database import init_db, db
    init_db(app)

    # 4. Registro de Blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # 5. Inicializar Autenticación
    # NOTA: Si esto lanza "Token requerido", revisar app/auth/ para ver las excepciones
    from app.auth import init_auth
    init_auth(app)

    # 6. Verificación de Contexto y Tablas
    with app.app_context():
        try:
            db.create_all()
            print("✅ Estructura de PostgreSQL verificada.")
            
            # Importación dinámica para evitar conflictos de nombres
            # IMPORTANTE: Asegúrate que la carpeta sea 'models' en minúsculas
            from app.Models.models import Empleado
            count = Empleado.query.count()
            print(f"✅ Conexión exitosa. Empleados registrados: {count}")
            
        except Exception as e:
            print(f"❌ Error al verificar la base de datos: {e}")
      
    return app