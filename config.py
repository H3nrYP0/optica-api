import os

class Config:
    # Obtener URL de Render
    DATABASE_URL = os.environ.get('DATABASE_URL', '')

    # Render da 'postgres://', hay que corregirlo primero
    if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

    # Convertir driver a psycopg (psycopg3)
    if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)

    # Si no hay DB remota, usar SQLite local
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///optica.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-temporal')
