import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    _url = os.environ.get('DATABASE_URL', '').strip()

    if _url.startswith('postgres://'):
        _url = _url.replace('postgres://', 'postgresql://', 1)
    if _url.startswith('postgresql://'):
        _url = _url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    if _url.startswith('postgresql+psycopg2://') and 'sslmode' not in _url:
        _url += '?sslmode=require'

    # Si no hay URL de producción, construir ruta absoluta para SQLite
    if not _url:
        _sqlite_path = os.path.join(BASE_DIR, 'instance', 'optica.db')
        _url = f'sqlite:///{_sqlite_path}'

    SQLALCHEMY_DATABASE_URI = _url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    if 'postgresql' in _url:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
            "pool_timeout": 20,
            "max_overflow": 0,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}

    _env = os.environ.get('FLASK_ENV', 'production')

    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')

    if _env == 'production':
        if not SECRET_KEY:
            raise ValueError("SECRET_KEY no está definida")
        if not JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY no está definida")
    else:
        SECRET_KEY = SECRET_KEY or 'dev-secret-inseguro'
        JWT_SECRET_KEY = JWT_SECRET_KEY or 'dev-jwt-inseguro'

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)