"""
Testes de API para endpoints de parâmetros
"""
import pytest
import json
from models import Parametro


class TestParametrosAPI:
    """Testes para endpoints de parâmetros"""
    
    def test_criar_parametro_sucesso(self, client, auth_headers_admin):
        """Testa criação bem-sucedida de parâmetro"""
        dados = {
            'empresa': 'Empresa Nova',
            'lote': 'LOTE123',
            'temp_ideal': 37.5,
            'umid_ideal': 60.0,
            'pressao_ideal': 1013.25,
            'lumens': 500.0,
            'id_sala': 1,
            'estagio_ovo': 'Inicial'
        }
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'message' in data
        assert 'parametro' in data
        assert data['parametro']['empresa'] == 'Empresa Nova'
    
    def test_criar_parametro_campos_obrigatorios_faltando(self, client, auth_headers_admin):
        """Testa criação de parâmetro sem campos obrigatórios"""
        dados = {
            'empresa': 'Empresa',
            # Faltando lote, temp_ideal, umid_ideal
        }
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 400
    
    def test_criar_parametro_apenas_obrigatorios(self, client, auth_headers_admin):
        """Testa criação de parâmetro apenas com campos obrigatórios"""
        dados = {
            'empresa': 'Empresa Mínima',
            'lote': 'LOTE_MIN',
            'temp_ideal': 37.5,
            'umid_ideal': 60.0
        }
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['parametro']['empresa'] == 'Empresa Mínima'
    
    def test_criar_parametro_usuario_comum_negado(self, client, auth_headers_comum):
        """Testa que usuário comum não pode criar parâmetro"""
        dados = {
            'empresa': 'Empresa',
            'lote': 'LOTE',
            'temp_ideal': 37.5,
            'umid_ideal': 60.0
        }
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 403
    
    def test_listar_empresas(self, client, auth_headers_admin, multiplos_parametros):
        """Testa listagem de empresas"""
        response = client.get('/api/empresas', headers=auth_headers_admin)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
        assert 'Empresa A' in data
        assert 'Empresa B' in data
    
    def test_listar_empresas_usuario_comum_negado(self, client, auth_headers_comum):
        """Testa que usuário comum não pode listar empresas"""
        response = client.get('/api/empresas', headers=auth_headers_comum)
        
        assert response.status_code == 403
    
    def test_listar_lotes(self, client, auth_headers_comum, multiplos_parametros):
        """Testa listagem de lotes"""
        response = client.get('/api/lotes', headers=auth_headers_comum)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_listar_lotes_filtrado_por_empresa(self, client, auth_headers_comum, multiplos_parametros):
        """Testa listagem de lotes filtrado por empresa"""
        response = client.get(
            '/api/lotes?empresa=Empresa A',
            headers=auth_headers_comum
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Deve retornar apenas lotes da Empresa A
        assert 'LOTE_A1' in data
        assert 'LOTE_A2' in data
        assert 'LOTE_B1' not in data
    
    def test_buscar_parametros_sucesso(self, client, auth_headers_admin, parametro_exemplo):
        """Testa busca de parâmetros por empresa e lote"""
        response = client.get(
            f'/api/parametros?empresa={parametro_exemplo.empresa}&lote={parametro_exemplo.lote}',
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]['empresa'] == parametro_exemplo.empresa
        assert data[0]['lote'] == parametro_exemplo.lote
    
    def test_buscar_parametros_sem_empresa_ou_lote(self, client, auth_headers_admin):
        """Testa busca de parâmetros sem empresa ou lote"""
        # Sem empresa
        response = client.get(
            '/api/parametros?lote=LOTE',
            headers=auth_headers_admin
        )
        assert response.status_code == 400
        
        # Sem lote
        response = client.get(
            '/api/parametros?empresa=Empresa',
            headers=auth_headers_admin
        )
        assert response.status_code == 400
    
    def test_buscar_parametros_usuario_comum_negado(self, client, auth_headers_comum):
        """Testa que usuário comum não pode buscar parâmetros"""
        response = client.get(
            '/api/parametros?empresa=Empresa&lote=LOTE',
            headers=auth_headers_comum
        )
        
        assert response.status_code == 403
    
    def test_atualizar_parametro_sucesso(self, client, auth_headers_admin, parametro_exemplo):
        """Testa atualização de parâmetro"""
        dados_atualizacao = {
            'temp_ideal': 38.0,
            'umid_ideal': 62.0
        }
        
        response = client.put(
            f'/api/parametros/{parametro_exemplo.id}',
            data=json.dumps(dados_atualizacao),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['parametro']['temp_ideal'] == 38.0
        assert data['parametro']['umid_ideal'] == 62.0
    
    def test_atualizar_parametro_inexistente(self, client, auth_headers_admin):
        """Testa atualização de parâmetro inexistente"""
        dados = {'temp_ideal': 38.0}
        
        response = client.put(
            '/api/parametros/99999',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 404
    
    def test_atualizar_parametro_usuario_comum_negado(self, client, auth_headers_comum, parametro_exemplo):
        """Testa que usuário comum não pode atualizar parâmetro"""
        dados = {'temp_ideal': 38.0}
        
        response = client.put(
            f'/api/parametros/{parametro_exemplo.id}',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 403
    
    def test_atualizar_parametro_parcial(self, client, auth_headers_admin, parametro_exemplo):
        """Testa atualização parcial de parâmetro"""
        temp_original = parametro_exemplo.temp_ideal
        
        # Atualizar apenas umidade
        dados = {'umid_ideal': 65.0}
        
        response = client.put(
            f'/api/parametros/{parametro_exemplo.id}',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Temperatura deve permanecer igual
        assert data['parametro']['temp_ideal'] == temp_original
        # Umidade deve ser atualizada
        assert data['parametro']['umid_ideal'] == 65.0
    
    def test_atualizar_todos_campos_parametro(self, client, auth_headers_admin, parametro_exemplo):
        """Testa atualização de todos os campos de um parâmetro"""
        dados = {
            'empresa': 'Nova Empresa',
            'lote': 'NOVO_LOTE',
            'temp_ideal': 38.5,
            'umid_ideal': 65.0,
            'pressao_ideal': 1015.0,
            'lumens': 600.0,
            'id_sala': 2,
            'estagio_ovo': 'Final'
        }
        
        response = client.put(
            f'/api/parametros/{parametro_exemplo.id}',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['parametro']['empresa'] == 'Nova Empresa'
        assert data['parametro']['lote'] == 'NOVO_LOTE'
        assert data['parametro']['temp_ideal'] == 38.5


class TestParametrosValidacao:
    """Testes de validação de dados de parâmetros"""
    
    def test_temperatura_ideal_tipo_correto(self, client, auth_headers_admin):
        """Testa se temperatura ideal aceita tipo correto"""
        dados = {
            'empresa': 'Empresa',
            'lote': 'LOTE',
            'temp_ideal': 37.5,  # float
            'umid_ideal': 60.0
        }
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 201
    
    def test_umidade_ideal_tipo_correto(self, client, auth_headers_admin):
        """Testa se umidade ideal aceita tipo correto"""
        dados = {
            'empresa': 'Empresa',
            'lote': 'LOTE',
            'temp_ideal': 37.5,
            'umid_ideal': 60.0  # float
        }
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 201
    
    def test_campos_opcionais_podem_ser_nulos(self, client, auth_headers_admin):
        """Testa se campos opcionais podem ser nulos"""
        dados = {
            'empresa': 'Empresa',
            'lote': 'LOTE',
            'temp_ideal': 37.5,
            'umid_ideal': 60.0,
            'pressao_ideal': None,
            'lumens': None,
            'id_sala': None,
            'estagio_ovo': None
        }
        
        response = client.post(
            '/api/parametros',
            data=json.dumps(dados),
            headers=auth_headers_admin
        )
        
        assert response.status_code == 201
