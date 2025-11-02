"""
Testes de API para endpoints de leituras
"""
import pytest
import json
from datetime import datetime
from models import Leitura


class TestLeiturasAPI:
    """Testes para endpoints de leituras"""
    
    def test_criar_leitura_sucesso(self, client, auth_headers_comum):
        """Testa criação bem-sucedida de leitura"""
        dados = {
            'umidade': 58.5,
            'temperatura': 37.2,
            'pressao': 1012.5,
            'lote': 'LOTE001',
            'data_inicial': '2024-01-01T10:00:00',
            'data_final': '2024-01-21T10:00:00'
        }
        
        response = client.post(
            '/api/leituras',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'message' in data
        
        # Verificar se foi criada no banco
        leitura = Leitura.query.filter_by(lote='LOTE001').first()
        assert leitura is not None
        assert leitura.umidade == 58.5
        assert leitura.temperatura == 37.2
    
    def test_criar_leitura_campos_minimos(self, client, auth_headers_comum):
        """Testa criação de leitura com campos mínimos"""
        dados = {
            'umidade': 60.0,
            'temperatura': 37.5
        }
        
        response = client.post(
            '/api/leituras',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 201
    
    def test_criar_leitura_todos_campos_opcionais(self, client, auth_headers_comum):
        """Testa criação de leitura com todos os campos"""
        dados = {
            'umidade': 59.2,
            'temperatura': 37.4,
            'pressao': 1012.8,
            'lote': 'LOTE_COMPLETO',
            'data_inicial': '2024-03-01T08:00:00',
            'data_final': '2024-03-21T08:00:00'
        }
        
        response = client.post(
            '/api/leituras',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 201
    
    def test_criar_leitura_sem_autenticacao(self, client):
        """Testa que criação de leitura requer autenticação"""
        dados = {
            'umidade': 60.0,
            'temperatura': 37.5
        }
        
        response = client.post(
            '/api/leituras',
            data=json.dumps(dados),
            content_type='application/json'
        )
        
        assert response.status_code == 401
    
    def test_listar_leituras(self, client, auth_headers_comum, multiplas_leituras):
        """Testa listagem de leituras"""
        response = client.get('/api/leituras', headers=auth_headers_comum)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
        assert len(data) == len(multiplas_leituras)
    
    def test_listar_leituras_vazio(self, client, auth_headers_comum, db_session):
        """Testa listagem de leituras quando não há dados"""
        response = client.get('/api/leituras', headers=auth_headers_comum)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_listar_leituras_formato_dados(self, client, auth_headers_comum, leitura_exemplo):
        """Testa formato dos dados retornados na listagem"""
        response = client.get('/api/leituras', headers=auth_headers_comum)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert len(data) > 0
        leitura = data[0]
        
        # Verificar campos presentes
        assert 'id' in leitura
        assert 'umidade' in leitura
        assert 'temperatura' in leitura
        assert 'pressao' in leitura
        assert 'lote' in leitura
    
    def test_atualizar_leitura_sucesso(self, client, auth_headers_comum, leitura_exemplo):
        """Testa atualização de leitura"""
        dados_atualizacao = {
            'umidade': 62.0,
            'temperatura': 38.0
        }
        
        response = client.put(
            f'/api/leituras/{leitura_exemplo.id}',
            data=json.dumps(dados_atualizacao),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 200
        
        # Verificar se foi atualizada no banco
        leitura = Leitura.query.get(leitura_exemplo.id)
        assert leitura.umidade == 62.0
        assert leitura.temperatura == 38.0
    
    def test_atualizar_leitura_inexistente(self, client, auth_headers_comum):
        """Testa atualização de leitura inexistente"""
        dados = {'umidade': 60.0}
        
        response = client.put(
            '/api/leituras/99999',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 404
    
    def test_atualizar_leitura_parcial(self, client, auth_headers_comum, leitura_exemplo):
        """Testa atualização parcial de leitura"""
        umidade_original = leitura_exemplo.umidade
        
        # Atualizar apenas temperatura
        dados = {'temperatura': 38.5}
        
        response = client.put(
            f'/api/leituras/{leitura_exemplo.id}',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 200
        
        # Verificar que umidade não mudou
        leitura = Leitura.query.get(leitura_exemplo.id)
        assert leitura.umidade == umidade_original
        assert leitura.temperatura == 38.5
    
    def test_deletar_leitura_sucesso(self, client, auth_headers_comum, leitura_exemplo):
        """Testa deleção de leitura"""
        leitura_id = leitura_exemplo.id
        
        response = client.delete(
            f'/api/leituras/{leitura_id}',
            headers=auth_headers_comum
        )
        
        assert response.status_code == 200
        
        # Verificar se foi deletada do banco
        leitura = Leitura.query.get(leitura_id)
        assert leitura is None
    
    def test_deletar_leitura_inexistente(self, client, auth_headers_comum):
        """Testa deleção de leitura inexistente"""
        response = client.delete(
            '/api/leituras/99999',
            headers=auth_headers_comum
        )
        
        assert response.status_code == 404
    
    def test_deletar_leitura_sem_autenticacao(self, client, leitura_exemplo):
        """Testa que deleção requer autenticação"""
        response = client.delete(f'/api/leituras/{leitura_exemplo.id}')
        
        assert response.status_code == 401


class TestLeiturasValidacao:
    """Testes de validação de dados de leituras"""
    
    def test_umidade_valores_validos(self, client, auth_headers_comum):
        """Testa se umidade aceita valores válidos"""
        # Valores extremos mas válidos
        for umidade in [0.0, 50.0, 100.0]:
            dados = {
                'umidade': umidade,
                'temperatura': 37.5
            }
            
            response = client.post(
                '/api/leituras',
                data=json.dumps(dados),
                headers=auth_headers_comum
            )
            
            assert response.status_code == 201
    
    def test_temperatura_valores_validos(self, client, auth_headers_comum):
        """Testa se temperatura aceita valores válidos"""
        for temperatura in [20.0, 37.5, 40.0]:
            dados = {
                'umidade': 60.0,
                'temperatura': temperatura
            }
            
            response = client.post(
                '/api/leituras',
                data=json.dumps(dados),
                headers=auth_headers_comum
            )
            
            assert response.status_code == 201
    
    def test_pressao_valores_validos(self, client, auth_headers_comum):
        """Testa se pressão aceita valores válidos"""
        dados = {
            'umidade': 60.0,
            'temperatura': 37.5,
            'pressao': 1013.25
        }
        
        response = client.post(
            '/api/leituras',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 201
    
    def test_lote_string(self, client, auth_headers_comum):
        """Testa se lote aceita string"""
        dados = {
            'umidade': 60.0,
            'temperatura': 37.5,
            'lote': 'LOTE_TESTE_123'
        }
        
        response = client.post(
            '/api/leituras',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 201
    
    def test_datas_formato_iso(self, client, auth_headers_comum):
        """Testa se datas aceitam formato ISO"""
        dados = {
            'umidade': 60.0,
            'temperatura': 37.5,
            'data_inicial': '2024-01-01T10:00:00',
            'data_final': '2024-01-21T10:00:00'
        }
        
        response = client.post(
            '/api/leituras',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 201


class TestLeiturasIntegracao:
    """Testes de integração de leituras"""
    
    def test_criar_e_listar_leitura(self, client, auth_headers_comum):
        """Testa criar uma leitura e depois listá-la"""
        # Criar leitura
        dados = {
            'umidade': 58.5,
            'temperatura': 37.2,
            'lote': 'LOTE_INTEGRACAO'
        }
        
        response_create = client.post(
            '/api/leituras',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response_create.status_code == 201
        
        # Listar leituras
        response_list = client.get('/api/leituras', headers=auth_headers_comum)
        
        assert response_list.status_code == 200
        data = json.loads(response_list.data)
        
        # Verificar se a leitura criada está na lista
        lotes = [l['lote'] for l in data]
        assert 'LOTE_INTEGRACAO' in lotes
    
    def test_criar_atualizar_e_deletar_leitura(self, client, auth_headers_comum):
        """Testa ciclo completo: criar, atualizar e deletar"""
        # 1. Criar
        dados_criar = {
            'umidade': 58.5,
            'temperatura': 37.2,
            'lote': 'LOTE_CICLO'
        }
        
        response_create = client.post(
            '/api/leituras',
            data=json.dumps(dados_criar),
            headers=auth_headers_comum
        )
        
        assert response_create.status_code == 201
        
        # Buscar ID da leitura criada
        leitura = Leitura.query.filter_by(lote='LOTE_CICLO').first()
        assert leitura is not None
        leitura_id = leitura.id
        
        # 2. Atualizar
        dados_atualizar = {'temperatura': 38.0}
        
        response_update = client.put(
            f'/api/leituras/{leitura_id}',
            data=json.dumps(dados_atualizar),
            headers=auth_headers_comum
        )
        
        assert response_update.status_code == 200
        
        # Verificar atualização
        leitura = Leitura.query.get(leitura_id)
        assert leitura.temperatura == 38.0
        
        # 3. Deletar
        response_delete = client.delete(
            f'/api/leituras/{leitura_id}',
            headers=auth_headers_comum
        )
        
        assert response_delete.status_code == 200
        
        # Verificar deleção
        leitura = Leitura.query.get(leitura_id)
        assert leitura is None
    
    def test_multiplos_usuarios_criam_leituras(self, client, auth_headers_comum, auth_headers_admin):
        """Testa que múltiplos usuários podem criar leituras"""
        # Usuário comum cria leitura
        dados1 = {
            'umidade': 58.0,
            'temperatura': 37.0,
            'lote': 'LOTE_USER1'
        }
        
        response1 = client.post(
            '/api/leituras',
            data=json.dumps(dados1),
            headers=auth_headers_comum
        )
        
        assert response1.status_code == 201
        
        # Admin cria leitura
        dados2 = {
            'umidade': 59.0,
            'temperatura': 38.0,
            'lote': 'LOTE_ADMIN'
        }
        
        response2 = client.post(
            '/api/leituras',
            data=json.dumps(dados2),
            headers=auth_headers_admin
        )
        
        assert response2.status_code == 201
        
        # Ambas devem estar no banco
        leitura1 = Leitura.query.filter_by(lote='LOTE_USER1').first()
        leitura2 = Leitura.query.filter_by(lote='LOTE_ADMIN').first()
        
        assert leitura1 is not None
        assert leitura2 is not None
