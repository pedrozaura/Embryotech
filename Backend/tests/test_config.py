"""
Configuração específica para ambiente de testes
"""
import os
from config import Config

class TestConfig(Config):
    """Configuração para ambiente de testes"""
    
    # Usar banco de dados em memória SQLite para testes
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Ou usar um banco PostgreSQL de teste separado
    # SQLALCHEMY_DATABASE_URI = 'postgresql://testuser:testpass@localhost:5432/embryotech_test'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Desabilitar proteção CSRF em testes
    WTF_CSRF_ENABLED = False
    TESTING = True
    
    # Chaves secretas para testes (não usar em produção)
    SECRET_KEY = 'test-secret-key-123'
    JWT_SECRET_KEY = 'test-jwt-secret-key-456'
    
    # Debug desabilitado em testes
    DEBUG = False
    
    # Configurações de logging para testes
    LOG_TO_STDOUT = False
