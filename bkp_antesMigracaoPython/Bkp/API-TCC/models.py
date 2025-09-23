from extensions import db  # Ou from app import db, dependendo da sua estrutura
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash   
import jwt
from flask import request, jsonify
from functools import wraps
from flask import current_app

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_auth_token(self, secret_key, expires_in=3600):
        return jwt.encode(
            {'id': self.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_in)},
            secret_key,
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_auth_token(token, secret_key):
        try:
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            return User.query.get(data['id'])
        except:
            return None

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    
def generate_auth_token(self, expires_in=3600):
    payload = {
        'id': self.id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in)
    }
    return jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],  # Acessa a chave configurada
        algorithm='HS256'
    )

class Leitura(db.Model):
    __tablename__ = 'leituras'
    
    id = db.Column(db.Integer, primary_key=True)
    umidade = db.Column(db.Float, nullable=True)
    temperatura = db.Column(db.Float, nullable=True)
    pressao = db.Column(db.Float, nullable=True)
    lote = db.Column(db.String(100), nullable=True)
    data_inicial = db.Column(db.DateTime, nullable=True)
    data_final = db.Column(db.DateTime, nullable=True)