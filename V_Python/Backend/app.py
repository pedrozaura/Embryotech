from flask import Flask, request, jsonify, render_template, redirect, url_for, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
import jwt
import datetime
from functools import wraps
from config import Config
from flask_cors import CORS
from extensions import db, migrate
import secrets
import os
import json

from sqlalchemy.sql import text
from datetime import timedelta

# Importar Flasgger para Swagger
from flasgger import Swagger, swag_from

# Importar sistema de logging
from logging_utils import (
    log_activity, log_login_attempt, log_logout, log_parametro_alteracao,
    log_acesso_tela, log_crud_operation, registrar_log_atividade
)

from models import User, Item, Leitura, Parametro, Log

# Obtenha o caminho absoluto do diretório onde app.py está (Backend/)
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuração da porta
PORT = int(os.environ.get('PORT', 5001))  # Padrão 5001, mas pode ser sobrescrito

# ==================== CONFIGURAÇÕES DO SWAGGER ====================

# Adicione esta função no início do app.py, após as importações
def get_swagger_host():
    """Detecta o host correto para o Swagger baseado no ambiente"""
    import os
    if os.getenv('DOCKER_ENV'):
        return None  # Deixa o Swagger detectar automaticamente
    return f"localhost:{PORT}"

# Configuração principal do Swagger
SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # Documenta todas as rotas
            "model_filter": lambda tag: True,  # Inclui todos os modelos
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/",  # URL principal da documentação
}

# Template principal do Swagger
SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Embryotech API",
        "description": """
        ## Sistema de Monitoramento de Embriões
        
        Esta API fornece funcionalidades completas para:
        
        - **Autenticação**: Login/logout com tokens JWT
        - **Gestão de Usuários**: Registro, listagem e administração de usuários
        - **Leituras**: CRUD completo para leituras de sensores (temperatura, umidade, pressão)
        - **Parâmetros**: Gestão de parâmetros ideais por empresa e lote
        - **Relatórios**: Geração de relatórios em PDF
        - **Auditoria**: Logs completos de todas as ações do sistema
        
        ### Como Usar
        
        1. **Registre-se** ou faça **login** para obter um token JWT
        2. **Clique em "Authorize"** e insira: `Bearer {seu_token}`
        3. **Teste os endpoints** diretamente nesta interface
        
        ### Permissões
        
        - **Usuários comuns**: Podem gerenciar leituras e visualizar dados
        - **Administradores**: Acesso completo a todas as funcionalidades
        """,
    #    "contact": {
    #        "responsibleOrganization": "Outside Agrotech",
    #        "responsibleDeveloper": "Equipe de Desenvolvimento",
    #        "email": "suporte@outsideagro.tech",
    #        "url": "https://outsideagro.tech",
    #    },
        "version": "2.0.0"
    },
    "host": get_swagger_host(),
    "basePath": "/",
    "schemes": [
        "https"
    ],
    "consumes": [
        "application/json"
    ],
    "produces": [
        "application/json",
        "application/pdf"
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Token de autorização JWT. Formato: 'Bearer {seu_token_jwt_aqui}'"
        }
    },
    "tags": [
        {
            "name": "Sistema",
            "description": "Endpoints de informações do sistema"
        },
        {
            "name": "Autenticação",
            "description": "Login, logout e gestão de tokens JWT"
        },
        {
            "name": "Usuários",
            "description": "Gestão de usuários do sistema"
        },
        {
            "name": "Leituras",
            "description": "CRUD de leituras de sensores (temperatura, umidade, pressão)"
        },
        {
            "name": "Parâmetros",
            "description": "Gestão de parâmetros ideais por empresa e lote"
        },
        {
            "name": "Logs",
            "description": "Sistema de auditoria e logs de atividades"
        },
        {
            "name": "Relatórios",
            "description": "Geração de relatórios em PDF"
        }
    ],
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "ID único do usuário"},
                "username": {"type": "string", "description": "Nome de usuário único"},
                "email": {"type": "string", "format": "email", "description": "Email do usuário"},
                "is_admin": {"type": "boolean", "description": "Se o usuário possui privilégios administrativos"}
            }
        },
        "Leitura": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "ID único da leitura"},
                "temperatura": {"type": "number", "format": "float", "description": "Temperatura em graus Celsius"},
                "umidade": {"type": "number", "format": "float", "description": "Umidade relativa em porcentagem"},
                "pressao": {"type": "number", "format": "float", "description": "Pressão atmosférica em hPa"},
                "lote": {"type": "string", "description": "Identificador do lote"},
                "data_inicial": {"type": "string", "format": "date-time", "description": "Data/hora inicial da leitura"},
                "data_final": {"type": "string", "format": "date-time", "description": "Data/hora final da leitura"}
            }
        },
        "Parametro": {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "description": "ID único do parâmetro"},
                "empresa": {"type": "string", "description": "Nome da empresa"},
                "lote": {"type": "string", "description": "Identificador do lote"},
                "temp_ideal": {"type": "number", "format": "float", "description": "Temperatura ideal em °C"},
                "umid_ideal": {"type": "number", "format": "float", "description": "Umidade ideal em %"},
                "pressao_ideal": {"type": "number", "format": "float", "description": "Pressão ideal em hPa"},
                "lumens": {"type": "number", "format": "float", "description": "Iluminação em lumens"},
                "id_sala": {"type": "string", "description": "Identificador da sala"},
                "estagio_ovo": {"type": "string", "description": "Estágio de desenvolvimento do ovo"}
            }
        },
        "Error": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Mensagem de erro"}
            }
        }
    }
}

# ==================== CRIAÇÃO DA APLICAÇÃO ====================

app = Flask(__name__,
          static_folder=os.path.join(basedir, 'static'),
          template_folder=os.path.join(basedir, 'templates'))

CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

app.config.from_object(Config)

# Inicializar Swagger
swagger = Swagger(app, config=SWAGGER_CONFIG, template=SWAGGER_TEMPLATE)

db.init_app(app)
migrate.init_app(app, db)

# ==================== MIDDLEWARES E DECORADORES ====================

# Middleware para logging automático
@app.before_request
def before_request():
    """Middleware para logging automático de acessos"""
    # Pular documentação do Swagger e arquivos estáticos
    if (not request.endpoint or 
        request.endpoint.startswith('static') or
        request.endpoint.startswith('flasgger')):
        return
    
    # Se for um endpoint de página (não API), registrar acesso
    if request.endpoint in ['login', 'dashboard']:
        user = None
        token = request.cookies.get('embryotech_token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        if token:
            try:
                user = User.verify_auth_token(token, app.config['JWT_SECRET_KEY'])
            except:
                pass
        
        log_acesso_tela(
            usuario=user,
            tela=request.endpoint,
            detalhes_adicionais={
                'user_agent': request.headers.get('User-Agent', ''),
                'ip': request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
                'timestamp': datetime.datetime.utcnow().isoformat()
            }
        )

# Decorator para rotas que requerem autenticação
def token_required(f):
    """Decorator para autenticação via token JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            parts = auth_header.split()
            
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
            else:
                return jsonify({'message': 'Authorization header must be Bearer token!'}), 401
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            current_user = User.verify_auth_token(token, app.config['JWT_SECRET_KEY'])
            if not current_user:
                return jsonify({'message': 'Token is invalid!'}), 401
            
            # Adicionar usuário ao contexto global
            g.current_user = current_user
            
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# ==================== ROTAS DE PÁGINAS (TEMPLATES) ====================

@app.route('/')
@app.route('/login')
def login():
    """Página de login"""
    logout_success = request.args.get('logout') == 'success'
    return render_template('login.html', logout_success=logout_success)

@app.route('/dashboard')
def dashboard():
    """Dashboard principal - requer autenticação via JavaScript"""
    return render_template('dashboard.html')

# Rota para redirecionar para a documentação
@app.route('/docs')
@app.route('/api-docs')
def redirect_to_swagger():
    """Redireciona para a documentação Swagger"""
    return redirect('/swagger/')

# ==================== ROTAS DE API COM DOCUMENTAÇÃO SWAGGER ====================

@app.route('/api/')
@log_activity("API_STATUS_CHECK")
@swag_from({
    'tags': ['Sistema'],
    'summary': 'Status da API',
    'description': 'Endpoint de status da API e informações do sistema',
    'responses': {
        200: {
            'description': 'Status da API e informações do sistema',
            'schema': {
                'type': 'object',
                'properties': {
                    'mensagem': {'type': 'string'},
                    'data_hora': {'type': 'string'},
                    'PORTA': {'type': 'integer'},
                    'fuso_horario': {'type': 'string'},
                    'swagger_ui': {'type': 'string'},
                    'versao': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Erro interno do servidor',
            'schema': {'$ref': '#/definitions/Error'}
        }
    }
})
def api_status():
    """Endpoint de status da API"""
    try:
        data_hora_db = db.session.execute(text("SELECT CURRENT_TIMESTAMP")).scalar()
        data_hora_ajustada = data_hora_db - timedelta(hours=3)
        return jsonify({
            "mensagem": "Bem-vindo ao Backend do Sistema Embryotech",
            "data_hora": data_hora_ajustada.strftime("%Y-%m-%d %H:%M:%S"),
            "PORTA": PORT,
            "fuso_horario": "GMT-3",
            "swagger_ui": f"http://localhost:{PORT}/swagger/",
            "versao": "2.0.0"
        })
    except Exception as e:
        return jsonify({"erro": f"Erro ao recuperar hora: {str(e)}"}), 500

@app.route('/api/register', methods=['POST'])
@log_activity("USUARIO_REGISTRO")
@swag_from({
    'tags': ['Usuários'],
    'summary': 'Registrar usuário',
    'description': 'Registrar novo usuário no sistema',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['username', 'password', 'email'],
            'properties': {
                'username': {'type': 'string', 'example': 'joao123', 'description': 'Nome de usuário único'},
                'password': {'type': 'string', 'example': 'senha123', 'description': 'Senha (mínimo 6 caracteres)'},
                'email': {'type': 'string', 'format': 'email', 'example': 'joao@email.com', 'description': 'Email válido'}
            }
        }
    }],
    'responses': {
        201: {'description': 'Usuário registrado com sucesso'},
        400: {'description': 'Dados inválidos ou incompletos'}
    }
})
def api_register():
    """Registrar novo usuário"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        log_crud_operation(None, 'users', 'CREATE_FAILED', dados={'erro': 'campos_faltando'})
        return jsonify({'message': 'Missing required fields!'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        log_crud_operation(None, 'users', 'CREATE_FAILED', dados={'erro': 'username_existe', 'username': data['username']})
        return jsonify({'message': 'Username already exists!'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        log_crud_operation(None, 'users', 'CREATE_FAILED', dados={'erro': 'email_existe', 'email': data['email']})
        return jsonify({'message': 'Email already exists!'}), 400
    
    new_user = User(
        username=data['username'],
        email=data['email']
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    log_crud_operation(None, 'users', 'CREATE', dados={'username': data['username'], 'email': data['email']})
    
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Login',
    'description': 'Fazer login no sistema e obter token JWT',
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'type': 'object',
            'required': ['username', 'password'],
            'properties': {
                'username': {'type': 'string', 'example': 'joao123'},
                'password': {'type': 'string', 'example': 'senha123'}
            }
        }
    }],
    'responses': {
        200: {
            'description': 'Login realizado com sucesso',
            'schema': {
                'type': 'object',
                'properties': {
                    'token': {'type': 'string', 'description': 'Token JWT para autenticação'},
                    'user': {'$ref': '#/definitions/User'}
                }
            }
        },
        400: {'description': 'Campos obrigatórios não informados'},
        401: {'description': 'Credenciais inválidas'}
    }
})
def api_login():
    """Login de usuário"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        log_login_attempt('', False, 'campos_faltando')
        return jsonify({'message': 'Missing username or password!'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        log_login_attempt(data['username'], False, 'credenciais_invalidas')
        return jsonify({'message': 'Invalid username or password!'}), 401
    
    token = user.generate_auth_token(app.config['JWT_SECRET_KEY'])
    log_login_attempt(data['username'], True)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }
    }), 200

@app.route('/api/logout', methods=['POST'])
@token_required
@log_activity("LOGOUT")
@swag_from({
    'tags': ['Autenticação'],
    'summary': 'Logout',
    'description': 'Fazer logout do sistema',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Logout realizado com sucesso'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_logout(current_user):
    """Logout de usuário"""
    log_logout(current_user)
    return jsonify({'message': 'Logout realizado com sucesso'}), 200

@app.route('/api/leituras', methods=['POST'])
@token_required
@log_activity("CRIAR_LEITURAS")
@swag_from({
    'tags': ['Leituras'],
    'summary': 'Criar leituras',
    'description': 'Criar novas leituras de embrião (suporte a múltiplas leituras)',
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {
            'oneOf': [
                {'$ref': '#/definitions/Leitura'},
                {'type': 'array', 'items': {'$ref': '#/definitions/Leitura'}}
            ]
        }
    }],
    'responses': {
        201: {'description': 'Leituras criadas com sucesso'},
        400: {'description': 'Dados inválidos'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_criar_leitura(current_user):
    """Criar novas leituras de embrião (suporte a múltiplas leituras)"""
    try:
        if not request.is_json:
            return jsonify({'message': 'O corpo da requisição deve ser JSON'}), 400
            
        data = request.get_json()
        
        if not isinstance(data, list):
            data = [data]
        
        leituras = []
        for item in data:
            nova = Leitura(
                umidade=item.get('umidade'),
                temperatura=item.get('temperatura'),
                pressao=item.get('pressao'),
                lote=item.get('lote'),
                data_inicial=item.get('data_inicial'),
                data_final=item.get('data_final')
            )
            leituras.append(nova)
        
        db.session.add_all(leituras)
        db.session.commit()
        
        log_crud_operation(current_user, 'leituras', 'CREATE_BATCH', dados={'quantidade': len(leituras)})
        
        return jsonify({
            'message': f'{len(leituras)} leituras criadas com sucesso',
            'quantidade': len(leituras)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_crud_operation(current_user, 'leituras', 'CREATE_FAILED', dados={'erro': str(e)})
        return jsonify({'message': f'Erro ao processar os dados: {str(e)}'}), 400

@app.route('/api/leituras', methods=['GET'])
@token_required
@log_activity("LISTAR_LEITURAS")
@swag_from({
    'tags': ['Leituras'],
    'summary': 'Listar leituras',
    'description': 'Listar leituras de embriões com filtro opcional por lote',
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'lote',
        'in': 'query',
        'type': 'string',
        'required': False,
        'description': 'Filtrar por lote específico',
        'example': 'LOTE_001'
    }],
    'responses': {
        200: {
            'description': 'Lista de leituras',
            'schema': {
                'type': 'array',
                'items': {'$ref': '#/definitions/Leitura'}
            }
        },
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_listar_leituras(current_user):
    """Listar todas as leituras de embriões"""
    lote = request.args.get('lote')
    
    query = Leitura.query
    
    if lote:
        query = query.filter(Leitura.lote == lote)
    
    leituras = query.order_by(Leitura.data_inicial.desc()).all()
    
    return jsonify([{
        'id': l.id,
        'umidade': l.umidade,
        'temperatura': l.temperatura,
        'pressao': l.pressao,
        'lote': l.lote,
        'data_inicial': l.data_inicial.isoformat() if l.data_inicial else None,
        'data_final': l.data_final.isoformat() if l.data_final else None
    } for l in leituras]), 200

@app.route('/api/leituras/<int:leitura_id>', methods=['PUT'])
@token_required
@log_activity("ATUALIZAR_LEITURA")
@swag_from({
    'tags': ['Leituras'],
    'summary': 'Atualizar leitura',
    'description': 'Atualizar uma leitura existente',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'leitura_id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {'$ref': '#/definitions/Leitura'}}
    ],
    'responses': {
        200: {'description': 'Leitura atualizada com sucesso'},
        404: {'description': 'Leitura não encontrada'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_atualizar_leitura(current_user, leitura_id):
    """Atualizar uma leitura existente"""
    leitura = Leitura.query.get(leitura_id)
    if not leitura:
        return jsonify({'message': 'Leitura não encontrada'}), 404

    data = request.get_json()
    dados_anteriores = {
        'umidade': leitura.umidade,
        'temperatura': leitura.temperatura,
        'pressao': leitura.pressao,
        'lote': leitura.lote
    }
    
    leitura.umidade = data.get('umidade', leitura.umidade)
    leitura.temperatura = data.get('temperatura', leitura.temperatura)
    leitura.pressao = data.get('pressao', leitura.pressao)
    leitura.lote = data.get('lote', leitura.lote)
    leitura.data_inicial = data.get('data_inicial', leitura.data_inicial)
    leitura.data_final = data.get('data_final', leitura.data_final)

    db.session.commit()
    
    log_crud_operation(current_user, 'leituras', 'UPDATE', leitura_id, 
                      dados={'anteriores': dados_anteriores, 'novos': data})
    
    return jsonify({'message': 'Leitura atualizada com sucesso'}), 200

@app.route('/api/leituras/<int:leitura_id>', methods=['DELETE'])
@token_required
@log_activity("DELETAR_LEITURA")
@swag_from({
    'tags': ['Leituras'],
    'summary': 'Deletar leitura',
    'description': 'Deletar uma leitura existente',
    'security': [{'Bearer': []}],
    'parameters': [{'name': 'leitura_id', 'in': 'path', 'type': 'integer', 'required': True}],
    'responses': {
        200: {'description': 'Leitura deletada com sucesso'},
        404: {'description': 'Leitura não encontrada'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_deletar_leitura(current_user, leitura_id):
    """Deletar uma leitura existente"""
    leitura = Leitura.query.get(leitura_id)
    if not leitura:
        return jsonify({'message': 'Leitura não encontrada'}), 404

    dados_leitura = {
        'id': leitura.id,
        'lote': leitura.lote,
        'temperatura': leitura.temperatura
    }
    
    db.session.delete(leitura)
    db.session.commit()
    
    log_crud_operation(current_user, 'leituras', 'DELETE', leitura_id, dados=dados_leitura)
    
    return jsonify({'message': 'Leitura deletada com sucesso'}), 200

@app.route('/api/parametros', methods=['POST'])
@token_required
@log_activity("CRIAR_PARAMETRO")
@swag_from({
    'tags': ['Parâmetros'],
    'summary': 'Criar parâmetros',
    'description': 'Criar novo conjunto de parâmetros ideais (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'body',
        'in': 'body',
        'required': True,
        'schema': {'$ref': '#/definitions/Parametro'}
    }],
    'responses': {
        201: {'description': 'Parâmetro criado com sucesso'},
        403: {'description': 'Acesso negado (apenas administradores)'},
        400: {'description': 'Dados inválidos ou incompletos'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_criar_parametro(current_user):
    """Criar novo conjunto de parâmetros ideais"""
    if not current_user.is_admin:
        log_crud_operation(current_user, 'parametros', 'CREATE_DENIED', dados={'motivo': 'nao_admin'})
        return jsonify({'message': 'Acesso negado!'}), 403

    data = request.get_json()
    try:
        if not all([data.get('empresa'), data.get('lote'), data.get('temp_ideal'), data.get('umid_ideal')]):
            return jsonify({'message': 'Empresa, lote, temperatura e umidade são obrigatórios'}), 400

        novo_parametro = Parametro(
            empresa=data['empresa'],
            lote=data['lote'],
            temp_ideal=data['temp_ideal'],
            umid_ideal=data['umid_ideal'],
            pressao_ideal=data.get('pressao_ideal'),
            lumens=data.get('lumens'),
            id_sala=data.get('id_sala'),
            estagio_ovo=data.get('estagio_ovo')
        )
        db.session.add(novo_parametro)
        db.session.commit()
        
        log_crud_operation(current_user, 'parametros', 'CREATE', novo_parametro.id, 
                          dados={'empresa': data['empresa'], 'lote': data['lote']})
        
        return jsonify({
            'message': 'Parâmetro criado com sucesso!',
            'parametro': novo_parametro.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        log_crud_operation(current_user, 'parametros', 'CREATE_FAILED', dados={'erro': str(e)})
        return jsonify({'message': f'Erro ao salvar parâmetro: {str(e)}'}), 400

@app.route('/api/empresas', methods=['GET'])
@token_required
@log_activity("LISTAR_EMPRESAS")
@swag_from({
    'tags': ['Parâmetros'],
    'summary': 'Listar empresas',
    'description': 'Obter lista de empresas cadastradas (apenas administradores)',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Lista de empresas'},
        403: {'description': 'Acesso negado (apenas administradores)'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_get_empresas(current_user):
    """Obter lista de empresas cadastradas"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    empresas = db.session.query(Parametro.empresa).distinct().all()
    return jsonify([e[0] for e in empresas if e[0]]), 200

@app.route('/api/lotes', methods=['GET'])
@token_required
@log_activity("LISTAR_LOTES")
@swag_from({
    'tags': ['Parâmetros'],
    'summary': 'Listar lotes',
    'description': 'Obter lista de lotes com filtro opcional por empresa',
    'security': [{'Bearer': []}],
    'parameters': [{'name': 'empresa', 'in': 'query', 'type': 'string', 'required': False}],
    'responses': {
        200: {'description': 'Lista de lotes'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_get_lotes(current_user):
    """Obter lista de todos os lotes (ou filtrado por empresa)"""
    empresa = request.args.get('empresa')
    
    query = db.session.query(Parametro.lote).distinct()
    if empresa:
        query = query.filter_by(empresa=empresa)
    
    lotes = query.all()
    return jsonify([l[0] for l in lotes if l[0]]), 200

@app.route('/api/parametros', methods=['GET'])
@token_required
@log_activity("BUSCAR_PARAMETROS")
@swag_from({
    'tags': ['Parâmetros'],
    'summary': 'Buscar parâmetros',
    'description': 'Buscar parâmetros por empresa e lote (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'empresa', 'in': 'query', 'type': 'string', 'required': True},
        {'name': 'lote', 'in': 'query', 'type': 'string', 'required': True}
    ],
    'responses': {
        200: {'description': 'Parâmetros encontrados'},
        400: {'description': 'Empresa e lote são obrigatórios'},
        403: {'description': 'Acesso negado (apenas administradores)'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_get_parametros(current_user):
    """Buscar parâmetros por empresa e lote"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403

    empresa = request.args.get('empresa')
    lote = request.args.get('lote')

    if not empresa or not lote:
        return jsonify({'message': 'Empresa e lote são obrigatórios'}), 400

    parametros = Parametro.query.filter_by(empresa=empresa, lote=lote).all()

    return jsonify([p.to_dict() for p in parametros]), 200

@app.route('/api/parametros/<int:id>', methods=['PUT'])
@token_required
@log_activity("ATUALIZAR_PARAMETRO")
@swag_from({
    'tags': ['Parâmetros'],
    'summary': 'Atualizar parâmetros',
    'description': 'Atualizar parâmetros existentes (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'id', 'in': 'path', 'type': 'integer', 'required': True},
        {'name': 'body', 'in': 'body', 'required': True, 'schema': {'$ref': '#/definitions/Parametro'}}
    ],
    'responses': {
        200: {'description': 'Parâmetro atualizado com sucesso'},
        404: {'description': 'Parâmetro não encontrado'},
        403: {'description': 'Acesso negado (apenas administradores)'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_atualizar_parametro(current_user, id):
    """Atualizar parâmetros existentes"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403

    parametro = Parametro.query.get(id)
    if not parametro:
        return jsonify({'message': 'Parâmetro não encontrado'}), 404

    data = request.get_json()
    dados_anteriores = parametro.to_dict()
    
    try:
        if 'empresa' in data:
            parametro.empresa = data['empresa']
        if 'lote' in data:
            parametro.lote = data['lote']
        if 'temp_ideal' in data:
            parametro.temp_ideal = data['temp_ideal']
        if 'umid_ideal' in data:
            parametro.umid_ideal = data['umid_ideal']
        if 'pressao_ideal' in data:
            parametro.pressao_ideal = data.get('pressao_ideal')
        if 'lumens' in data:
            parametro.lumens = data.get('lumens')
        if 'id_sala' in data:
            parametro.id_sala = data.get('id_sala')
        if 'estagio_ovo' in data:
            parametro.estagio_ovo = data.get('estagio_ovo')

        db.session.commit()
        
        log_parametro_alteracao(current_user, id, dados_anteriores, parametro.to_dict(), 'UPDATE')
        
        return jsonify({
            'message': 'Parâmetro atualizado com sucesso!',
            'parametro': parametro.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        log_crud_operation(current_user, 'parametros', 'UPDATE_FAILED', id, dados={'erro': str(e)})
        return jsonify({'message': f'Erro ao atualizar parâmetro: {str(e)}'}), 400

@app.route('/api/logs', methods=['GET'])
@token_required
@log_activity("CONSULTAR_LOGS")
@swag_from({
    'tags': ['Logs'],
    'summary': 'Consultar logs',
    'description': 'Consultar logs do sistema com filtros opcionais (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'usuario_id', 'in': 'query', 'type': 'integer', 'required': False},
        {'name': 'acao', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'data_inicio', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False},
        {'name': 'data_fim', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False},
        {'name': 'limite', 'in': 'query', 'type': 'integer', 'required': False, 'default': 100}
    ],
    'responses': {
        200: {'description': 'Lista de logs'},
        403: {'description': 'Acesso negado (apenas administradores)'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_get_logs(current_user):
    """Consultar logs do sistema (apenas para administradores)"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    usuario_id = request.args.get('usuario_id', type=int)
    acao = request.args.get('acao')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    limite = request.args.get('limite', 100, type=int)
    
    query = Log.query
    
    if usuario_id:
        query = query.filter(Log.usuario_id == usuario_id)
    if acao:
        query = query.filter(Log.acao.contains(acao))
    if data_inicio:
        query = query.filter(Log.data_hora >= data_inicio)
    if data_fim:
        query = query.filter(Log.data_hora <= data_fim)
    
    logs = query.order_by(Log.data_hora.desc()).limit(limite).all()
    
    return jsonify([log.to_dict() for log in logs]), 200

@app.route('/api/usuarios', methods=['GET'])
@token_required
@log_activity("LISTAR_USUARIOS")
@swag_from({
    'tags': ['Usuários'],
    'summary': 'Listar usuários',
    'description': 'Obter lista de usuários (apenas administradores)',
    'security': [{'Bearer': []}],
    'responses': {
        200: {'description': 'Lista de usuários'},
        403: {'description': 'Acesso negado (apenas administradores)'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_get_usuarios(current_user):
    """Obter lista de usuários (apenas para administradores)"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    usuarios = User.query.all()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'is_admin': u.is_admin
    } for u in usuarios]), 200

@app.route('/api/relatorio/leituras', methods=['GET'])
@token_required
@log_activity("RELATORIO_LEITURAS")
@swag_from({
    'tags': ['Relatórios'],
    'summary': 'Relatório de leituras',
    'description': 'Relatório de leituras com filtros opcionais (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'lote', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'data_inicio', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False},
        {'name': 'data_fim', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False}
    ],
    'responses': {
        200: {'description': 'Relatório de leituras'},
        403: {'description': 'Acesso negado (apenas administradores)'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_relatorio_leituras(current_user):
    """Relatório de leituras com filtros"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    lote = request.args.get('lote')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Leitura.query
    
    if lote:
        query = query.filter(Leitura.lote == lote)
    if data_inicio:
        query = query.filter(Leitura.data_inicial >= data_inicio)
    if data_fim:
        data_fim_obj = datetime.datetime.strptime(data_fim, '%Y-%m-%d')
        data_fim_obj = data_fim_obj.replace(hour=23, minute=59, second=59)
        query = query.filter(Leitura.data_inicial <= data_fim_obj)
    
    leituras = query.order_by(Leitura.data_inicial.desc()).all()
    
    return jsonify([{
        'id': l.id,
        'umidade': l.umidade,
        'temperatura': l.temperatura,
        'pressao': l.pressao,
        'lote': l.lote,
        'data_inicial': l.data_inicial.isoformat() if l.data_inicial else None,
        'data_final': l.data_final.isoformat() if l.data_final else None
    } for l in leituras]), 200

@app.route('/api/relatorio/auditoria/pdf', methods=['GET'])
@token_required
@log_activity("EXPORTAR_AUDITORIA_PDF")
@swag_from({
    'tags': ['Relatórios'],
    'summary': 'Exportar auditoria PDF',
    'description': 'Exportar relatório de auditoria em PDF (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'usuario_id', 'in': 'query', 'type': 'integer', 'required': False},
        {'name': 'data_inicio', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False},
        {'name': 'data_fim', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False}
    ],
    'produces': ['application/pdf'],
    'responses': {
        200: {'description': 'Arquivo PDF gerado'},
        403: {'description': 'Acesso negado (apenas administradores)'},
        500: {'description': 'Erro ao gerar PDF'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_exportar_auditoria_pdf(current_user):
    """Exportar relatório de auditoria em PDF"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        
        usuario_id = request.args.get('usuario_id', type=int)
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        query = Log.query
        if usuario_id:
            query = query.filter(Log.usuario_id == usuario_id)
        if data_inicio:
            query = query.filter(Log.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(Log.data_hora <= data_fim)
        
        logs = query.order_by(Log.data_hora.desc()).limit(500).all()
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=cm, leftMargin=cm, 
                               topMargin=cm, bottomMargin=cm)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#25691b'),
            alignment=1,
            spaceAfter=20
        )
        
        elements = []
        
        title = Paragraph("Relatório de Auditoria - Embryotech", title_style)
        elements.append(title)
        
        info_text = f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}<br/>"
        info_text += f"Total de registros: {len(logs)}<br/>"
        if usuario_id:
            usuario = User.query.get(usuario_id)
            info_text += f"Filtrado por usuário: {usuario.username if usuario else 'N/A'}<br/>"
        if data_inicio:
            info_text += f"Data início: {data_inicio}<br/>"
        if data_fim:
            info_text += f"Data fim: {data_fim}<br/>"
        
        info_para = Paragraph(info_text, styles['Normal'])
        elements.append(info_para)
        elements.append(Spacer(1, 20))
        
        if logs:
            data = [['Data/Hora', 'Usuário', 'Ação', 'IP', 'Status']]
            
            for log in logs:
                data.append([
                    log.data_hora.strftime('%d/%m/%Y %H:%M') if log.data_hora else '-',
                    log.usuario_nome or 'Anônimo',
                    log.acao[:50] + ('...' if len(log.acao) > 50 else ''),
                    log.ip_address or '-',
                    str(log.status_code) if log.status_code else '-'
                ])
            
            table = Table(data, colWidths=[3*cm, 2.5*cm, 4*cm, 2.5*cm, 1.5*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#25691b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph("Nenhum registro encontrado para os filtros selecionados.", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        
        return buffer.getvalue(), 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="auditoria_embryotech.pdf"'
        }
        
    except ImportError:
        return jsonify({'message': 'Biblioteca reportlab não instalada. Execute: pip install reportlab'}), 500
    except Exception as e:
        return jsonify({'message': f'Erro ao gerar PDF: {str(e)}'}), 500

@app.route('/api/relatorio/leituras/pdf', methods=['GET'])
@token_required
@log_activity("EXPORTAR_LEITURAS_PDF")
@swag_from({
    'tags': ['Relatórios'],
    'summary': 'Exportar leituras PDF',
    'description': 'Exportar relatório de leituras em PDF (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'lote', 'in': 'query', 'type': 'string', 'required': False},
        {'name': 'data_inicio', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False},
        {'name': 'data_fim', 'in': 'query', 'type': 'string', 'format': 'date', 'required': False}
    ],
    'produces': ['application/pdf'],
    'responses': {
        200: {'description': 'Arquivo PDF gerado'},
        403: {'description': 'Acesso negado (apenas administradores)'},
        500: {'description': 'Erro ao gerar PDF'},
        401: {'description': 'Token inválido ou ausente'}
    }
})
def api_exportar_leituras_pdf(current_user):
    """Exportar relatório de leituras em PDF"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        
        lote = request.args.get('lote')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        query = Leitura.query
        if lote:
            query = query.filter(Leitura.lote == lote)
        if data_inicio:
            query = query.filter(Leitura.data_inicial >= data_inicio)
        if data_fim:
            data_fim_obj = datetime.datetime.strptime(data_fim, '%Y-%m-%d')
            data_fim_obj = data_fim_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(Leitura.data_inicial <= data_fim_obj)
        
        leituras = query.order_by(Leitura.data_inicial.desc()).limit(1000).all()
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=cm, leftMargin=cm, 
                               topMargin=cm, bottomMargin=cm)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#25691b'),
            alignment=1,
            spaceAfter=20
        )
        
        elements = []
        
        title = Paragraph("Relatório de Leituras - Embryotech", title_style)
        elements.append(title)
        
        info_text = f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}<br/>"
        info_text += f"Total de registros: {len(leituras)}<br/>"
        if lote:
            info_text += f"Filtrado por lote: {lote}<br/>"
        if data_inicio:
            info_text += f"Data início: {data_inicio}<br/>"
        if data_fim:
            info_text += f"Data fim: {data_fim}<br/>"
        
        info_para = Paragraph(info_text, styles['Normal'])
        elements.append(info_para)
        elements.append(Spacer(1, 20))
        
        if leituras:
            data = [['Data/Hora', 'Lote', 'Temp.(°C)', 'Umid.(%)', 'Pressão(hPa)']]
            
            for leitura in leituras:
                data.append([
                    leitura.data_inicial.strftime('%d/%m/%Y %H:%M') if leitura.data_inicial else '-',
                    leitura.lote or '-',
                    f"{leitura.temperatura:.1f}" if leitura.temperatura else '-',
                    f"{leitura.umidade:.1f}" if leitura.umidade else '-',
                    f"{leitura.pressao:.1f}" if leitura.pressao else '-'
                ])
            
            table = Table(data, colWidths=[3*cm, 3*cm, 2*cm, 2*cm, 2*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#25691b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph("Nenhum registro encontrado para os filtros selecionados.", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        
        return buffer.getvalue(), 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="leituras_embryotech.pdf"'
        }
        
    except ImportError:
        return jsonify({'message': 'Biblioteca reportlab não instalada. Execute: pip install reportlab'}), 500
    except Exception as e:
        return jsonify({'message': f'Erro ao gerar PDF: {str(e)}'}), 500

@app.route('/api/usuarios/<int:user_id>/senha', methods=['PUT'])
@token_required
@log_activity("ALTERAR_SENHA_USUARIO")
@swag_from({
    'tags': ['Usuários'],
    'summary': 'Alterar senha',
    'description': 'Alterar senha de usuário (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'user_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['nova_senha'],
                'properties': {
                    'nova_senha': {'type': 'string', 'minLength': 6}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Senha alterada com sucesso'},
        400: {'description': 'Nova senha inválida'},
        403: {'description': 'Acesso negado'},
        404: {'description': 'Usuário não encontrado'},
        401: {'description': 'Token inválido'}
    }
})
def api_alterar_senha_usuario(current_user, user_id):
    """Alterar senha de outro usuário (apenas admin)"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    data = request.get_json()
    nova_senha = data.get('nova_senha')
    
    if not nova_senha or len(nova_senha) < 6:
        return jsonify({'message': 'Nova senha deve ter pelo menos 6 caracteres'}), 400
    
    usuario = User.query.get(user_id)
    if not usuario:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    try:
        usuario.set_password(nova_senha)
        db.session.commit()
        
        log_crud_operation(current_user, 'users', 'UPDATE_PASSWORD', user_id, 
                          dados={'usuario_alterado': usuario.username})
        
        return jsonify({'message': 'Senha alterada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao alterar senha: {str(e)}'}), 500

@app.route('/api/usuarios/<int:user_id>/admin', methods=['PUT'])
@token_required
@log_activity("ALTERAR_PRIVILEGIOS_USUARIO")
@swag_from({
    'tags': ['Usuários'],
    'summary': 'Alterar privilégios',
    'description': 'Alterar privilégios de administrador (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [
        {'name': 'user_id', 'in': 'path', 'type': 'integer', 'required': True},
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'required': ['is_admin'],
                'properties': {
                    'is_admin': {'type': 'boolean'}
                }
            }
        }
    ],
    'responses': {
        200: {'description': 'Privilégios alterados com sucesso'},
        400: {'description': 'Não é possível remover próprios privilégios'},
        403: {'description': 'Acesso negado'},
        404: {'description': 'Usuário não encontrado'},
        401: {'description': 'Token inválido'}
    }
})
def api_alterar_privilegios_usuario(current_user, user_id):
    """Alterar privilégios de admin de um usuário (apenas admin)"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    data = request.get_json()
    is_admin = data.get('is_admin', False)
    
    usuario = User.query.get(user_id)
    if not usuario:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    if usuario.id == current_user.id and not is_admin:
        return jsonify({'message': 'Você não pode remover seus próprios privilégios de admin'}), 400
    
    try:
        usuario.is_admin = is_admin
        db.session.commit()
        
        acao = 'PROMOVER_ADMIN' if is_admin else 'REMOVER_ADMIN'
        log_crud_operation(current_user, 'users', acao, user_id, 
                          dados={'usuario_alterado': usuario.username, 'novo_status': is_admin})
        
        return jsonify({'message': 'Privilégios alterados com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao alterar privilégios: {str(e)}'}), 500

@app.route('/api/relatorio/usuarios/pdf', methods=['GET'])
@token_required
@log_activity("EXPORTAR_USUARIOS_PDF")
@swag_from({
    'tags': ['Relatórios'],
    'summary': 'Exportar usuários PDF',
    'description': 'Exportar relatório de usuários em PDF (apenas administradores)',
    'security': [{'Bearer': []}],
    'parameters': [{
        'name': 'tipo',
        'in': 'query',
        'type': 'string',
        'enum': ['admin', 'user'],
        'required': False
    }],
    'produces': ['application/pdf'],
    'responses': {
        200: {'description': 'Arquivo PDF gerado'},
        403: {'description': 'Acesso negado'},
        500: {'description': 'Erro ao gerar PDF'},
        401: {'description': 'Token inválido'}
    }
})
def api_exportar_usuarios_pdf(current_user):
    """Exportar relatório de usuários em PDF"""
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        
        tipo_usuario = request.args.get('tipo')
        usuarios = User.query.all()
        
        if tipo_usuario == 'admin':
            usuarios = [u for u in usuarios if u.is_admin]
        elif tipo_usuario == 'user':
            usuarios = [u for u in usuarios if not u.is_admin]
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=cm, leftMargin=cm, 
                               topMargin=cm, bottomMargin=cm)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#25691b'),
            alignment=1,
            spaceAfter=20
        )
        
        elements = []
        
        title = Paragraph("Relatório de Usuários - Embryotech", title_style)
        elements.append(title)
        
        info_text = f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}<br/>"
        info_text += f"Total de registros: {len(usuarios)}<br/>"
        if tipo_usuario:
            tipo_desc = 'Administradores' if tipo_usuario == 'admin' else 'Usuários Comuns'
            info_text += f"Filtrado por tipo: {tipo_desc}<br/>"
        
        info_para = Paragraph(info_text, styles['Normal'])
        elements.append(info_para)
        elements.append(Spacer(1, 20))
        
        if usuarios:
            data = [['ID', 'Nome de Usuário', 'Email', 'Tipo']]
            
            for usuario in usuarios:
                data.append([
                    str(usuario.id),
                    usuario.username,
                    usuario.email,
                    'Administrador' if usuario.is_admin else 'Usuário Comum'
                ])
            
            table = Table(data, colWidths=[2*cm, 4*cm, 6*cm, 3*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#25691b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph("Nenhum usuário encontrado para os filtros selecionados.", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        
        return buffer.getvalue(), 200, {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="usuarios_embryotech.pdf"'
        }
        
    except ImportError:
        return jsonify({'message': 'Biblioteca reportlab não instalada. Execute: pip install reportlab'}), 500
    except Exception as e:
        return jsonify({'message': f'Erro ao gerar PDF: {str(e)}'}), 500

# ==================== HANDLERS DE ERRO ====================

@app.errorhandler(404)
def not_found(error):
    """Handler para 404 - Página não encontrada"""
    return jsonify({
        'message': 'Endpoint não encontrado',
        'swagger_ui': f'http://localhost:{PORT}/swagger/',
        'error': 'Not Found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handler para 500 - Erro interno"""
    db.session.rollback()
    return jsonify({
        'message': 'Erro interno do servidor',
        'error': 'Internal Server Error'
    }), 500

# ==================== EXECUÇÃO ====================

if __name__ == '__main__':
    print("="*60)
    print(f"🚀 Embryotech API iniciando na porta {PORT}")
    print(f"📚 Documentação Swagger: http://localhost:{PORT}/swagger/")
    print(f"🔗 API Status: http://localhost:{PORT}/api/")
    print(f"💻 Dashboard: http://localhost:{PORT}/dashboard")
    print("="*60)
    
    app.run(host='0.0.0.0', port=PORT, debug=True)