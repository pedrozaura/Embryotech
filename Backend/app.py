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

# Configuração da porta
PORT = int(os.environ.get('PORT', 5001))  # Padrão 5001, mas pode ser sobrescrito

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

# Adicione esta configuração do Swagger antes das rotas
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Embryotech API  --  Outside Agrotech",
        "description": "API para gerenciamento de usuários, itens e leituras de embriões",
        "contact": {
            "email": "pedro.zaura@outsideagro.tech"
        },
        "version": "1.0.1"
    },
    "basePath": "/",
    "schemes": [
        "http",
        "https"
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
            "mensagem": "Bem-vindo ao Backend do Sistema embryotech",
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

# Rotas CRUD para Items
@app.route('/items', methods=['GET'])
@token_required
def get_all_items(current_user):
    """
    Listar todos os itens do usuário
    ---
    tags:
      - Itens
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de itens
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                $ref: '#/definitions/Item'
      401:
        description: Token inválido ou faltando
    definitions:
      Item:
        type: object
        properties:
          id:
            type: integer
            example: 1
          name:
            type: string
            example: "Item exemplo"
          description:
            type: string
            example: "Descrição do item"
    """
    items = Item.query.filter_by(created_by=current_user.id).all()
    
    output = []
    for item in items:
        item_data = {
            'id': item.id,
            'name': item.name,
            'description': item.description
        }
        output.append(item_data)
    
    return jsonify({'items': output}), 200

@app.route('/items/<int:item_id>', methods=['GET'])
@token_required
def get_one_item(current_user, item_id):
    """
    Obter detalhes de um item específico
    ---
    tags:
      - Itens
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        type: integer
        required: true
        description: ID do item a ser recuperado
        example: 1
    responses:
      200:
        description: Detalhes do item
        schema:
          type: object
          properties:
            item:
              $ref: '#/definitions/Item'
      401:
        description: Token inválido ou faltando
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Token é invalido!"
      404:
        description: Item não encontrado
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Item não encontrado!"
    """
    item = Item.query.filter_by(id=item_id, created_by=current_user.id).first()
    
    if not item:
        return jsonify({'message': 'Item not found!'}), 404
    
    item_data = {
        'id': item.id,
        'name': item.name,
        'description': item.description
    }
    
    return jsonify({'item': item_data}), 200

@app.route('/items', methods=['POST'])
@token_required
def create_item(current_user):
    """
    Criar novo item
    ---
    tags:
      - Itens
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          id: NewItem
          required:
            - name
          properties:
            name:
              type: string
              example: "Novo item"
            description:
              type: string
              example: "Descrição opcional"
    responses:
      201:
        description: Item criado com sucesso
      400:
        description: Nome do item faltando
      401:
        description: Token inválido ou faltando
    """
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'message': 'Name is required!'}), 400
    
    new_item = Item(
        name=data['name'],
        description=data.get('description', ''),
        created_by=current_user.id
    )
    
    db.session.add(new_item)
    db.session.commit()
    
    return jsonify({'message': 'Item created successfully!'}), 201

@app.route('/items/<int:item_id>', methods=['PUT'])
@token_required
def update_item(current_user, item_id):
    """
    Atualizar um item específico
    ---
    tags:
      - Itens
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        type: integer
        required: true
        description: ID do item a ser atualizado
        example: 1
      - in: body
        name: body
        required: true
        schema:
          id: ItemUpdate
          properties:
            name:
              type: string
              example: "Novo nome do item"
              description: Novo nome para o item (opcional)
            description:
              type: string
              example: "Nova descrição detalhada"
              description: Nova descrição para o item (opcional)
    responses:
      200:
        description: Item atualizado com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Item atualizado com sucesso!"
      400:
        description: Nenhum campo válido fornecido para atualização
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Não existem campos validos para atualizar!"
      401:
        description: Token inválido ou faltando
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Token é invalido!"
      404:
        description: Item não encontrado
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Item não encontrado!"
    """
    item = Item.query.filter_by(id=item_id, created_by=current_user.id).first()
    
    if not item:
        return jsonify({'message': 'Item not found!'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        item.name = data['name']
    if 'description' in data:
        item.description = data['description']
    
    db.session.commit()
    
    return jsonify({'message': 'Item updated successfully!'}), 200

@app.route('/items/<int:item_id>', methods=['DELETE'])
@token_required
def delete_item(current_user, item_id):
    """
    Deletar um item específico
    ---
    tags:
      - Itens
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        type: integer
        required: true
        description: ID do item a ser deletado
        example: 1
    responses:
      200:
        description: Item deletado com sucesso
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Item Deletado com Sucesso!"
      401:
        description: Token inválido ou faltando
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Token é invalido!"
      404:
        description: Item não encontrado
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Item não encontrado!"
    """
    item = Item.query.filter_by(id=item_id, created_by=current_user.id).first()
    
    if not item:
        return jsonify({'message': 'Item not found!'}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Item deleted successfully!'}), 200

@app.route('/leituras', methods=['POST'])
@token_required
def criar_leitura(current_user):
    """
    Criar nova leitura de embrião
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
          id: NewLeitura
          properties:
            umidade:
              type: float
              example: 65.5
            temperatura:
              type: float
              example: 36.7
            pressao:
              type: float
              example: 1.2
            lote:
              type: string
              example: "Lote A"
            data_inicial:
              type: string
              format: date-time
              example: "2023-05-20T10:30:00"
            data_final:
              type: string
              format: date-time
              example: "2023-05-21T10:30:00"
    responses:
      201:
        description: Leitura criada com sucesso
      401:
        description: Token inválido ou faltando
    """
    data = request.get_json()
    nova = Leitura(
        umidade=data.get('umidade'),
        temperatura=data.get('temperatura'),
        pressao=data.get('pressao'),
        lote=data.get('lote'),
        data_inicial=data.get('data_inicial'),
        data_final=data.get('data_final')
    )
    db.session.add(nova)
    db.session.commit()
    return jsonify({'message': 'Leitura criada com sucesso'}), 201

@app.route('/leituras', methods=['GET'])
@token_required
def listar_leituras(current_user):
    """
    Listar todas as leituras
    ---
    tags:
      - Leituras
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de leituras
        schema:
          type: array
          items:
            $ref: '#/definitions/Leitura'
      401:
        description: Token inválido ou faltando
    definitions:
      Leitura:
        type: object
        properties:
          id:
            type: integer
            example: 1
          umidade:
            type: float
            example: 65.5
          temperatura:
            type: float
            example: 36.7
          pressao:
            type: float
            example: 1.2
          lote:
            type: string
            example: "Lote A"
          data_inicial:
            type: string
            format: date-time
            example: "2023-05-20T10:30:00"
          data_final:
            type: string
            format: date-time
            example: "2023-05-21T10:30:00"
    """     
    leituras = Leitura.query.all()
    retorno = []
    for l in leituras:
        retorno.append({
            'id': l.id,
            'umidade': l.umidade,
            'temperatura': l.temperatura,
            'pressao': l.pressao,
            'lote': l.lote,
            'data_inicial': l.data_inicial,
            'data_final': l.data_final
        })
    return jsonify(retorno), 200

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

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])