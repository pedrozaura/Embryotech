"""
Testes para sistema de logging
"""
import pytest
import json
from models import Log
from logging_utils import (
    registrar_log_atividade,
    log_login_attempt,
    log_logout,
    log_parametro_alteracao,
    log_acesso_tela,
    log_crud_operation
)


class TestLogBasico:
    """Testes básicos de logging"""
    
    def test_registrar_log_com_usuario(self, app, db_session, usuario_comum):
        """Testa registro de log com usuário"""
        with app.test_request_context('/test', method='GET'):
            registrar_log_atividade(
                usuario=usuario_comum,
                acao='TESTE_ACAO',
                detalhes='Detalhes do teste',
                status_code=200
            )
        
        # Verificar se log foi criado
        logs = Log.query.filter_by(acao='TESTE_ACAO').all()
        assert len(logs) == 1
        assert logs[0].usuario_id == usuario_comum.id
        assert logs[0].usuario_nome == usuario_comum.username
    
    def test_registrar_log_sem_usuario(self, app, db_session):
        """Testa registro de log sem usuário (anônimo)"""
        with app.test_request_context('/test', method='POST'):
            registrar_log_atividade(
                usuario=None,
                acao='ACESSO_ANONIMO',
                detalhes='Acesso sem autenticação',
                status_code=401
            )
        
        logs = Log.query.filter_by(acao='ACESSO_ANONIMO').all()
        assert len(logs) == 1
        assert logs[0].usuario_id is None
    
    def test_log_contem_informacoes_request(self, app, db_session, usuario_comum):
        """Testa se log contém informações da requisição"""
        with app.test_request_context(
            '/api/test',
            method='POST',
            environ_base={'REMOTE_ADDR': '192.168.1.1'}
        ):
            registrar_log_atividade(
                usuario=usuario_comum,
                acao='TESTE_REQUEST',
                status_code=200
            )
        
        log = Log.query.filter_by(acao='TESTE_REQUEST').first()
        assert log is not None
        assert log.endpoint is not None
        assert log.metodo_http == 'POST'
        assert log.ip_address is not None


class TestLogLogin:
    """Testes de logging de login"""
    
    def test_log_login_sucesso(self, app, db_session):
        """Testa log de login bem-sucedido"""
        with app.test_request_context():
            log_login_attempt('usuario_teste', sucesso=True)
        
        logs = Log.query.filter_by(acao='LOGIN_SUCESSO').all()
        assert len(logs) == 1
        assert 'usuario_teste' in logs[0].detalhes
    
    def test_log_login_falha(self, app, db_session):
        """Testa log de login com falha"""
        with app.test_request_context():
            log_login_attempt(
                'usuario_invalido',
                sucesso=False,
                motivo='Senha incorreta'
            )
        
        logs = Log.query.filter_by(acao='LOGIN_FALHOU').all()
        assert len(logs) == 1
        assert 'usuario_invalido' in logs[0].detalhes
        assert 'Senha incorreta' in logs[0].detalhes
    
    def test_log_logout(self, app, db_session, usuario_comum):
        """Testa log de logout"""
        with app.test_request_context():
            log_logout(usuario_comum)
        
        logs = Log.query.filter_by(acao='LOGOUT').all()
        assert len(logs) == 1
        assert logs[0].usuario_id == usuario_comum.id


class TestLogParametros:
    """Testes de logging de parâmetros"""
    
    def test_log_parametro_alteracao(self, app, db_session, usuario_admin):
        """Testa log de alteração de parâmetro"""
        dados_anteriores = {
            'temp_ideal': 37.5,
            'umid_ideal': 60.0
        }
        
        dados_novos = {
            'temp_ideal': 38.0,
            'umid_ideal': 62.0
        }
        
        with app.test_request_context():
            log_parametro_alteracao(
                usuario_admin,
                parametro_id=1,
                dados_anteriores=dados_anteriores,
                dados_novos=dados_novos,
                operacao='UPDATE'
            )
        
        logs = Log.query.filter_by(acao='PARAMETRO_UPDATE').all()
        assert len(logs) == 1
        assert logs[0].usuario_id == usuario_admin.id
        assert '37.5' in logs[0].detalhes
        assert '38.0' in logs[0].detalhes
    
    def test_log_parametro_criacao(self, app, db_session, usuario_admin):
        """Testa log de criação de parâmetro"""
        dados_novos = {
            'empresa': 'Nova Empresa',
            'lote': 'LOTE001'
        }
        
        with app.test_request_context():
            log_parametro_alteracao(
                usuario_admin,
                parametro_id=1,
                dados_anteriores=None,
                dados_novos=dados_novos,
                operacao='CREATE'
            )
        
        logs = Log.query.filter_by(acao='PARAMETRO_CREATE').all()
        assert len(logs) == 1


class TestLogAcessoTela:
    """Testes de logging de acesso a telas"""
    
    def test_log_acesso_dashboard(self, app, db_session, usuario_comum):
        """Testa log de acesso ao dashboard"""
        with app.test_request_context():
            log_acesso_tela(usuario_comum, 'dashboard')
        
        logs = Log.query.filter_by(acao='ACESSO_TELA_DASHBOARD').all()
        assert len(logs) == 1
        assert logs[0].usuario_id == usuario_comum.id
    
    def test_log_acesso_tela_com_detalhes(self, app, db_session, usuario_comum):
        """Testa log de acesso com detalhes adicionais"""
        detalhes = {
            'user_agent': 'Mozilla/5.0',
            'ip': '192.168.1.1'
        }
        
        with app.test_request_context():
            log_acesso_tela(
                usuario_comum,
                'parametros',
                detalhes_adicionais=detalhes
            )
        
        logs = Log.query.filter_by(acao='ACESSO_TELA_PARAMETROS').all()
        assert len(logs) == 1
        assert 'Mozilla' in logs[0].detalhes


class TestLogCRUD:
    """Testes de logging de operações CRUD"""
    
    def test_log_create_operation(self, app, db_session, usuario_comum):
        """Testa log de operação CREATE"""
        dados = {
            'umidade': 60.0,
            'temperatura': 37.5
        }
        
        with app.test_request_context():
            log_crud_operation(
                usuario_comum,
                tabela='leituras',
                operacao='CREATE',
                registro_id=1,
                dados=dados
            )
        
        logs = Log.query.filter_by(acao='CREATE_LEITURAS').all()
        assert len(logs) == 1
        assert '60.0' in logs[0].detalhes
    
    def test_log_update_operation(self, app, db_session, usuario_comum):
        """Testa log de operação UPDATE"""
        dados = {'temperatura': 38.0}
        
        with app.test_request_context():
            log_crud_operation(
                usuario_comum,
                tabela='leituras',
                operacao='UPDATE',
                registro_id=1,
                dados=dados
            )
        
        logs = Log.query.filter_by(acao='UPDATE_LEITURAS').all()
        assert len(logs) == 1
    
    def test_log_delete_operation(self, app, db_session, usuario_admin):
        """Testa log de operação DELETE"""
        dados = {'id': 1, 'lote': 'LOTE001'}
        
        with app.test_request_context():
            log_crud_operation(
                usuario_admin,
                tabela='parametros',
                operacao='DELETE',
                registro_id=1,
                dados=dados
            )
        
        logs = Log.query.filter_by(acao='DELETE_PARAMETROS').all()
        assert len(logs) == 1
    
    def test_log_crud_remove_senha(self, app, db_session, usuario_admin):
        """Testa que log CRUD remove campos de senha"""
        dados = {
            'username': 'usuario',
            'password': 'senha123',  # Deve ser removido
            'email': 'user@email.com'
        }
        
        with app.test_request_context():
            log_crud_operation(
                usuario_admin,
                tabela='users',
                operacao='CREATE',
                dados=dados
            )
        
        logs = Log.query.filter_by(acao='CREATE_USERS').all()
        assert len(logs) == 1
        # Senha não deve estar nos detalhes
        assert 'senha123' not in logs[0].detalhes
        # Outros campos devem estar
        assert 'usuario' in logs[0].detalhes


class TestLogsAPI:
    """Testes da API de consulta de logs"""
    
    def test_consultar_logs_admin(self, client, auth_headers_admin, db_session, usuario_comum):
        """Testa que admin pode consultar logs"""
        # Criar alguns logs
        with client.application.test_request_context():
            Log.registrar_log(usuario_comum, 'TESTE_1', status_code=200)
            Log.registrar_log(usuario_comum, 'TESTE_2', status_code=200)
        
        response = client.get('/api/logs', headers=auth_headers_admin)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_consultar_logs_usuario_comum_negado(self, client, auth_headers_comum):
        """Testa que usuário comum não pode consultar logs"""
        response = client.get('/api/logs', headers=auth_headers_comum)
        
        assert response.status_code == 403
    
    def test_filtrar_logs_por_usuario(self, client, auth_headers_admin, usuario_comum, usuario_admin):
        """Testa filtro de logs por usuário"""
        # Criar logs de usuários diferentes
        with client.application.test_request_context():
            Log.registrar_log(usuario_comum, 'LOG_USER1', status_code=200)
            Log.registrar_log(usuario_admin, 'LOG_ADMIN', status_code=200)
        
        # Filtrar por usuario_comum
        response = client.get(
            f'/api/logs?usuario_id={usuario_comum.id}',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Todos os logs devem ser do usuario_comum
        for log in data:
            if log['usuario_id'] is not None:
                assert log['usuario_id'] == usuario_comum.id
    
    def test_filtrar_logs_por_acao(self, client, auth_headers_admin):
        """Testa filtro de logs por ação"""
        # Criar logs com ações diferentes
        with client.application.test_request_context():
            Log.registrar_log(None, 'LOGIN_SUCESSO', status_code=200)
            Log.registrar_log(None, 'LOGIN_FALHOU', status_code=401)
            Log.registrar_log(None, 'LOGOUT', status_code=200)
        
        # Filtrar por LOGIN
        response = client.get(
            '/api/logs?acao=LOGIN',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Todos os logs devem conter LOGIN na ação
        for log in data:
            assert 'LOGIN' in log['acao']
    
    def test_limite_logs(self, client, auth_headers_admin):
        """Testa limite de logs retornados"""
        # Criar vários logs
        with client.application.test_request_context():
            for i in range(15):
                Log.registrar_log(None, f'LOG_{i}', status_code=200)
        
        # Solicitar apenas 5
        response = client.get(
            '/api/logs?limite=5',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert len(data) <= 5


class TestLogIntegracao:
    """Testes de integração do sistema de logging"""
    
    def test_login_cria_log_automatico(self, client, usuario_comum, db_session):
        """Testa que login cria log automaticamente"""
        dados = {
            'username': 'usuario_teste',
            'password': 'senha123'
        }
        
        logs_antes = Log.query.count()
        
        response = client.post(
            '/api/login',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        logs_depois = Log.query.count()
        assert logs_depois > logs_antes
    
    def test_criar_parametro_cria_log(self, client, auth_headers_admin, db_session):
        """Testa que criar parâmetro gera log"""
        dados = {
            'empresa': 'Empresa Log',
            'lote': 'LOTE_LOG',
            'temp_ideal': 37.5,
            'umid_ideal': 60.0
        }
        
        logs_antes = Log.query.count()
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 201
        
        logs_depois = Log.query.count()
        assert logs_depois > logs_antes
    
    def test_acesso_negado_cria_log(self, client, auth_headers_comum):
        """Testa que acesso negado gera log"""
        dados = {
            'empresa': 'Empresa',
            'lote': 'LOTE',
            'temp_ideal': 37.5,
            'umid_ideal': 60.0
        }
        
        logs_antes = Log.query.count()
        
        # Usuário comum tenta criar parâmetro (requer admin)
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 403
        
        # Deve ter criado log da tentativa
        logs_depois = Log.query.count()
        assert logs_depois > logs_antes
