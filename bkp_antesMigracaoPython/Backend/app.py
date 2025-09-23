from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash
import jwt
import datetime
from functools import wraps
from config import Config
from flask_cors import CORS
from extensions import db, migrate
from flasgger import Swagger
import secrets
import os
from flask import redirect, url_for

from sqlalchemy.sql import text
from datetime import timedelta

from models import User, Item, Leitura, Parametro

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

db.init_app(app)
migrate.init_app(app, db)

# Adicione esta configuração do Swagger antes das rotas
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Embryotech API  --  Outside Agrotech",
        "description": "API para gerenciamento de usuários, parâmetros e leituras de embriões",
        "contact": {
            "email": "pedro.zaura@outsideagro.tech"
        },
        "version": "1.0.1"
    },
    "basePath": "/",
    "schemes": [
        "http"
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: \"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\""
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ]
}


swagger = Swagger(app, template=swagger_template)

# Importar models após inicializar db para evitar import circular
from models import User, Item, Leitura


#print("SECRET_KEY:", secrets.token_urlsafe(32))
#print("JWT_SECRET_KEY:", secrets.token_hex(32))



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
        except Exception as e:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Rotas de autenticação
@app.route('/')
def hello():
    """
    Endpoint de status da API
    ---
    responses:
      200:
        description: Exibe mensagem de boas-vindas e data/hora do servidor
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

@app.route('/register', methods=['POST'])
def register():
    """
    Registrar novo usuário
    ---
    tags:
      - Autenticação
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: UserRegistration
          required:
            - username
            - password
            - email
          properties:
            username:
              type: string
              example: "usuario1"
            password:
              type: string
              example: "senhasegura123"
            email:
              type: string
              example: "usuario@email.com"
    responses:
      201:
        description: Usuário registrado com sucesso
      400:
        description: Campos obrigatórios faltando ou usuário/email já existente
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'message': 'Missing required fields!'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists!'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists!'}), 400
    
    new_user = User(
        username=data['username'],
        email=data['email']
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Login de usuário
    ---
    tags:
      - Autenticação
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: UserLogin
          required:
            - username
            - password
          properties:
            username:
              type: string
              example: "usuario1"
            password:
              type: string
              example: "senhasegura123"
    responses:
      200:
        description: Login bem-sucedido
        schema:
          properties:
            token:
              type: string
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      400:
        description: Campos obrigatórios faltando
      401:
        description: Credenciais inválidas
    """
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password!'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid username or password!'}), 401
    
    token = user.generate_auth_token(app.config['JWT_SECRET_KEY'])
    
    return jsonify({'token': token}), 200

# # Rotas CRUD para Items
# @app.route('/items', methods=['GET'])
# @token_required
# def get_all_items(current_user):
    # """
    # Listar todos os itens do usuário
    # ---
    # tags:
      # - Itens
    # security:
      # - Bearer: []
    # responses:
      # 200:
        # description: Lista de itens
        # schema:
          # type: object
          # properties:
            # items:
              # type: array
              # items:
                # $ref: '#/definitions/Item'
      # 401:
        # description: Token inválido ou faltando
    # definitions:
      # Item:
        # type: object
        # properties:
          # id:
            # type: integer
            # example: 1
          # name:
            # type: string
            # example: "Item exemplo"
          # description:
            # type: string
            # example: "Descrição do item"
    # """
    # items = Item.query.filter_by(created_by=current_user.id).all()
    
    # output = []
    # for item in items:
        # item_data = {
            # 'id': item.id,
            # 'name': item.name,
            # 'description': item.description
        # }
        # output.append(item_data)
    
    # return jsonify({'items': output}), 200

# @app.route('/items/<int:item_id>', methods=['GET'])
# @token_required
# def get_one_item(current_user, item_id):
    # """
    # Obter detalhes de um item específico
    # ---
    # tags:
      # - Itens
    # security:
      # - Bearer: []
    # parameters:
      # - name: item_id
        # in: path
        # type: integer
        # required: true
        # description: ID do item a ser recuperado
        # example: 1
    # responses:
      # 200:
        # description: Detalhes do item
        # schema:
          # type: object
          # properties:
            # item:
              # $ref: '#/definitions/Item'
      # 401:
        # description: Token inválido ou faltando
        # schema:
          # type: object
          # properties:
            # message:
              # type: string
              # example: "Token é invalido!"
      # 404:
        # description: Item não encontrado
        # schema:
          # type: object
          # properties:
            # message:
              # type: string
              # example: "Item não encontrado!"
    # """
    # item = Item.query.filter_by(id=item_id, created_by=current_user.id).first()
    
    # if not item:
        # return jsonify({'message': 'Item not found!'}), 404
    
    # item_data = {
        # 'id': item.id,
        # 'name': item.name,
        # 'description': item.description
    # }
    
    # return jsonify({'item': item_data}), 200

# @app.route('/items', methods=['POST'])
# @token_required
# def create_item(current_user):
    # """
    # Criar novo item
    # ---
    # tags:
      # - Itens
    # security:
      # - Bearer: []
    # parameters:
      # - in: body
        # name: body
        # required: true
        # schema:
          # id: NewItem
          # required:
            # - name
          # properties:
            # name:
              # type: string
              # example: "Novo item"
            # description:
              # type: string
              # example: "Descrição opcional"
    # responses:
      # 201:
        # description: Item criado com sucesso
      # 400:
        # description: Nome do item faltando
      # 401:
        # description: Token inválido ou faltando
    # """
    # data = request.get_json()
    
    # if not data or not data.get('name'):
        # return jsonify({'message': 'Name is required!'}), 400
    
    # new_item = Item(
        # name=data['name'],
        # description=data.get('description', ''),
        # created_by=current_user.id
    # )
    
    # db.session.add(new_item)
    # db.session.commit()
    
    # return jsonify({'message': 'Item created successfully!'}), 201

# @app.route('/items/<int:item_id>', methods=['PUT'])
# @token_required
# def update_item(current_user, item_id):
    # """
    # Atualizar um item específico
    # ---
    # tags:
      # - Itens
    # security:
      # - Bearer: []
    # parameters:
      # - name: item_id
        # in: path
        # type: integer
        # required: true
        # description: ID do item a ser atualizado
        # example: 1
      # - in: body
        # name: body
        # required: true
        # schema:
          # id: ItemUpdate
          # properties:
            # name:
              # type: string
              # example: "Novo nome do item"
              # description: Novo nome para o item (opcional)
            # description:
              # type: string
              # example: "Nova descrição detalhada"
              # description: Nova descrição para o item (opcional)
    # responses:
      # 200:
        # description: Item atualizado com sucesso
        # schema:
          # type: object
          # properties:
            # message:
              # type: string
              # example: "Item atualizado com sucesso!"
      # 400:
        # description: Nenhum campo válido fornecido para atualização
        # schema:
          # type: object
          # properties:
            # message:
              # type: string
              # example: "Não existem campos validos para atualizar!"
      # 401:
        # description: Token inválido ou faltando
        # schema:
          # type: object
          # properties:
            # message:
              # type: string
              # example: "Token é invalido!"
      # 404:
        # description: Item não encontrado
        # schema:
          # type: object
          # properties:
            # message:
              # type: string
              # example: "Item não encontrado!"
    # """
    # item = Item.query.filter_by(id=item_id, created_by=current_user.id).first()
    
    # if not item:
        # return jsonify({'message': 'Item not found!'}), 404
    
    # data = request.get_json()
    
    # if 'name' in data:
        # item.name = data['name']
    # if 'description' in data:
        # item.description = data['description']
    
    # db.session.commit()
    
    # return jsonify({'message': 'Item updated successfully!'}), 200

# @app.route('/items/<int:item_id>', methods=['DELETE'])
# @token_required
# def delete_item(current_user, item_id):
    # """
    # Deletar um item específico
    # ---
    # tags:
      # - Itens
    # security:
      # - Bearer: []
    # parameters:
      # - name: item_id
        # in: path
        # type: integer
        # required: true
        # description: ID do item a ser deletado
        # example: 1
    # responses:
      # 200:
        # description: Item deletado com sucesso
        # schema:
          # type: object
          # properties:
            # message:
              # type: string
              # example: "Item Deletado com Sucesso!"
      # 401:
        # description: Token inválido ou faltando
        # schema:
          # type: object
          # properties:
            # message:
              # type: string
              # example: "Token é invalido!"
      # 404:
        # description: Item não encontrado
        # schema:
          # type: object
          # properties:
            # message:
              # type: string
              # example: "Item não encontrado!"
    # """
    # item = Item.query.filter_by(id=item_id, created_by=current_user.id).first()
    
    # if not item:
        # return jsonify({'message': 'Item not found!'}), 404
    
    # db.session.delete(item)
    # db.session.commit()
    
    # return jsonify({'message': 'Item deleted successfully!'}), 200

@app.route('/leituras', methods=['POST'])
@token_required
def criar_leitura(current_user):
    """
    Criar novas leituras de embrião (suporte a múltiplas leituras)
    ---
    tags:
      - Leituras
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: array
          items:
            $ref: '#/definitions/Leitura'
    responses:
      201:
        description: Leituras criadas com sucesso
      400:
        description: Dados inválidos
      401:
        description: Token inválido ou faltando
    """
    try:
        if not request.is_json:
            return jsonify({'message': 'O corpo da requisição deve ser JSON'}), 400
            
        data = request.get_json()
        
        # Se não for uma lista, converte para lista de um item
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
        
        return jsonify({
            'message': f'{len(leituras)} leituras criadas com sucesso',
            'quantidade': len(leituras)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao processar os dados: {str(e)}'}), 400

@app.route('/leituras', methods=['GET'])
@token_required
def listar_leituras(current_user):
    """
    Listar todas as leituras de embriões
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
        description: Filtro opcional para buscar leituras de um lote específico
        example: "LOTE-2024-XYZ"
    responses:
      200:
        description: Lista de leituras encontradas
        schema:
          type: array
          items:
            $ref: '#/definitions/Leitura'
      401:
        description: Token inválido ou ausente
    definitions:
      Leitura:
        type: object
        properties:
          id:
            type: integer
            example: 1
          umidade:
            type: number
            format: float
            example: 65.0
          temperatura:
            type: number
            format: float
            example: 37.5
          pressao:
            type: number
            format: float
            example: 1013.2
          lote:
            type: string
            example: "LOTE-2024-XYZ"
          data_inicial:
            type: string
            format: date-time
            example: "2025-07-10T08:00:00"
          data_final:
            type: string
            format: date-time
            example: "2025-07-10T09:00:00"
    """
    lote = request.args.get('lote')
    
    # Debug: Log do parâmetro recebido
    #current_app.logger.info(f"Filtrando leituras pelo lote: {lote}")
    
    query = Leitura.query
    
    if lote:
        query = query.filter(Leitura.lote == lote)
    
    leituras = query.order_by(Leitura.data_inicial.desc()).all()
    
    # Debug: Log da quantidade de leituras encontradas
    #current_app.logger.info(f"Leituras encontradas: {len(leituras)}")
    
    return jsonify([{
        'id': l.id,
        'umidade': l.umidade,
        'temperatura': l.temperatura,
        'pressao': l.pressao,
        'lote': l.lote,
        'data_inicial': l.data_inicial.isoformat() if l.data_inicial else None,
        'data_final': l.data_final.isoformat() if l.data_final else None
    } for l in leituras]), 200

@app.route('/leituras/<int:leitura_id>', methods=['PUT'])
@token_required
def atualizar_leitura(current_user, leitura_id):
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
        example: 1
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/Leitura'
    responses:
      200:
        description: Leitura atualizada com sucesso
      401:
        description: Token inválido ou faltando
      404:
        description: Leitura não encontrada
    """
    
    leitura = Leitura.query.get(leitura_id)
    if not leitura:
        return jsonify({'message': 'Leitura não encontrada'}), 404

    data = request.get_json()
    leitura.umidade = data.get('umidade', leitura.umidade)
    leitura.temperatura = data.get('temperatura', leitura.temperatura)
    leitura.pressao = data.get('pressao', leitura.pressao)
    leitura.lote = data.get('lote', leitura.lote)
    leitura.data_inicial = data.get('data_inicial', leitura.data_inicial)
    leitura.data_final = data.get('data_final', leitura.data_final)

    db.session.commit()
    return jsonify({'message': 'Leitura atualizada com sucesso'}), 200

@app.route('/leituras/<int:leitura_id>', methods=['DELETE'])
@token_required
def deletar_leitura(current_user, leitura_id):
    """
    Deletar uma leitura existente
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
        example: 1
    responses:
      200:
        description: Leitura deletada com sucesso
      401:
        description: Token inválido ou faltando
      404:
        description: Leitura não encontrada
    """
    leitura = Leitura.query.get(leitura_id)
    if not leitura:
        return jsonify({'message': 'Leitura não encontrada'}), 404

    db.session.delete(leitura)
    db.session.commit()
    return jsonify({'message': 'Leitura deletada com sucesso'}), 200

@app.route('/parametros', methods=['POST'])
@token_required
def criar_parametro(current_user):
    """
    Criar novo conjunto de parâmetros ideais
    ---
    tags:
      - Parâmetros
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: ParametroInput
          required:
            - empresa
            - lote
            - temp_ideal
            - umid_ideal
          properties:
            empresa:
              type: string
              example: "Outside Agrotech"
              description: Nome da empresa responsável pelo lote
            lote:
              type: string
              example: "LOTE-2023-001"
              description: Identificação única do lote
            temp_ideal:
              type: number
              format: float
              example: 37.5
              description: Temperatura ideal em graus Celsius
            umid_ideal:
              type: number
              format: float
              example: 65.0
              description: Umidade ideal em porcentagem
            pressao_ideal:
              type: number
              format: float
              example: 1013.25
              description: Pressão atmosférica ideal em hPa
            lumens:
              type: number
              format: float
              example: 400.0
              description: Intensidade luminosa ideal em lumens
            id_sala:
              type: integer
              example: 3
              description: Identificação da sala/incubadora
            estagio_ovo:
              type: string
              example: "Desenvolvimento"
              description: Estágio de desenvolvimento dos ovos
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
              $ref: '#/definitions/Parametro'
      400:
        description: Requisição malformada ou campos obrigatórios faltando
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Empresa, lote, temperatura e umidade são obrigatórios"
      401:
        description: Token inválido ou ausente
      403:
        description: Acesso não autorizado para usuário não-admin
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403

    data = request.get_json()
    try:
        # Validação dos campos obrigatórios
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
        return jsonify({
            'message': 'Parâmetro criado com sucesso!',
            'parametro': novo_parametro.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao salvar parâmetro: {str(e)}'}), 400

@app.route('/empresas', methods=['GET'])
@token_required
def get_empresas(current_user):
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
            example: "Outside Agrotech"
      401:
        description: Token inválido ou ausente
      403:
        description: Acesso não autorizado para usuário não-admin
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403
    
    empresas = db.session.query(Parametro.empresa).distinct().all()
    return jsonify([e[0] for e in empresas if e[0]]), 200

@app.route('/lotes', methods=['GET'])
@token_required
def get_lotes(current_user):
    """
    Obter lista de todos os lotes (ou filtrado por empresa)
    ---
    tags:
      - Parâmetros
    parameters:
      - name: empresa
        in: query
        type: string
        required: false
        description: Nome da empresa para filtrar os lotes
    responses:
      200:
        description: Lista de lotes
        schema:
          type: array
          items:
            type: string
            example: "LOTE-2023-001"
    """
    empresa = request.args.get('empresa')
    
    query = db.session.query(Parametro.lote).distinct()
    if empresa:
        query = query.filter_by(empresa=empresa)
    
    lotes = query.all()
    return jsonify([l[0] for l in lotes if l[0]]), 200


@app.route('/parametros', methods=['GET'])
@token_required
def get_parametros(current_user):
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
      - name: lote
        in: query
        type: string
        required: true
        description: Identificação do lote
    responses:
      200:
        description: Lista de parâmetros encontrados
        schema:
          type: array
          items:
            $ref: '#/definitions/Parametro'
      400:
        description: Empresa ou lote não especificados
      401:
        description: Token inválido
      403:
        description: Acesso não autorizado para usuários não-admin
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403

    empresa = request.args.get('empresa')
    lote = request.args.get('lote')

    if not empresa or not lote:
        return jsonify({'message': 'Empresa e lote são obrigatórios'}), 400

    parametros = Parametro.query.filter_by(empresa=empresa, lote=lote).all()

    return jsonify([p.to_dict() for p in parametros]), 200

@app.route('/parametros/<int:id>', methods=['PUT'])
@token_required
def atualizar_parametro(current_user, id):
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
        description: ID do parâmetro a ser atualizado
      - in: body
        name: body
        required: true
        schema:
          id: ParametroUpdate
          properties:
            empresa:
              type: string
              example: "Outside Agrotech"
            lote:
              type: string
              example: "LOTE-2023-001"
            temp_ideal:
              type: number
              format: float
              example: 37.5
            umid_ideal:
              type: number
              format: float
              example: 65.0
            pressao_ideal:
              type: number
              format: float
              example: 1013.25
            lumens:
              type: number
              format: float
              example: 400.0
            id_sala:
              type: integer
              example: 3
            estagio_ovo:
              type: string
              example: "Desenvolvimento"
    responses:
      200:
        description: Parâmetro atualizado com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Parâmetro atualizado com sucesso!"
            parametro:
              $ref: '#/definitions/Parametro'
      400:
        description: Requisição malformada
      401:
        description: Token inválido ou ausente
      403:
        description: Acesso não autorizado para usuário não-admin
      404:
        description: Parâmetro não encontrado
    """
    if not current_user.is_admin:
        return jsonify({'message': 'Acesso negado!'}), 403

    parametro = Parametro.query.get(id)
    if not parametro:
        return jsonify({'message': 'Parâmetro não encontrado'}), 404

    data = request.get_json()
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
        return jsonify({
            'message': 'Parâmetro atualizado com sucesso!',
            'parametro': parametro.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Erro ao atualizar parâmetro: {str(e)}'}), 400



if __name__ == '__main__':
    # app.run(debug=app.config['DEBUG'])
    app.run(host='0.0.0.0', port=9001, debug=True)