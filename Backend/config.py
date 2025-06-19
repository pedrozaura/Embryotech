import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class Config:
    # Configurações do PostgreSQL
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?connect_timeout=10"


    # Configurações de segurança
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-secreta-muito-segura')
    JWT_SECRET_KEY = os.environ['JWT_SECRET_KEY']  # Isso levantará erro se não estiver definido
   # JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'uma-chave-secreta-muito-segura')
    
    # Configurações do Flask
    DEBUG = os.getenv('DEBUG', 'False') == 'True'