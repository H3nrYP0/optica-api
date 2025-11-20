import os

class Config:
    # ✅ CORREGIDO: Usar PostgreSQL de Render
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    # Render usa postgres:// pero SQLAlchemy necesita postgresql://
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    # Usar PostgreSQL si DATABASE_URL existe, sino SQLite local
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///optica.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-temporal')