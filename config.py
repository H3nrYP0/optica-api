import os

class Config:
    # Obtener DATABASE_URL de environment
    database_url = os.environ.get('DATABASE_URL')
    
    # Render usa postgres:// pero SQLAlchemy necesita postgresql://
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = database_url or 'sqlite:///optica_dev.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-secreta-temporal')