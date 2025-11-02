"""
Fixtures e configurações compartilhadas para todos os testes
"""
import pytest
import sys
import os

# Adicionar o diretório pai (Backend) ao path para importar os módulos
# Este caminho deve apontar para onde estão app.py, models.py, etc.
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BACKEND_DIR)

from app import app as flask_app
from extensions import db
from models import User, Parametro, Leitura, Log
from test_config import TestConfig
from datetime import datetime

@pytest.fixture(scope='session')
def app():
    """Cria a aplicação Flask configurada para testes"""
    flask_app.config.from_object(TestConfig)
    
    with flask_app.app_context():
        # Criar todas as tabelas
        db.create_all()
        yield flask_app
        
        # Cleanup após todos os testes
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Cliente de teste para fazer requisições HTTP"""
    return app.test_client()

@pytest.fixture(scope='function')
def db_session(app):
    """
    Sessão de banco de dados limpa para cada teste.
    Faz rollback após cada teste.
    """
    with app.app_context():
        # Limpar todos os dados antes de cada teste
        db.session.query(Log).delete()
        db.session.query(Leitura).delete()
        db.session.query(Parametro).delete()
        db.session.query(User).delete()
        db.session.commit()
        
        yield db.session
        
        # Rollback após cada teste
        db.session.rollback()

@pytest.fixture
def usuario_comum(db_session):
    """Cria um usuário comum para testes"""
    user = User(
        username='usuario_teste',
        email='usuario@teste.com',
        is_admin=False
    )
    user.set_password('senha123')
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def usuario_admin(db_session):
    """Cria um usuário administrador para testes"""
    admin = User(
        username='admin_teste',
        email='admin@teste.com',
        is_admin=True
    )
    admin.set_password('admin123')
    db_session.add(admin)
    db_session.commit()
    return admin

@pytest.fixture
def token_usuario_comum(app, usuario_comum):
    """Gera token JWT para usuário comum"""
    return usuario_comum.generate_auth_token(
        app.config['JWT_SECRET_KEY'],
        expires_in=3600
    )

@pytest.fixture
def token_usuario_admin(app, usuario_admin):
    """Gera token JWT para usuário administrador"""
    return usuario_admin.generate_auth_token(
        app.config['JWT_SECRET_KEY'],
        expires_in=3600
    )

@pytest.fixture
def auth_headers_comum(token_usuario_comum):
    """Headers HTTP com autenticação de usuário comum"""
    return {
        'Authorization': f'Bearer {token_usuario_comum}',
        'Content-Type': 'application/json'
    }

@pytest.fixture
def auth_headers_admin(token_usuario_admin):
    """Headers HTTP com autenticação de administrador"""
    return {
        'Authorization': f'Bearer {token_usuario_admin}',
        'Content-Type': 'application/json'
    }

@pytest.fixture
def parametro_exemplo(db_session, usuario_admin):
    """Cria um parâmetro de exemplo no banco"""
    parametro = Parametro(
        empresa='Empresa Teste',
        lote='LOTE001',
        temp_ideal=37.5,
        umid_ideal=60.0,
        pressao_ideal=1013.25,
        lumens=500.0,
        id_sala=1,
        estagio_ovo='Incubação'
    )
    db_session.add(parametro)
    db_session.commit()
    return parametro

@pytest.fixture
def leitura_exemplo(db_session):
    """Cria uma leitura de exemplo no banco"""
    leitura = Leitura(
        umidade=58.5,
        temperatura=37.2,
        pressao=1012.5,
        lote='LOTE001',
        data_inicial=datetime(2024, 1, 1, 10, 0, 0),
        data_final=datetime(2024, 1, 21, 10, 0, 0)
    )
    db_session.add(leitura)
    db_session.commit()
    return leitura

@pytest.fixture
def multiplos_parametros(db_session):
    """Cria múltiplos parâmetros para testes de listagem/filtro"""
    parametros = [
        Parametro(
            empresa='Empresa A',
            lote='LOTE_A1',
            temp_ideal=37.5,
            umid_ideal=60.0,
            estagio_ovo='Inicial'
        ),
        Parametro(
            empresa='Empresa A',
            lote='LOTE_A2',
            temp_ideal=37.8,
            umid_ideal=62.0,
            estagio_ovo='Médio'
        ),
        Parametro(
            empresa='Empresa B',
            lote='LOTE_B1',
            temp_ideal=37.3,
            umid_ideal=58.0,
            estagio_ovo='Final'
        )
    ]
    
    for param in parametros:
        db_session.add(param)
    
    db_session.commit()
    return parametros

@pytest.fixture
def multiplas_leituras(db_session):
    """Cria múltiplas leituras para testes"""
    leituras = [
        Leitura(
            umidade=58.5,
            temperatura=37.2,
            pressao=1012.5,
            lote='LOTE001',
            data_inicial=datetime(2024, 1, 1),
            data_final=datetime(2024, 1, 21)
        ),
        Leitura(
            umidade=60.0,
            temperatura=37.5,
            pressao=1013.0,
            lote='LOTE001',
            data_inicial=datetime(2024, 2, 1),
            data_final=datetime(2024, 2, 21)
        ),
        Leitura(
            umidade=59.2,
            temperatura=37.4,
            pressao=1012.8,
            lote='LOTE002',
            data_inicial=datetime(2024, 3, 1),
            data_final=datetime(2024, 3, 21)
        )
    ]
    
    for leitura in leituras:
        db_session.add(leitura)
    
    db_session.commit()
    return leituras
