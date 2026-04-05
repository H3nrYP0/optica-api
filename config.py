import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base de datos
    DATABASE_URL = os.environ.get('DATABASE_URL', '')

    # Render entrega la URL con 'postgres://', SQLAlchemy requiere 'postgresql://'
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    # Usar psycopg2 como driver — más estable que psycopg v3 en Render con SSL
    if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)

    # Render requiere SSL explícito para conectarse a PostgreSQL
    if DATABASE_URL and 'sslmode' not in DATABASE_URL:
        DATABASE_URL += '?sslmode=require'

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///optica.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pool de conexiones — evita errores cuando Render duerme la API
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,  # verifica que la conexión siga activa antes de usarla
        "pool_recycle": 300,    # renueva conexiones cada 5 min antes de que Render las cierre
        "pool_timeout": 20,     # tiempo máximo esperando una conexión disponible
        "max_overflow": 0       # no permite conexiones extra fuera del pool
    }

    # Claves de seguridad
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    if not SECRET_KEY:
        raise ValueError("❌ SECRET_KEY no está definida en el .env")
    if not JWT_SECRET_KEY:
        raise ValueError("❌ JWT_SECRET_KEY no está definida en el .env")

    # JWT configuración
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)