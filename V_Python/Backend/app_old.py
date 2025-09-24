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

# Configuração do Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Embryotech API",
        "description": "Sistema de Monitoramento de Embriões - API completa para gerenciamento de leituras, parâmetros e usuários",
        "contact": {
            "responsibleOrganization": "Embryotech",
            "responsibleDeveloper": "Equipe Embryotech",
            "email": "suporte@embryotech.com",
            "url": "https://embryotech.com",
        },
        "version": "2.0.0"
    },
    "host": f"localhost:{PORT}",
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ],
    "operationId": "get_my_ip",
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Token de autorização JWT. Formato: 'Bearer {token}'"
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

db.init_app(app)
migrate.init_app(app, db)

# Middleware para logging automático
@app.before_request
def before_request():
    # Registrar acesso apenas se não for um endpoint de API ou static
    if not request.endpoint or request.endpoint.startswith('static'):
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

# ==================== ROTAS DE API COM DOCUMENTAÇÃO SWAGGER ====================

@app.route('/api/')
@log_activity("API_STATUS_CHECK")
def api_status():
    """
    Status da API
    ---
    tags:
      - Sistema
    responses:
      200:
        description: Status da API e informações do sistema
        schema:
          type: object
          properties:
            mensagem:
              type: string
              example: "Bem-vindo ao Backend do Sistema Embryotech"
            data_hora:
              type: string
              example: "2024-01-15 14:30:00"
            PORTA:
              type: integer
              example: 5001
            fuso_horario:
              type: string
              example: "GMT-3"
      500:
        description: Erro interno do servidor
        schema:
          type: object
          properties:
            erro:
              type: string
              example: "Erro ao recuperar hora: conexão com BD falhou"
    """
    try:
        data_hora_db = db.session.execute(text("SELECT CURRENT_TIMESTAMP")).scalar()
        data_hora_ajustada = data_hora_db - timedelta(hours=3)
        return jsonify({
            "mensagem": "Bem-vindo ao Backend do Sistema Embryotech",
            "data_hora": data_hora_ajustada.strftime("%Y-%m-%d %H:%M:%S"),
            "PORTA": PORT,
            "fuso_horario": "GMT-3"
        })
    except Exception as e:
        return jsonify({"erro": f"Erro ao recuperar hora: {str(e)}"}), 500

@app.route('/api/register', methods=['POST'])
@log_activity("USUARIO_REGISTRO")
def api_register():
    """
    Registrar novo usuário
    ---
    tags:
      - Usuários
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: "joao123"
              description: Nome de usuário único
            password:
              type: string
              example: "senha123"
              description: Senha (mínimo 6 caracteres)
            email:
              type: string
              example: "joao@email.com"
              description: Email válido
          required:
            - username
            - password
            - email
    responses:
      201:
        description: Usuário registrado com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "User registered successfully!"
      400:
        description: Dados inválidos ou incompletos
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Missing required fields!"
    """
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
def api_login():
    """
    Login de usuário
    ---
    tags:
      - Autenticação
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: "joao123"
              description: Nome de usuário
            password:
              type: string
              example: "senha123"
              description: Senha do usuário
          required:
            - username
            - password
    responses:
      200:
        description: Login realizado com sucesso
        schema:
          type: object
          properties:
            token:
              type: string
              example: "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
              description: Token JWT para autenticação
      400:
        description: Campos obrigatórios não informados
      401:
        description: Credenciais inválidas
    """
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
    
    return jsonify({'token': token}), 200

@app.route('/api/logout', methods=['POST'])
@token_required
@log_activity("LOGOUT")
def api_logout(current_user):
    """
    Logout de usuário
    ---
    tags:
      - Autenticação
    security:
      - Bearer: []
    responses:
      200:
        description: Logout realizado com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Logout realizado com sucesso"
      401:
        description: Token inválido ou ausente
    """
    log_logout(current_user)
    return jsonify({'message': 'Logout realizado com sucesso'}), 200

@app.route('/api/leituras', methods=['POST'])
@token_required
@log_activity("CRIAR_LEITURAS")
def api_criar_leitura(current_user):
    """
    Criar novas leituras de embrião
    ---
    tags:
      - Leituras
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          oneOf:
            - type: object
              properties:
                umidade:
                  type: number
                  example: 65.5
                  description: Umidade relativa (%)
                temperatura:
                  type: number
                  example: 37.8
                  description: Temperatura (°C)
                pressao:
                  type: number
                  example: 1013.2
                  description: Pressão atmosférica (hPa)
                lote:
                  type: string
                  example: "LOTE_001"
                  description: Identificador do lote
                data_inicial:
                  type: string
                  format: date-time
                  example: "2024-01-15T10:00:00"
                data_final:
                  type: string
                  format: date-time
                  example: "2024-01-15T11:00:00"
            - type: array
              items:
                type: object
                properties:
                  umidade:
                    type: number
                  temperatura:
                    type: number
                  pressao:
                    type: number
                  lote:
                    type: string
                  data_inicial:
                    type: string
                    format: date-time
                  data_final:
                    type: string
                    format: date-time
    responses:
      201:
        description: Leituras criadas com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "2 leituras criadas com sucesso"
            quantidade:
              type: integer
              example: 2
      400:
        description: Dados inválidos
      401:
        description: Token inválido ou ausente
    """
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
def api_listar_leituras(current_user):
    """
    Listar leituras de embriões
    ---
    tags:
      - Leituras
    security:
      - Bearer: []
    parameters:
      - name: lote
        in: query
        type: string
        required: false
        description: Filtrar por lote específico
        example: "LOTE_001"
    responses:
      200:
        description: Lista de leituras
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              umidade:
                type: number
                example: 65.5
              temperatura:
                type: number
                example: 37.8
              pressao:
                type: number
                example: 1013.2
              lote:
                type: string
                example: "LOTE_001"
              data_inicial:
                type: string
                format: date-time
                example: "2024-01-15T10:00:00"
              data_final:
                type: string
                format: date-time
                example: "2024-01-15T11:00:00"
      401:
        description: Token inválido ou ausente
    """
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
def api_atualizar_leitura(current_user, leitura_id):
    """
    Atualizar uma leitura existente
    ---
    tags:
      - Leituras
    security:
      - Bearer: []
    parameters:
      - name: leitura_id
        in: path
        type: integer
        required: true
        description: ID da leitura a ser atualizada
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            umidade:
              type: number
              example: 66.0
            temperatura:
              type: number
              example: 38.0
            pressao:
              type: number
              example: 1014.0
            lote:
              type: string
              example: "LOTE_001_MOD"
            data_inicial:
              type: string
              format: date-time
            data_final:
              type: string
              format: date-time
    responses:
      200:
        description: Leitura atualizada com sucesso
      404:
        description: Leitura não encontrada
      401:
        description: Token inválido ou ausente
    """
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
def api_deletar_leitura(current_user, leitura_id):
    """
    Deletar uma leitura
    ---
    tags:
      - Leituras
    security:
      - Bearer: []
    parameters:
      - name: leitura_id
        in: path
        type: integer
        required: true
        description: ID da leitura a ser deletada
    responses:
      200:
        description: Leitura deletada com sucesso
      404:
        description: Leitura não encontrada
      401:
        description: Token inválido ou ausente
    """
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
def api_criar_parametro(current_user):
    """
    Criar conjunto de parâmetros ideais
    ---
    tags:
      - Parâmetros
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            empresa:
              type: string
              example: "Embryotech Inc."
              description: Nome da empresa
            lote:
              type: string
              example: "LOTE_001"
              description: Identificador do lote
            temp_ideal:
              type: number
              example: 37.8
              description: Temperatura ideal (°C)
            umid_ideal:
              type: number
              example: 65.0
              description: Umidade ideal (%)
            pressao_ideal:
              type: number
              example: 1013.2
              description: Pressão ideal (hPa)
            lumens:
              type: number
              example: 1200
              description: Iluminação em lumens
            id_sala:
              type: string
              example: "SALA_A1"
              description: Identificador da sala
            estagio_ovo:
              type: string
              example: "incubacao_inicial"
              description: Estágio do desenvolvimento do ovo
          required:
            - empresa
            - lote
            - temp_ideal
            - umid_ideal
    responses:
      201:
        description: Parâmetro criado com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Parâmetro criado com sucesso!"
            parametro:
              type: object
      403:
        description: Acesso negado (apenas administradores)
      400:
        description: Dados inválidos ou incompletos
      401:
        description: Token inválido ou ausente
    """
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
def api_get_empresas(current_user):
    """
    Obter lista de empresas cadastradas
    ---
    tags:
      - Parâmetros
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de empresas
        schema:
          type: array
          items:
            type: string
          example: ["Embryotech Inc.", "Avícola XYZ"]
      403:
        description: Acesso negado (apenas administradores)
      401:
        description: Token inválido ou ausente
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    empresas = db.session.query(Parametro.empresa).distinct().all()
    return jsonify([e[0] for e in empresas if e[0]]), 200

@app.route('/api/lotes', methods=['GET'])
@token_required
@log_activity("LISTAR_LOTES")
def api_get_lotes(current_user):
    """
    Obter lista de lotes
    ---
    tags:
      - Parâmetros
    security:
      - Bearer: []
    parameters:
      - name: empresa
        in: query
        type: string
        required: false
        description: Filtrar lotes por empresa
        example: "Embryotech Inc."
    responses:
      200:
        description: Lista de lotes
        schema:
          type: array
          items:
            type: string
          example: ["LOTE_001", "LOTE_002", "LOTE_003"]
      401:
        description: Token inválido ou ausente
    """
    empresa = request.args.get('empresa')
    
    query = db.session.query(Parametro.lote).distinct()
    if empresa:
        query = query.filter_by(empresa=empresa)
    
    lotes = query.all()
    return jsonify([l[0] for l in lotes if l[0]]), 200

@app.route('/api/parametros', methods=['GET'])
@token_required
@log_activity("BUSCAR_PARAMETROS")
def api_get_parametros(current_user):
    """
    Buscar parâmetros por empresa e lote
    ---
    tags:
      - Parâmetros
    security:
      - Bearer: []
    parameters:
      - name: empresa
        in: query
        type: string
        required: true
        description: Nome da empresa
        example: "Embryotech Inc."
      - name: lote
        in: query
        type: string
        required: true
        description: Identificador do lote
        example: "LOTE_001"
    responses:
      200:
        description: Parâmetros encontrados
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              empresa:
                type: string
              lote:
                type: string
              temp_ideal:
                type: number
              umid_ideal:
                type: number
              pressao_ideal:
                type: number
              lumens:
                type: number
              id_sala:
                type: string
              estagio_ovo:
                type: string
      400:
        description: Empresa e lote são obrigatórios
      403:
        description: Acesso negado (apenas administradores)
      401:
        description: Token inválido ou ausente
    """
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
def api_atualizar_parametro(current_user, id):
    """
    Atualizar parâmetros existentes
    ---
    tags:
      - Parâmetros
    security:
      - Bearer: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID do parâmetro
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            empresa:
              type: string
            lote:
              type: string
            temp_ideal:
              type: number
            umid_ideal:
              type: number
            pressao_ideal:
              type: number
            lumens:
              type: number
            id_sala:
              type: string
            estagio_ovo:
              type: string
    responses:
      200:
        description: Parâmetro atualizado com sucesso
      404:
        description: Parâmetro não encontrado
      403:
        description: Acesso negado (apenas administradores)
      401:
        description: Token inválido ou ausente
    """
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
def api_get_logs(current_user):
    """
    Consultar logs do sistema
    ---
    tags:
      - Logs
    security:
      - Bearer: []
    parameters:
      - name: usuario_id
        in: query
        type: integer
        required: false
        description: Filtrar por ID do usuário
      - name: acao
        in: query
        type: string
        required: false
        description: Filtrar por ação (busca parcial)
        example: "LOGIN"
      - name: data_inicio
        in: query
        type: string
        format: date
        required: false
        description: Data inicial do filtro
        example: "2024-01-01"
      - name: data_fim
        in: query
        type: string
        format: date
        required: false
        description: Data final do filtro
        example: "2024-01-31"
      - name: limite
        in: query
        type: integer
        required: false
        default: 100
        description: Limite de registros retornados
        example: 50
    responses:
      200:
        description: Lista de logs
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              usuario_id:
                type: integer
              usuario_nome:
                type: string
              acao:
                type: string
              data_hora:
                type: string
                format: date-time
              ip_address:
                type: string
              status_code:
                type: integer
              dados_adicionais:
                type: object
      403:
        description: Acesso negado (apenas administradores)
      401:
        description: Token inválido ou ausente
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    # Parâmetros de filtro
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
def api_get_usuarios(current_user):
    """
    Obter lista de usuários
    ---
    tags:
      - Usuários
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de usuários
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                example: 1
              username:
                type: string
                example: "joao123"
              email:
                type: string
                example: "joao@email.com"
              is_admin:
                type: boolean
                example: false
      403:
        description: Acesso negado (apenas administradores)
      401:
        description: Token inválido ou ausente
    """
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
def api_relatorio_leituras(current_user):
    """
    Relatório de leituras com filtros
    ---
    tags:
      - Relatórios
    security:
      - Bearer: []
    parameters:
      - name: lote
        in: query
        type: string
        required: false
        description: Filtrar por lote
      - name: data_inicio
        in: query
        type: string
        format: date
        required: false
        description: Data inicial
      - name: data_fim
        in: query
        type: string
        format: date
        required: false
        description: Data final
    responses:
      200:
        description: Relatório de leituras
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              umidade:
                type: number
              temperatura:
                type: number
              pressao:
                type: number
              lote:
                type: string
              data_inicial:
                type: string
                format: date-time
              data_final:
                type: string
                format: date-time
      403:
        description: Acesso negado (apenas administradores)
      401:
        description: Token inválido ou ausente
    """
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
def api_exportar_auditoria_pdf(current_user):
    """
    Exportar relatório de auditoria em PDF
    ---
    tags:
      - Relatórios
    security:
      - Bearer: []
    parameters:
      - name: usuario_id
        in: query
        type: integer
        required: false
        description: Filtrar por usuário
      - name: data_inicio
        in: query
        type: string
        format: date
        required: false
        description: Data inicial
      - name: data_fim
        in: query
        type: string
        format: date
        required: false
        description: Data final
    responses:
      200:
        description: Arquivo PDF gerado
        schema:
          type: file
      403:
        description: Acesso negado (apenas administradores)
      500:
        description: Erro ao gerar PDF
      401:
        description: Token inválido ou ausente
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        
        # Parâmetros de filtro
        usuario_id = request.args.get('usuario_id', type=int)
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Consultar logs
        query = Log.query
        if usuario_id:
            query = query.filter(Log.usuario_id == usuario_id)
        if data_inicio:
            query = query.filter(Log.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(Log.data_hora <= data_fim)
        
        logs = query.order_by(Log.data_hora.desc()).limit(500).all()
        
        # Criar PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=cm, leftMargin=cm, 
                               topMargin=cm, bottomMargin=cm)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#25691b'),
            alignment=1,  # Center
            spaceAfter=20
        )
        
        # Conteúdo do PDF
        elements = []
        
        # Título
        title = Paragraph("Relatório de Auditoria - Embryotech", title_style)
        elements.append(title)
        
        # Informações do relatório
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
        
        # Tabela de dados
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
        
        # Gerar PDF
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
def api_exportar_leituras_pdf(current_user):
    """
    Exportar relatório de leituras em PDF
    ---
    tags:
      - Relatórios
    security:
      - Bearer: []
    parameters:
      - name: lote
        in: query
        type: string
        required: false
        description: Filtrar por lote
      - name: data_inicio
        in: query
        type: string
        format: date
        required: false
        description: Data inicial
      - name: data_fim
        in: query
        type: string
        format: date
        required: false
        description: Data final
    responses:
      200:
        description: Arquivo PDF gerado
        schema:
          type: file
      403:
        description: Acesso negado (apenas administradores)
      500:
        description: Erro ao gerar PDF
      401:
        description: Token inválido ou ausente
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        
        # Parâmetros de filtro
        lote = request.args.get('lote')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        # Consultar leituras
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
        
        # Criar PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=cm, leftMargin=cm, 
                               topMargin=cm, bottomMargin=cm)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#25691b'),
            alignment=1,  # Center
            spaceAfter=20
        )
        
        # Conteúdo do PDF
        elements = []
        
        # Título
        title = Paragraph("Relatório de Leituras - Embryotech", title_style)
        elements.append(title)
        
        # Informações do relatório
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
        
        # Tabela de dados
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
        
        # Gerar PDF
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
def api_alterar_senha_usuario(current_user, user_id):
    """
    Alterar senha de usuário (apenas admin)
    ---
    tags:
      - Usuários
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID do usuário
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            nova_senha:
              type: string
              example: "novaSenha123"
              description: Nova senha (mínimo 6 caracteres)
          required:
            - nova_senha
    responses:
      200:
        description: Senha alterada com sucesso
      400:
        description: Nova senha inválida
      403:
        description: Acesso negado (apenas administradores)
      404:
        description: Usuário não encontrado
      401:
        description: Token inválido ou ausente
    """
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
def api_alterar_privilegios_usuario(current_user, user_id):
    """
    Alterar privilégios de administrador
    ---
    tags:
      - Usuários
    security:
      - Bearer: []
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID do usuário
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            is_admin:
              type: boolean
              example: true
              description: True para promover a admin, false para remover
          required:
            - is_admin
    responses:
      200:
        description: Privilégios alterados com sucesso
      400:
        description: Não é possível remover próprios privilégios
      403:
        description: Acesso negado (apenas administradores)
      404:
        description: Usuário não encontrado
      401:
        description: Token inválido ou ausente
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    data = request.get_json()
    is_admin = data.get('is_admin', False)
    
    usuario = User.query.get(user_id)
    if not usuario:
        return jsonify({'message': 'Usuário não encontrado'}), 404
    
    # Evitar que o admin remova seu próprio privilégio
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
def api_exportar_usuarios_pdf(current_user):
    """
    Exportar relatório de usuários em PDF
    ---
    tags:
      - Relatórios
    security:
      - Bearer: []
    parameters:
      - name: tipo
        in: query
        type: string
        required: false
        enum: [admin, user]
        description: Filtrar por tipo de usuário
        example: "admin"
    responses:
      200:
        description: Arquivo PDF gerado
        schema:
          type: file
      403:
        description: Acesso negado (apenas administradores)
      500:
        description: Erro ao gerar PDF
      401:
        description: Token inválido ou ausente
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        import io
        
        # Parâmetro de filtro
        tipo_usuario = request.args.get('tipo')
        
        # Consultar usuários
        usuarios = User.query.all()
        
        # Filtrar por tipo se especificado
        if tipo_usuario == 'admin':
            usuarios = [u for u in usuarios if u.is_admin]
        elif tipo_usuario == 'user':
            usuarios = [u for u in usuarios if not u.is_admin]
        
        # Criar PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=cm, leftMargin=cm, 
                               topMargin=cm, bottomMargin=cm)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#25691b'),
            alignment=1,  # Center
            spaceAfter=20
        )
        
        # Conteúdo do PDF
        elements = []
        
        # Título
        title = Paragraph("Relatório de Usuários - Embryotech", title_style)
        elements.append(title)
        
        # Informações do relatório
        info_text = f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}<br/>"
        info_text += f"Total de registros: {len(usuarios)}<br/>"
        if tipo_usuario:
            tipo_desc = 'Administradores' if tipo_usuario == 'admin' else 'Usuários Comuns'
            info_text += f"Filtrado por tipo: {tipo_desc}<br/>"
        
        info_para = Paragraph(info_text, styles['Normal'])
        elements.append(info_para)
        elements.append(Spacer(1, 20))
        
        # Tabela de dados
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
        
        # Gerar PDF
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)