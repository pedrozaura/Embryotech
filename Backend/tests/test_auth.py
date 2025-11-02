"""
Testes de autenticação e autorização
"""
import pytest
import json
from models import User, Log


class TestRegistro:
    """Testes para registro de novos usuários"""
    
    def test_registro_sucesso(self, client, db_session):
        """Testa registro bem-sucedido de usuário"""
        dados = {
            'username': 'novo_usuario',
            'email': 'novo@email.com',
            'password': 'senha123'
        }
        
        response = client.post(
            '/api/register',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'message' in data
        assert 'user' in data
        
        # Verificar se usuário foi criado no banco
        user = User.query.filter_by(username='novo_usuario').first()
        assert user is not None
        assert user.email == 'novo@email.com'
    
    def test_registro_campos_faltando(self, client):
        """Testa registro com campos obrigatórios faltando"""
        # Faltando password
        dados = {
            'username': 'usuario',
            'email': 'email@email.com'
        }
        
        response = client.post(
            '/api/register',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_registro_username_duplicado(self, client, usuario_comum):
        """Testa registro com username já existente"""
        dados = {
            'username': usuario_comum.username,
            'email': 'outro@email.com',
            'password': 'senha123'
        }
        
        response = client.post(
            '/api/register',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'already exists' in data['message'].lower()
    
    def test_registro_email_duplicado(self, client, usuario_comum):
        """Testa registro com email já existente"""
        dados = {
            'username': 'outro_usuario',
            'email': usuario_comum.email,
            'password': 'senha123'
        }
        
        response = client.post(
            '/api/register',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'already exists' in data['message'].lower()
    
    def test_registro_sem_dados(self, client):
        """Testa registro sem enviar dados"""
        response = client.post(
            '/api/register',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestLogin:
    """Testes para login de usuários"""
    
    def test_login_sucesso(self, client, usuario_comum):
        """Testa login bem-sucedido"""
        dados = {
            'username': 'usuario_teste',
            'password': 'senha123'
        }
        
        response = client.post(
            '/api/login',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data
        assert 'user' in data
        assert len(data['token']) > 0
    
    def test_login_senha_incorreta(self, client, usuario_comum):
        """Testa login com senha incorreta"""
        dados = {
            'username': 'usuario_teste',
            'password': 'senha_errada'
        }
        
        response = client.post(
            '/api/login',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_login_usuario_inexistente(self, client):
        """Testa login com usuário inexistente"""
        dados = {
            'username': 'usuario_nao_existe',
            'password': 'senha123'
        }
        
        response = client.post(
            '/api/login',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_login_campos_faltando(self, client):
        """Testa login sem username ou password"""
        # Sem password
        response = client.post(
            '/api/login',
            data=json.dumps({'username': 'usuario'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        
        # Sem username
        response = client.post(
            '/api/login',
            data=json.dumps({'password': 'senha'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_login_cria_log(self, client, usuario_comum, db_session):
        """Testa se login bem-sucedido cria log"""
        dados = {
            'username': 'usuario_teste',
            'password': 'senha123'
        }
        
        # Contar logs antes
        logs_antes = Log.query.count()
        
        response = client.post(
            '/api/login',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # Verificar se log foi criado
        logs_depois = Log.query.count()
        assert logs_depois > logs_antes


class TestAutorizacao:
    """Testes de autorização e controle de acesso"""
    
    def test_acesso_sem_token(self, client):
        """Testa acesso a endpoint protegido sem token"""
        response = client.get('/api/parametros')
        
        assert response.status_code == 401
        data = json.loads(response.data)
        assert 'token' in data['message'].lower()
    
    def test_acesso_token_invalido(self, client):
        """Testa acesso com token inválido"""
        headers = {
            'Authorization': 'Bearer token_invalido_123',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/api/parametros', headers=headers)
        
        assert response.status_code == 401
    
    def test_acesso_token_formato_incorreto(self, client):
        """Testa acesso com formato de token incorreto"""
        # Sem 'Bearer'
        headers = {
            'Authorization': 'token_sem_bearer',
            'Content-Type': 'application/json'
        }
        
        response = client.get('/api/parametros', headers=headers)
        
        assert response.status_code == 401
    
    def test_acesso_admin_usuario_comum(self, client, auth_headers_comum):
        """Testa se usuário comum não pode acessar rotas admin"""
        # Tentar criar parâmetro (apenas admin)
        dados = {
            'empresa': 'Empresa',
            'lote': 'LOTE',
            'temp_ideal': 37.5,
            'umid_ideal': 60.0
        }
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'negado' in data['message'].lower() or 'denied' in data['message'].lower()
    
    def test_acesso_admin_usuario_admin(self, client, auth_headers_admin):
        """Testa se administrador pode acessar rotas admin"""
        dados = {
            'empresa': 'Empresa',
            'lote': 'LOTE',
            'temp_ideal': 37.5,
            'umid_ideal': 60.0
        }
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        # Admin deve conseguir criar
        assert response.status_code == 201
    
    def test_usuario_comum_acessa_proprias_rotas(self, client, auth_headers_comum):
        """Testa se usuário comum pode acessar suas próprias rotas"""
        # Listar leituras (não requer admin)
        response = client.get('/api/leituras', headers=auth_headers_comum)
        
        assert response.status_code == 200
    
    def test_logout(self, client, auth_headers_comum):
        """Testa logout de usuário"""
        response = client.post('/api/logout', headers=auth_headers_comum)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data


class TestTokenJWT:
    """Testes específicos para tokens JWT"""
    
    def test_token_contem_informacoes_usuario(self, app, usuario_comum):
        """Testa se token contém informações do usuário"""
        token = usuario_comum.generate_auth_token(
            app.config['JWT_SECRET_KEY'],
            expires_in=3600
        )
        
        # Verificar token
        user = User.verify_auth_token(token, app.config['JWT_SECRET_KEY'])
        
        assert user is not None
        assert user.id == usuario_comum.id
        assert user.is_admin == usuario_comum.is_admin
    
    def test_token_expira(self, app, usuario_comum):
        """Testa se token expira após tempo determinado"""
        # Token que expira em -1 segundo (já expirado)
        token = usuario_comum.generate_auth_token(
            app.config['JWT_SECRET_KEY'],
            expires_in=-1
        )
        
        user = User.verify_auth_token(token, app.config['JWT_SECRET_KEY'])
        
        assert user is None
    
    def test_token_diferente_para_usuarios_diferentes(self, app, usuario_comum, usuario_admin):
        """Testa se usuários diferentes geram tokens diferentes"""
        token1 = usuario_comum.generate_auth_token(
            app.config['JWT_SECRET_KEY'],
            expires_in=3600
        )
        
        token2 = usuario_admin.generate_auth_token(
            app.config['JWT_SECRET_KEY'],
            expires_in=3600
        )
        
        assert token1 != token2
    
    def test_token_admin_flag(self, app, usuario_admin):
        """Testa se token contém flag de admin corretamente"""
        token = usuario_admin.generate_auth_token(
            app.config['JWT_SECRET_KEY'],
            expires_in=3600
        )
        
        user = User.verify_auth_token(token, app.config['JWT_SECRET_KEY'])
        
        assert user is not None
        assert user.is_admin is True
