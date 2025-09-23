# models.py completo com Parametro, campo is_admin e modelo de Log

from extensions import db
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app, request

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
    id = db.Column(db.Integer, primary_key=True)
    empresa = db.Column(db.String(100), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    temp_ideal = db.Column(db.Float, nullable=False)
    umid_ideal = db.Column(db.Float, nullable=False)
    pressao_ideal = db.Column(db.Float)
    lumens = db.Column(db.Float)
    id_sala = db.Column(db.Integer)
    estagio_ovo = db.Column(db.String(50))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'empresa': self.empresa,
            'lote': self.lote,
            'temp_ideal': self.temp_ideal,
            'umid_ideal': self.umid_ideal,
            'pressao_ideal': self.pressao_ideal,
            'lumens': self.lumens,
            'id_sala': self.id_sala,
            'estagio_ovo': self.estagio_ovo,
            'data_criacao': self.data_criacao.isoformat()
        }

class Log(db.Model):
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    usuario_nome = db.Column(db.String(80), nullable=True)
    acao = db.Column(db.String(100), nullable=False)
    detalhes = db.Column(db.Text, nullable=True)
    endpoint = db.Column(db.String(200), nullable=True)
    metodo_http = db.Column(db.String(10), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    status_code = db.Column(db.Integer, nullable=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com User
    usuario = db.relationship('User', backref=db.backref('logs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'usuario_nome': self.usuario_nome,
            'acao': self.acao,
            'detalhes': self.detalhes,
            'endpoint': self.endpoint,
            'metodo_http': self.metodo_http,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status_code': self.status_code,
            'data_hora': self.data_hora.isoformat() if self.data_hora else None
        }

    @staticmethod
    def registrar_log(usuario=None, acao='', detalhes=None, status_code=200):
        """
        Método estático para registrar logs facilmente
        """
        try:
            log = Log(
                usuario_id=usuario.id if usuario else None,
                usuario_nome=usuario.username if usuario else None,
                acao=acao,
                detalhes=detalhes,
                endpoint=request.endpoint if request else None,
                metodo_http=request.method if request else None,
                ip_address=request.remote_addr if request else None,
                user_agent=request.headers.get('User-Agent', '') if request else None,
                status_code=status_code
            )
            
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f"Erro ao registrar log: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass