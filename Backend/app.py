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

# Configuração da porta
PORT = int(os.environ.get('PORT', 5001))  # Padrão 5001, mas pode ser sobrescrito

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)
swagger = Swagger(app)

# Importar models após inicializar db para evitar import circular
from models import User, Item

print("SECRET_KEY:", secrets.token_urlsafe(32))
print("JWT_SECRET_KEY:", secrets.token_hex(32))

# Decorator para rotas que requerem autenticação
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
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
    return "API rodando na porta {}".format(PORT)

@app.route('/register', methods=['POST'])
def register():
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
    item = Item.query.filter_by(id=item_id, created_by=current_user.id).first()
    
    if not item:
        return jsonify({'message': 'Item not found!'}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    return jsonify({'message': 'Item deleted successfully!'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)  # Mude para a porta desejada