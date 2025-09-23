# models.py completo com Parametro e campo is_admin

from extensions import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, secret_key, expires_in=3600):
        return jwt.encode(
            {
                'id': self.id,
                'is_admin': self.is_admin,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in)
            },
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

class Leitura(db.Model):
    __tablename__ = 'leituras'

    id = db.Column(db.Integer, primary_key=True)
    umidade = db.Column(db.Float, nullable=True)
    temperatura = db.Column(db.Float, nullable=True)
    pressao = db.Column(db.Float, nullable=True)
    lote = db.Column(db.String(100), nullable=True)
    data_inicial = db.Column(db.DateTime, nullable=True)
    data_final = db.Column(db.DateTime, nullable=True)

class Parametro(db.Model):
    __tablename__ = 'parametros'

    id = db.Column(db.Integer, primary_key=True)
    pressao_ideal = db.Column(db.Float, nullable=False)
    temp_ideal = db.Column(db.Float, nullable=False)
    umid_ideal = db.Column(db.Float, nullable=False)
    lumens = db.Column(db.Float, nullable=True)
    empresa = db.Column(db.String(120), nullable=True)
    id_sala = db.Column(db.Integer, nullable=True)
    estagio_ovo = db.Column(db.String(50), nullable=True)
