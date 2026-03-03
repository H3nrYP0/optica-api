import os
from datetime import timedelta
from dotenv import load_dotenv

# ── Cargar .env aquí mismo, antes de leer las variables ──
load_dotenv()

class Config:
    # ── Base de datos ──
    DATABASE_URL = os.environ.get('DATABASE_URL', '')

    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///optica.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Claves de seguridad ──
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    if not SECRET_KEY:
        raise ValueError("❌ SECRET_KEY no está definida en el .env")
    if not JWT_SECRET_KEY:
        raise ValueError("❌ JWT_SECRET_KEY no está definida en el .env")

    # ── JWT ──
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)