"""
Testes unitários para os modelos da aplicação
"""
import pytest
from datetime import datetime, timedelta
from models import User, Parametro, Leitura, Log
from extensions import db


class TestUserModel:
    """Testes para o modelo User"""
    
    def test_criar_usuario(self, db_session):
        """Testa criação de usuário"""
        user = User(
            username='teste_user',
            email='teste@email.com',
            is_admin=False
        )
        user.set_password('senha123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'teste_user'
        assert user.email == 'teste@email.com'
        assert user.is_admin is False
        assert user.password_hash is not None
    
    def test_set_password(self, db_session):
        """Testa se a senha é hasheada corretamente"""
        user = User(username='user', email='user@email.com')
        senha_original = 'minhasenha123'
        user.set_password(senha_original)
        
        # Hash não deve ser igual à senha original
        assert user.password_hash != senha_original
        # Deve ser uma string não vazia
        assert len(user.password_hash) > 0
    
    def test_check_password_correto(self, db_session):
        """Testa verificação de senha correta"""
        user = User(username='user', email='user@email.com')
        senha = 'minhasenha123'
        user.set_password(senha)
        
        assert user.check_password(senha) is True
    
    def test_check_password_incorreto(self, db_session):
        """Testa verificação de senha incorreta"""
        user = User(username='user', email='user@email.com')
        user.set_password('senhaCorreta')
        
        assert user.check_password('senhaErrada') is False
    
    def test_generate_auth_token(self, app, usuario_comum):
        """Testa geração de token JWT"""
        token = usuario_comum.generate_auth_token(
            app.config['JWT_SECRET_KEY'],
            expires_in=3600
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_auth_token_valido(self, app, usuario_comum):
        """Testa verificação de token válido"""
        token = usuario_comum.generate_auth_token(
            app.config['JWT_SECRET_KEY'],
            expires_in=3600
        )
        
        user_verificado = User.verify_auth_token(
            token,
            app.config['JWT_SECRET_KEY']
        )
        
        assert user_verificado is not None
        assert user_verificado.id == usuario_comum.id
        assert user_verificado.username == usuario_comum.username
    
    def test_verify_auth_token_invalido(self, app):
        """Testa verificação de token inválido"""
        token_invalido = 'token.invalido.123'
        
        user = User.verify_auth_token(
            token_invalido,
            app.config['JWT_SECRET_KEY']
        )
        
        assert user is None
    
    def test_verify_auth_token_expirado(self, app, usuario_comum):
        """Testa verificação de token expirado"""
        # Gera token que expira em -1 segundo (já expirado)
        token = usuario_comum.generate_auth_token(
            app.config['JWT_SECRET_KEY'],
            expires_in=-1
        )
        
        user = User.verify_auth_token(
            token,
            app.config['JWT_SECRET_KEY']
        )
        
        assert user is None
    
    def test_usuario_admin(self, usuario_admin):
        """Testa se o campo is_admin funciona corretamente"""
        assert usuario_admin.is_admin is True
    
    def test_usuario_comum_nao_admin(self, usuario_comum):
        """Testa se usuário comum não é admin"""
        assert usuario_comum.is_admin is False


class TestParametroModel:
    """Testes para o modelo Parametro"""
    
    def test_criar_parametro(self, db_session):
        """Testa criação de parâmetro"""
        parametro = Parametro(
            empresa='Empresa Teste',
            lote='LOTE123',
            temp_ideal=37.5,
            umid_ideal=60.0,
            pressao_ideal=1013.25,
            lumens=500.0,
            id_sala=1,
            estagio_ovo='Incubação'
        )
        
        db_session.add(parametro)
        db_session.commit()
        
        assert parametro.id is not None
        assert parametro.empresa == 'Empresa Teste'
        assert parametro.lote == 'LOTE123'
        assert parametro.temp_ideal == 37.5
        assert parametro.umid_ideal == 60.0
        assert parametro.data_criacao is not None
    
    def test_parametro_campos_obrigatorios(self, db_session):
        """Testa criação de parâmetro apenas com campos obrigatórios"""
        parametro = Parametro(
            empresa='Empresa',
            lote='LOTE',
            temp_ideal=37.0,
            umid_ideal=60.0
        )
        
        db_session.add(parametro)
        db_session.commit()
        
        assert parametro.id is not None
        assert parametro.pressao_ideal is None
        assert parametro.lumens is None
    
    def test_parametro_to_dict(self, parametro_exemplo):
        """Testa conversão de parâmetro para dicionário"""
        dict_parametro = parametro_exemplo.to_dict()
        
        assert isinstance(dict_parametro, dict)
        assert 'id' in dict_parametro
        assert 'empresa' in dict_parametro
        assert 'lote' in dict_parametro
        assert 'temp_ideal' in dict_parametro
        assert 'umid_ideal' in dict_parametro
        assert 'data_criacao' in dict_parametro
        
        assert dict_parametro['empresa'] == parametro_exemplo.empresa
        assert dict_parametro['lote'] == parametro_exemplo.lote
    
    def test_data_criacao_automatica(self, db_session):
        """Testa se data_criacao é preenchida automaticamente"""
        parametro = Parametro(
            empresa='Empresa',
            lote='LOTE',
            temp_ideal=37.0,
            umid_ideal=60.0
        )
        
        db_session.add(parametro)
        db_session.commit()
        
        assert parametro.data_criacao is not None
        assert isinstance(parametro.data_criacao, datetime)


class TestLeituraModel:
    """Testes para o modelo Leitura"""
    
    def test_criar_leitura(self, db_session):
        """Testa criação de leitura"""
        leitura = Leitura(
            umidade=58.5,
            temperatura=37.2,
            pressao=1012.5,
            lote='LOTE001',
            data_inicial=datetime(2024, 1, 1),
            data_final=datetime(2024, 1, 21)
        )
        
        db_session.add(leitura)
        db_session.commit()
        
        assert leitura.id is not None
        assert leitura.umidade == 58.5
        assert leitura.temperatura == 37.2
        assert leitura.lote == 'LOTE001'
    
    def test_leitura_campos_opcionais(self, db_session):
        """Testa criação de leitura com campos opcionais vazios"""
        leitura = Leitura()
        
        db_session.add(leitura)
        db_session.commit()
        
        assert leitura.id is not None
        assert leitura.umidade is None
        assert leitura.temperatura is None
    
    def test_leitura_com_datas(self, db_session):
        """Testa leitura com datas inicial e final"""
        data_inicial = datetime(2024, 1, 1, 10, 0, 0)
        data_final = datetime(2024, 1, 21, 10, 0, 0)
        
        leitura = Leitura(
            umidade=60.0,
            temperatura=37.5,
            data_inicial=data_inicial,
            data_final=data_final
        )
        
        db_session.add(leitura)
        db_session.commit()
        
        assert leitura.data_inicial == data_inicial
        assert leitura.data_final == data_final


class TestLogModel:
    """Testes para o modelo Log"""
    
    def test_criar_log(self, db_session, usuario_comum):
        """Testa criação de log"""
        log = Log(
            usuario_id=usuario_comum.id,
            usuario_nome=usuario_comum.username,
            acao='TESTE_ACAO',
            detalhes='Detalhes do teste',
            endpoint='/api/test',
            metodo_http='POST',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            status_code=200
        )
        
        db_session.add(log)
        db_session.commit()
        
        assert log.id is not None
        assert log.usuario_id == usuario_comum.id
        assert log.acao == 'TESTE_ACAO'
        assert log.data_hora is not None
    
    def test_log_sem_usuario(self, db_session):
        """Testa criação de log sem usuário (ação anônima)"""
        log = Log(
            usuario_nome='Anônimo',
            acao='LOGIN_FALHOU',
            status_code=401
        )
        
        db_session.add(log)
        db_session.commit()
        
        assert log.id is not None
        assert log.usuario_id is None
        assert log.usuario_nome == 'Anônimo'
    
    def test_log_to_dict(self, db_session, usuario_comum):
        """Testa conversão de log para dicionário"""
        log = Log(
            usuario_id=usuario_comum.id,
            usuario_nome=usuario_comum.username,
            acao='TESTE',
            status_code=200
        )
        
        db_session.add(log)
        db_session.commit()
        
        dict_log = log.to_dict()
        
        assert isinstance(dict_log, dict)
        assert 'id' in dict_log
        assert 'usuario_id' in dict_log
        assert 'acao' in dict_log
        assert 'data_hora' in dict_log
    
    def test_log_relacionamento_usuario(self, db_session, usuario_comum):
        """Testa relacionamento entre Log e User"""
        log = Log(
            usuario_id=usuario_comum.id,
            usuario_nome=usuario_comum.username,
            acao='TESTE',
            status_code=200
        )
        
        db_session.add(log)
        db_session.commit()
        
        # Verificar relacionamento
        assert log.usuario is not None
        assert log.usuario.id == usuario_comum.id
        assert log.usuario.username == usuario_comum.username
    
    def test_registrar_log_metodo_estatico(self, app, db_session, usuario_comum):
        """Testa método estático registrar_log"""
        with app.test_request_context('/test', method='GET'):
            Log.registrar_log(
                usuario=usuario_comum,
                acao='TESTE_ESTATICO',
                detalhes='Teste do método estático',
                status_code=200
            )
        
        # Verificar se o log foi criado
        logs = Log.query.filter_by(acao='TESTE_ESTATICO').all()
        assert len(logs) == 1
        assert logs[0].usuario_id == usuario_comum.id
