import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    # Configurações do PostgreSQL
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'embryotech')
    
    # Validação de configurações críticas
    if not DB_PASSWORD:
        raise ValueError("DB_PASSWORD não foi definida nas variáveis de ambiente")
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?connect_timeout=10"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configurações de segurança
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-secreta-muito-segura')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY não foi definida nas variáveis de ambiente")
    
    # Configurações do Flask
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'