# 🧪 Guia de Testes - Embryotech

Este documento descreve a estrutura de testes e como executá-los no projeto Embryotech.

## 📋 Índice

- [Estrutura de Testes](#estrutura-de-testes)
- [Instalação](#instalação)
- [Executando Testes](#executando-testes)
- [Tipos de Testes](#tipos-de-testes)
- [Cobertura de Código](#cobertura-de-código)
- [Boas Práticas](#boas-práticas)

## 🏗️ Estrutura de Testes

```
tests/
├── conftest.py                 # Fixtures e configurações compartilhadas
├── test_models.py             # Testes dos modelos (User, Parametro, Leitura, Log)
├── test_auth.py               # Testes de autenticação e autorização
├── test_parametros_api.py     # Testes da API de parâmetros
├── test_leituras_api.py       # Testes da API de leituras
└── test_logging.py            # Testes do sistema de logging
```

## 📦 Instalação

### 1. Instalar Dependências de Teste

```bash
pip install -r requirements-test.txt
```

### 2. Configurar Variáveis de Ambiente

Crie um arquivo `.env` para testes (ou use `.env.test`):

```bash
# Banco de dados de teste (SQLite em memória ou PostgreSQL separado)
DB_USER=testuser
DB_PASSWORD=testpass
DB_HOST=localhost
DB_PORT=5432
DB_NAME=embryotech_test

# Chaves secretas (apenas para testes)
SECRET_KEY=test-secret-key
JWT_SECRET_KEY=test-jwt-secret
```

## 🚀 Executando Testes

### Executar Todos os Testes

```bash
# Linux/Mac
chmod +x run_tests.sh
./run_tests.sh

# Ou diretamente com pytest
pytest tests/ -v
```

### Executar Testes Específicos

```bash
# Usar script helper
chmod +x run_specific_tests.sh

# Testes de modelos
./run_specific_tests.sh models

# Testes de autenticação
./run_specific_tests.sh auth

# Testes de API
./run_specific_tests.sh api

# Testes de logging
./run_specific_tests.sh logging

# Testes de parâmetros
./run_specific_tests.sh parametros

# Testes de leituras
./run_specific_tests.sh leituras

# Apenas testes rápidos
./run_specific_tests.sh fast

# Re-executar testes que falharam
./run_specific_tests.sh failed
```

### Executar Teste Individual

```bash
# Executar um arquivo específico
pytest tests/test_models.py -v

# Executar uma classe específica
pytest tests/test_models.py::TestUserModel -v

# Executar um teste específico
pytest tests/test_models.py::TestUserModel::test_criar_usuario -v
```

## 📊 Tipos de Testes

### 1. Testes Unitários de Modelos (`test_models.py`)

Testam os modelos de dados isoladamente:

- ✅ Criação de usuários
- ✅ Hash e verificação de senhas
- ✅ Geração e verificação de tokens JWT
- ✅ Modelos de Parâmetro, Leitura e Log
- ✅ Métodos to_dict() e relacionamentos

**Executar:**
```bash
pytest tests/test_models.py -v
```

### 2. Testes de Autenticação (`test_auth.py`)

Testam registro, login e autorização:

- ✅ Registro de novos usuários
- ✅ Login com credenciais válidas/inválidas
- ✅ Validação de tokens JWT
- ✅ Controle de acesso (admin vs usuário comum)
- ✅ Expiração de tokens

**Executar:**
```bash
pytest tests/test_auth.py -v
```

### 3. Testes de API de Parâmetros (`test_parametros_api.py`)

Testam endpoints de gerenciamento de parâmetros:

- ✅ CRUD de parâmetros (apenas admin)
- ✅ Listagem de empresas e lotes
- ✅ Busca e filtros
- ✅ Validação de dados
- ✅ Controle de permissões

**Executar:**
```bash
pytest tests/test_parametros_api.py -v
```

### 4. Testes de API de Leituras (`test_leituras_api.py`)

Testam endpoints de leituras de dados:

- ✅ CRUD de leituras
- ✅ Validação de campos (umidade, temperatura, pressão)
- ✅ Formatos de data
- ✅ Testes de integração (criar, atualizar, deletar)

**Executar:**
```bash
pytest tests/test_leituras_api.py -v
```

### 5. Testes de Logging (`test_logging.py`)

Testam o sistema de auditoria:

- ✅ Registro automático de logs
- ✅ Logs de login/logout
- ✅ Logs de alterações em parâmetros
- ✅ Logs de operações CRUD
- ✅ API de consulta de logs (admin)
- ✅ Filtros e buscas

**Executar:**
```bash
pytest tests/test_logging.py -v
```

## 📈 Cobertura de Código

### Gerar Relatório de Cobertura

```bash
# Executar testes com cobertura
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Abrir relatório HTML
# Linux
xdg-open htmlcov/index.html

# Mac
open htmlcov/index.html

# Windows
start htmlcov/index.html
```

### Verificar Cobertura Mínima

```bash
# Falhar se cobertura for menor que 80%
pytest tests/ --cov=. --cov-fail-under=80
```

## 🎯 Fixtures Disponíveis

As fixtures estão definidas em `tests/conftest.py`:

| Fixture | Descrição |
|---------|-----------|
| `app` | Aplicação Flask configurada para testes |
| `client` | Cliente HTTP para fazer requisições |
| `db_session` | Sessão de banco limpa para cada teste |
| `usuario_comum` | Usuário não-admin para testes |
| `usuario_admin` | Usuário administrador para testes |
| `token_usuario_comum` | Token JWT de usuário comum |
| `token_usuario_admin` | Token JWT de administrador |
| `auth_headers_comum` | Headers com autenticação de usuário comum |
| `auth_headers_admin` | Headers com autenticação de admin |
| `parametro_exemplo` | Parâmetro de exemplo no banco |
| `leitura_exemplo` | Leitura de exemplo no banco |
| `multiplos_parametros` | Vários parâmetros para testes de listagem |
| `multiplas_leituras` | Várias leituras para testes de filtro |

## ✅ Boas Práticas

### 1. Nomenclatura de Testes

```python
# ✅ BOM - Descritivo e claro
def test_criar_usuario_com_email_duplicado_retorna_erro():
    pass

# ❌ RUIM - Vago
def test_user():
    pass
```

### 2. Organização por Classes

```python
class TestUserModel:
    """Testes relacionados ao modelo User"""
    
    def test_criar_usuario(self):
        pass
    
    def test_verificar_senha(self):
        pass
```

### 3. Usar Fixtures

```python
# ✅ BOM - Usar fixtures
def test_criar_parametro(client, auth_headers_admin):
    response = client.post('/api/parametros', headers=auth_headers_admin)
    assert response.status_code == 201

# ❌ RUIM - Criar tudo manualmente
def test_criar_parametro():
    app = create_app()
    user = create_user()
    token = generate_token(user)
    # ...muito código repetitivo
```

### 4. Testes Independentes

```python
# ✅ BOM - Cada teste é independente
def test_criar_usuario(db_session):
    user = User(username='test')
    db_session.add(user)
    db_session.commit()
    assert user.id is not None

# ❌ RUIM - Depende de outros testes
def test_atualizar_usuario():
    # Assume que usuário foi criado em outro teste
    user = User.query.first()
    user.email = 'new@email.com'
```

### 5. Assertions Claras

```python
# ✅ BOM - Mensagens de erro claras
assert response.status_code == 200, f"Esperado 200, recebido {response.status_code}"
assert user.is_admin is True, "Usuário deveria ser admin"

# ❌ RUIM - Sem contexto
assert response.status_code == 200
assert user.is_admin
```

## 🐛 Debugging de Testes

### Ver Output Completo

```bash
pytest tests/test_models.py -v -s
```

### Parar no Primeiro Erro

```bash
pytest tests/ -x
```

### Modo Debug com PDB

```bash
pytest tests/test_models.py --pdb
```

### Ver Testes mais Lentos

```bash
pytest tests/ --durations=10
```

## 📝 Checklist de Testes

Antes de fazer commit, verifique:

- [ ] Todos os testes passam
- [ ] Cobertura de código >= 80%
- [ ] Novos features têm testes
- [ ] Testes são independentes
- [ ] Não há prints ou debugs esquecidos
- [ ] Nomes de testes são descritivos

## 🔄 Integração Contínua (CI/CD)

### GitHub Actions (exemplo)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements-test.txt
      - name: Run tests
        run: |
          pytest tests/ --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 📞 Suporte

Se encontrar problemas com os testes:

1. Verifique se todas as dependências estão instaladas
2. Confirme que o banco de dados de teste está configurado
3. Revise os logs de erro detalhados
4. Entre em contato com a equipe de desenvolvimento

---

**Desenvolvido por Outside Agrotech** 🌱
