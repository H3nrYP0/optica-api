import os

class Config:
    # Usar SQLite temporalmente - 100% funcional
    SQLALCHEMY_DATABASE_URI = 'sqlite:///optica.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-temporal')