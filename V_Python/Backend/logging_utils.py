# logging_utils.py - Sistema de logging para Embryotech

from functools import wraps
from flask import request, g
from models import Log, User
from extensions import db
import json
from datetime import datetime

def log_activity(acao_personalizada=None):
    """
    Decorator para logging automático de atividades
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Captura informações antes da execução
            start_time = datetime.utcnow()
            usuario = getattr(g, 'current_user', None)
            
            try:
                # Executa a função original
                result = f(*args, **kwargs)
                
                # Determina o status code baseado no resultado
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                elif isinstance(result, tuple) and len(result) > 1:
                    status_code = result[1]
                else:
                    status_code = 200
                
                # Define a ação baseada no decorator ou função
                if acao_personalizada:
                    acao = acao_personalizada
                else:
                    acao = f"{request.method} {request.endpoint or f.__name__}"
                
                # Captura dados da requisição para detalhes
                detalhes = capturar_detalhes_requisicao(f.__name__, args, kwargs)
                
                # Registra o log
                registrar_log_atividade(
                    usuario=usuario,
                    acao=acao,
                    detalhes=detalhes,
                    status_code=status_code,
                    duracao=datetime.utcnow() - start_time
                )
                
                return result
                
            except Exception as e:
                # Registra erro
                detalhes_erro = {
                    'erro': str(e),
                    'funcao': f.__name__,
                    'parametros': capturar_detalhes_requisicao(f.__name__, args, kwargs)
                }
                
                registrar_log_atividade(
                    usuario=usuario,
                    acao=f"ERRO: {acao_personalizada or f.__name__}",
                    detalhes=json.dumps(detalhes_erro, default=str),
                    status_code=500,
                    duracao=datetime.utcnow() - start_time
                )
                
                raise e
        
        return decorated_function
    return decorator

def capturar_detalhes_requisicao(func_name, args, kwargs):
    """
    Captura detalhes relevantes da requisição
    """
    detalhes = {
        'funcao': func_name,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Adiciona dados do JSON se houver
    if request.is_json and request.get_json():
        dados = request.get_json()
        # Remove senhas dos logs por segurança
        dados_seguros = {k: v for k, v in dados.items() if 'password' not in k.lower()}
        detalhes['dados_requisicao'] = dados_seguros
    
    # Adiciona parâmetros da URL
    if request.args:
        detalhes['parametros_url'] = dict(request.args)
    
    # Adiciona parâmetros da rota
    if kwargs:
        detalhes['parametros_rota'] = {k: v for k, v in kwargs.items() if not callable(v)}
    
    return json.dumps(detalhes, default=str)

def registrar_log_atividade(usuario=None, acao='', detalhes=None, status_code=200, duracao=None):
    """
    Registra atividade no banco de dados
    """
    try:
        # Adiciona duração aos detalhes se fornecida
        if duracao and detalhes:
            detalhes_dict = json.loads(detalhes) if isinstance(detalhes, str) else detalhes
            detalhes_dict['duracao_ms'] = int(duracao.total_seconds() * 1000)
            detalhes = json.dumps(detalhes_dict, default=str)
        
        log = Log(
            usuario_id=usuario.id if usuario else None,
            usuario_nome=usuario.username if usuario else 'Anônimo',
            acao=acao,
            detalhes=detalhes,
            endpoint=request.endpoint if request else None,
            metodo_http=request.method if request else None,
            ip_address=request.environ.get('HTTP_X_REAL_IP', request.remote_addr) if request else None,
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

def log_login_attempt(username, sucesso=True, motivo=None):
    """
    Log específico para tentativas de login
    """
    acao = "LOGIN_SUCESSO" if sucesso else "LOGIN_FALHOU"
    detalhes = {
        'username': username,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if motivo:
        detalhes['motivo'] = motivo
    
    registrar_log_atividade(
        usuario=None,
        acao=acao,
        detalhes=json.dumps(detalhes, default=str),
        status_code=200 if sucesso else 401
    )

def log_logout(usuario):
    """
    Log específico para logout
    """
    detalhes = {
        'username': usuario.username if usuario else 'Desconhecido',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    registrar_log_atividade(
        usuario=usuario,
        acao="LOGOUT",
        detalhes=json.dumps(detalhes, default=str),
        status_code=200
    )

def log_parametro_alteracao(usuario, parametro_id, dados_anteriores, dados_novos, operacao='UPDATE'):
    """
    Log específico para alterações de parâmetros
    """
    detalhes = {
        'parametro_id': parametro_id,
        'operacao': operacao,
        'dados_anteriores': dados_anteriores,
        'dados_novos': dados_novos,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    acao = f"PARAMETRO_{operacao}"
    
    registrar_log_atividade(
        usuario=usuario,
        acao=acao,
        detalhes=json.dumps(detalhes, default=str),
        status_code=200
    )

def log_acesso_tela(usuario, tela, detalhes_adicionais=None):
    """
    Log específico para acesso a telas
    """
    detalhes = {
        'tela': tela,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if detalhes_adicionais:
        detalhes.update(detalhes_adicionais)
    
    registrar_log_atividade(
        usuario=usuario,
        acao=f"ACESSO_TELA_{tela.upper()}",
        detalhes=json.dumps(detalhes, default=str),
        status_code=200
    )

def log_crud_operation(usuario, tabela, operacao, registro_id=None, dados=None):
    """
    Log específico para operações CRUD
    """
    detalhes = {
        'tabela': tabela,
        'operacao': operacao,
        'registro_id': registro_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if dados:
        # Remove campos sensíveis
        dados_seguros = {k: v for k, v in dados.items() if 'password' not in k.lower()}
        detalhes['dados'] = dados_seguros
    
    acao = f"{operacao.upper()}_{tabela.upper()}"
    
    registrar_log_atividade(
        usuario=usuario,
        acao=acao,
        detalhes=json.dumps(detalhes, default=str),
        status_code=200
    )