"""
EXEMPLOS PRÁTICOS - Como Adicionar Novos Testes
================================================

Este arquivo contém exemplos práticos de como criar novos testes
para diferentes cenários no projeto Embryotech.
"""

# ==============================================================================
# EXEMPLO 1: Adicionar Teste para Novo Endpoint
# ==============================================================================

"""
Cenário: Você criou um novo endpoint GET /api/empresas/<id> 
que retorna detalhes de uma empresa específica.

Adicione este teste em tests/test_parametros_api.py:
"""

def test_obter_empresa_por_id(client, auth_headers_admin, parametro_exemplo):
    """Testa obtenção de empresa por ID"""
    empresa_id = parametro_exemplo.id
    
    response = client.get(
        f'/api/empresas/{empresa_id}',
        headers=auth_headers_admin
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['id'] == empresa_id
    assert 'nome' in data
    assert 'lotes' in data


# ==============================================================================
# EXEMPLO 2: Testar Validação de Campos
# ==============================================================================

"""
Cenário: Você adicionou validação para que temperatura deve estar entre 30-45°C

Adicione estes testes em tests/test_leituras_api.py:
"""

def test_temperatura_minima_invalida(client, auth_headers_comum):
    """Testa temperatura abaixo do mínimo permitido"""
    dados = {
        'temperatura': 25.0,  # Abaixo do mínimo (30°C)
        'umidade': 60.0
    }
    
    response = client.post(
        '/api/leituras',
        data=json.dumps(dados),
        headers=auth_headers_comum
    )
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'temperatura' in data['message'].lower()


def test_temperatura_maxima_invalida(client, auth_headers_comum):
    """Testa temperatura acima do máximo permitido"""
    dados = {
        'temperatura': 50.0,  # Acima do máximo (45°C)
        'umidade': 60.0
    }
    
    response = client.post(
        '/api/leituras',
        data=json.dumps(dados),
        headers=auth_headers_comum
    )
    
    assert response.status_code == 400


def test_temperatura_no_limite_valida(client, auth_headers_comum):
    """Testa temperaturas nos limites válidos"""
    for temp in [30.0, 45.0]:  # Limites válidos
        dados = {
            'temperatura': temp,
            'umidade': 60.0
        }
        
        response = client.post(
            '/api/leituras',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 201


# ==============================================================================
# EXEMPLO 3: Testar Novo Modelo
# ==============================================================================

"""
Cenário: Você criou um novo modelo 'Alerta' que registra alertas do sistema

Adicione este teste em tests/test_models.py:
"""

class TestAlertaModel:
    """Testes para o modelo Alerta"""
    
    def test_criar_alerta(self, db_session, parametro_exemplo):
        """Testa criação de alerta"""
        alerta = Alerta(
            parametro_id=parametro_exemplo.id,
            tipo='TEMPERATURA_ALTA',
            valor_medido=40.0,
            valor_esperado=37.5,
            gravidade='ALTA',
            mensagem='Temperatura acima do ideal'
        )
        
        db_session.add(alerta)
        db_session.commit()
        
        assert alerta.id is not None
        assert alerta.tipo == 'TEMPERATURA_ALTA'
        assert alerta.gravidade == 'ALTA'
    
    def test_relacionamento_alerta_parametro(self, db_session, parametro_exemplo):
        """Testa relacionamento entre Alerta e Parametro"""
        alerta = Alerta(
            parametro_id=parametro_exemplo.id,
            tipo='TESTE',
            mensagem='Teste'
        )
        
        db_session.add(alerta)
        db_session.commit()
        
        # Verificar relacionamento
        assert alerta.parametro is not None
        assert alerta.parametro.id == parametro_exemplo.id
    
    def test_alerta_to_dict(self, db_session, parametro_exemplo):
        """Testa conversão de alerta para dicionário"""
        alerta = Alerta(
            parametro_id=parametro_exemplo.id,
            tipo='TESTE',
            mensagem='Teste'
        )
        
        db_session.add(alerta)
        db_session.commit()
        
        dict_alerta = alerta.to_dict()
        
        assert isinstance(dict_alerta, dict)
        assert 'id' in dict_alerta
        assert 'tipo' in dict_alerta
        assert 'mensagem' in dict_alerta


# ==============================================================================
# EXEMPLO 4: Testar Funcionalidade com Mock
# ==============================================================================

"""
Cenário: Você tem um endpoint que envia email de notificação
e quer testar sem realmente enviar emails

Adicione este teste usando pytest-mock:
"""

def test_enviar_alerta_por_email(client, auth_headers_admin, mocker):
    """Testa envio de alerta por email (com mock)"""
    # Mock da função de envio de email
    mock_enviar_email = mocker.patch('utils.email.enviar_email')
    
    dados = {
        'destinatario': 'admin@empresa.com',
        'tipo_alerta': 'TEMPERATURA_ALTA',
        'mensagem': 'Temperatura crítica detectada'
    }
    
    response = client.post(
        '/api/alertas/enviar-email',
        data=json.dumps(dados),
        headers=auth_headers_admin
    )
    
    assert response.status_code == 200
    
    # Verificar que a função foi chamada com os parâmetros corretos
    mock_enviar_email.assert_called_once_with(
        destinatario='admin@empresa.com',
        assunto=mocker.ANY,
        corpo=mocker.ANY
    )


# ==============================================================================
# EXEMPLO 5: Testar Paginação
# ==============================================================================

"""
Cenário: Você adicionou paginação ao endpoint de listagem de leituras

Adicione estes testes em tests/test_leituras_api.py:
"""

def test_listar_leituras_com_paginacao(client, auth_headers_comum, db_session):
    """Testa listagem de leituras com paginação"""
    # Criar 25 leituras
    for i in range(25):
        leitura = Leitura(
            temperatura=37.0 + i * 0.1,
            umidade=60.0,
            lote=f'LOTE_{i:03d}'
        )
        db_session.add(leitura)
    db_session.commit()
    
    # Página 1 (10 itens)
    response = client.get(
        '/api/leituras?page=1&per_page=10',
        headers=auth_headers_comum
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert len(data['items']) == 10
    assert data['total'] == 25
    assert data['pages'] == 3
    assert data['current_page'] == 1


def test_paginacao_pagina_invalida(client, auth_headers_comum):
    """Testa paginação com página inválida"""
    response = client.get(
        '/api/leituras?page=999',
        headers=auth_headers_comum
    )
    
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'página' in data['message'].lower()


# ==============================================================================
# EXEMPLO 6: Testar Transações e Rollback
# ==============================================================================

"""
Cenário: Você quer garantir que falhas em operações fazem rollback

Adicione este teste:
"""

def test_criar_parametro_com_erro_faz_rollback(client, auth_headers_admin, db_session, mocker):
    """Testa que erro ao criar parâmetro faz rollback da transação"""
    # Contar parâmetros antes
    count_antes = Parametro.query.count()
    
    # Mock para forçar erro no commit
    mocker.patch.object(db_session, 'commit', side_effect=Exception('Erro de banco'))
    
    dados = {
        'empresa': 'Empresa',
        'lote': 'LOTE',
        'temp_ideal': 37.5,
        'umid_ideal': 60.0
    }
    
    response = client.post(
        '/api/parametros',
        data=json.dumps(dados),
        headers=auth_headers_admin
    )
    
    # Deve retornar erro
    assert response.status_code == 400
    
    # Verificar que nenhum registro foi adicionado (rollback funcionou)
    count_depois = Parametro.query.count()
    assert count_depois == count_antes


# ==============================================================================
# EXEMPLO 7: Testar Performance
# ==============================================================================

"""
Cenário: Você quer garantir que uma operação não demore mais que X segundos

Adicione este teste:
"""

import time

def test_listar_leituras_performance(client, auth_headers_comum, multiplas_leituras):
    """Testa que listagem de leituras é rápida"""
    inicio = time.time()
    
    response = client.get('/api/leituras', headers=auth_headers_comum)
    
    fim = time.time()
    duracao = fim - inicio
    
    assert response.status_code == 200
    # Deve completar em menos de 1 segundo
    assert duracao < 1.0, f"Listagem demorou {duracao:.2f}s (limite: 1.0s)"


# ==============================================================================
# EXEMPLO 8: Testar Filtros e Buscas Complexas
# ==============================================================================

"""
Cenário: Você adicionou filtros avançados à listagem de leituras

Adicione este teste:
"""

def test_filtrar_leituras_multiplos_criterios(client, auth_headers_comum, db_session):
    """Testa filtro de leituras com múltiplos critérios"""
    # Criar leituras de teste
    leituras = [
        Leitura(temperatura=35.0, umidade=55.0, lote='A', pressao=1010.0),
        Leitura(temperatura=37.0, umidade=60.0, lote='A', pressao=1013.0),
        Leitura(temperatura=39.0, umidade=65.0, lote='B', pressao=1015.0),
    ]
    
    for leitura in leituras:
        db_session.add(leitura)
    db_session.commit()
    
    # Filtrar: lote=A AND temperatura > 36
    response = client.get(
        '/api/leituras?lote=A&temp_min=36',
        headers=auth_headers_comum
    )
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Deve retornar apenas 1 leitura (37°C, lote A)
    assert len(data) == 1
    assert data[0]['temperatura'] == 37.0
    assert data[0]['lote'] == 'A'


# ==============================================================================
# EXEMPLO 9: Testar Rate Limiting
# ==============================================================================

"""
Cenário: Você adicionou rate limiting (limite de requisições) na API

Adicione este teste:
"""

def test_rate_limiting(client, auth_headers_comum):
    """Testa que rate limiting bloqueia após X requisições"""
    # Fazer 100 requisições rapidamente
    for i in range(100):
        response = client.get('/api/leituras', headers=auth_headers_comum)
        
        # Primeiras 50 devem funcionar
        if i < 50:
            assert response.status_code == 200
        # Após 50, deve retornar 429 (Too Many Requests)
        else:
            assert response.status_code == 429


# ==============================================================================
# EXEMPLO 10: Testar Webhooks ou Integrações Externas
# ==============================================================================

"""
Cenário: Seu sistema envia dados para uma API externa via webhook

Adicione este teste:
"""

def test_webhook_enviado_ao_criar_alerta(client, auth_headers_admin, mocker):
    """Testa que webhook é enviado quando alerta é criado"""
    # Mock da requisição HTTP para o webhook
    mock_post = mocker.patch('requests.post')
    
    dados = {
        'tipo': 'TEMPERATURA_ALTA',
        'valor': 40.0,
        'mensagem': 'Alerta de temperatura'
    }
    
    response = client.post(
        '/api/alertas',
        data=json.dumps(dados),
        headers=auth_headers_admin
    )
    
    assert response.status_code == 201
    
    # Verificar que webhook foi chamado
    mock_post.assert_called_once()
    
    # Verificar URL e payload do webhook
    call_args = mock_post.call_args
    assert 'https://webhook.site' in call_args[0][0]
    assert call_args[1]['json']['tipo'] == 'TEMPERATURA_ALTA'


# ==============================================================================
# DICAS FINAIS
# ==============================================================================

"""
1. SEMPRE escreva testes para bugs encontrados
   - Primeiro crie um teste que reproduz o bug
   - Depois corrija o código
   - O teste garante que o bug não voltará

2. Use fixtures para evitar código duplicado
   - Se você está criando os mesmos dados em vários testes, crie uma fixture

3. Teste casos extremos (edge cases)
   - Valores vazios, nulos, negativos
   - Strings muito longas
   - Listas vazias
   - Datas inválidas

4. Teste permissões em TODOS os endpoints
   - Sem autenticação
   - Com usuário comum
   - Com administrador

5. Mantenha testes rápidos
   - Use banco em memória (SQLite) quando possível
   - Evite sleeps desnecessários
   - Mock operações lentas (email, APIs externas)

6. Teste tanto o caminho feliz quanto os erros
   - Sucesso (200, 201)
   - Validação (400)
   - Autenticação (401)
   - Permissão (403)
   - Não encontrado (404)
   - Erro servidor (500)

7. Nomes de testes devem ser descritivos
   ✅ BOM: test_criar_usuario_com_email_duplicado_retorna_400
   ❌ RUIM: test_user_creation

8. Um teste deve testar UMA coisa
   - Se você tem múltiplos asserts, considere dividir em múltiplos testes
   
9. Use parametrize para testar múltiplos valores
   @pytest.mark.parametrize("temperatura", [30, 35, 40, 45])
   def test_temperatura_valida(temperatura):
       # teste com cada valor
       
10. Mantenha 100% de cobertura em código crítico
    - Autenticação
    - Autorização  
    - Operações financeiras
    - Validação de dados
"""

# ==============================================================================
# TEMPLATE DE TESTE
# ==============================================================================

"""
Use este template ao criar novos testes:
"""

class TestNoveFuncionalidade:
    """Testes para [descreva a funcionalidade]"""
    
    def test_cenario_feliz(self, client, auth_headers_comum):
        """Testa [descreva o que testa] com sucesso"""
        # Arrange (preparar)
        dados = {
            'campo1': 'valor1',
            'campo2': 'valor2'
        }
        
        # Act (executar)
        response = client.post(
            '/api/endpoint',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        # Assert (verificar)
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['campo1'] == 'valor1'
    
    def test_validacao_erro(self, client, auth_headers_comum):
        """Testa validação quando [descreva cenário de erro]"""
        dados = {'campo_invalido': 'valor'}
        
        response = client.post(
            '/api/endpoint',
            data=json.dumps(dados),
            headers=auth_headers_comum
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'erro' in data['message'].lower()
    
    def test_permissao_negada(self, client, auth_headers_comum):
        """Testa que usuário sem permissão não pode acessar"""
        response = client.post('/api/endpoint', headers=auth_headers_comum)
        
        assert response.status_code == 403
