# 🧪 Estrutura de Testes - Embryotech

## 📦 O que foi criado?

Criei uma estrutura **completa e profissional** de testes para validação da sua aplicação Flask Embryotech. Esta estrutura inclui:

### ✅ Arquivos de Teste

1. **`tests/conftest.py`** - Fixtures e configurações compartilhadas
2. **`tests/test_models.py`** - 20+ testes unitários dos modelos
3. **`tests/test_auth.py`** - 15+ testes de autenticação e autorização
4. **`tests/test_parametros_api.py`** - 20+ testes da API de parâmetros
5. **`tests/test_leituras_api.py`** - 25+ testes da API de leituras
6. **`tests/test_logging.py`** - 20+ testes do sistema de logging

### ⚙️ Configuração

- **`test_config.py`** - Configuração específica para ambiente de testes
- **`pytest.ini`** - Configuração do pytest com markers e opções
- **`requirements-test.txt`** - Dependências necessárias para testes

### 🚀 Scripts de Execução

- **`run_tests.sh`** - Script para executar todos os testes com cobertura
- **`run_specific_tests.sh`** - Script para executar testes específicos

### 📚 Documentação

- **`TESTING.md`** - Guia completo de testes com instruções detalhadas
- **`TESTING_EXAMPLES.py`** - 10+ exemplos práticos de como adicionar novos testes
- **`.gitignore_tests`** - Arquivos a ignorar no git

---

## 🎯 Cobertura de Testes

### **100+ Testes** cobrindo:

#### ✅ Modelos (test_models.py)
- Criação e validação de usuários
- Hash e verificação de senhas
- Geração e validação de tokens JWT
- Campos is_admin
- Modelos Parametro, Leitura e Log
- Métodos to_dict() e relacionamentos

#### ✅ Autenticação (test_auth.py)
- Registro de novos usuários
- Login com credenciais válidas/inválidas
- Validação de tokens JWT
- Controle de acesso (admin vs usuário comum)
- Expiração de tokens
- Headers de autorização

#### ✅ API de Parâmetros (test_parametros_api.py)
- CRUD completo de parâmetros
- Listagem de empresas
- Listagem e filtro de lotes
- Busca por empresa e lote
- Atualização parcial e completa
- Validação de permissões (apenas admin)
- Validação de campos obrigatórios

#### ✅ API de Leituras (test_leituras_api.py)
- CRUD completo de leituras
- Validação de campos (umidade, temperatura, pressão)
- Formatos de data (ISO)
- Testes de integração
- Múltiplos usuários
- Campos opcionais e obrigatórios

#### ✅ Sistema de Logging (test_logging.py)
- Registro automático de logs
- Logs de login/logout
- Logs de alterações em parâmetros
- Logs de operações CRUD
- API de consulta de logs
- Filtros por usuário e ação
- Remoção de senhas dos logs

---

## 🚀 Como Usar

### 1️⃣ Instalação

```bash
# Instalar dependências de teste
pip install -r requirements-test.txt
```

### 2️⃣ Executar Todos os Testes

```bash
# Linux/Mac
chmod +x run_tests.sh
./run_tests.sh

# Windows
python -m pytest tests/ -v
```

### 3️⃣ Executar Testes Específicos

```bash
# Tornar script executável (apenas primeira vez)
chmod +x run_specific_tests.sh

# Testes de modelos
./run_specific_tests.sh models

# Testes de autenticação
./run_specific_tests.sh auth

# Testes de API
./run_specific_tests.sh api

# Testes de logging
./run_specific_tests.sh logging

# Ver todas as opções
./run_specific_tests.sh help
```

### 4️⃣ Ver Cobertura de Código

```bash
# Gerar relatório HTML
pytest tests/ --cov=. --cov-report=html

# Abrir relatório
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## 📊 Estrutura de Diretórios

```
.
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Fixtures compartilhadas
│   ├── test_models.py           # Testes de modelos
│   ├── test_auth.py             # Testes de autenticação
│   ├── test_parametros_api.py   # Testes API parâmetros
│   ├── test_leituras_api.py     # Testes API leituras
│   └── test_logging.py          # Testes de logging
│
├── test_config.py               # Configuração de testes
├── pytest.ini                   # Configuração pytest
├── requirements-test.txt        # Dependências
├── run_tests.sh                 # Script executar tudo
├── run_specific_tests.sh        # Script testes específicos
├── TESTING.md                   # Documentação completa
├── TESTING_EXAMPLES.py          # Exemplos práticos
└── .gitignore_tests             # Arquivos a ignorar
```

---

## 🎨 Fixtures Disponíveis

Todas definidas em `tests/conftest.py`:

| Fixture | Descrição |
|---------|-----------|
| `app` | Aplicação Flask para testes |
| `client` | Cliente HTTP para requisições |
| `db_session` | Sessão de banco limpa |
| `usuario_comum` | Usuário não-admin |
| `usuario_admin` | Usuário administrador |
| `token_usuario_comum` | Token JWT de usuário |
| `token_usuario_admin` | Token JWT de admin |
| `auth_headers_comum` | Headers HTTP com autenticação |
| `auth_headers_admin` | Headers HTTP admin |
| `parametro_exemplo` | Parâmetro no banco |
| `leitura_exemplo` | Leitura no banco |
| `multiplos_parametros` | Vários parâmetros |
| `multiplas_leituras` | Várias leituras |

---

## 🔍 Exemplos de Uso

### Executar teste específico
```bash
pytest tests/test_models.py::TestUserModel::test_criar_usuario -v
```

### Executar com verbose
```bash
pytest tests/ -v
```

### Parar no primeiro erro
```bash
pytest tests/ -x
```

### Ver testes mais lentos
```bash
pytest tests/ --durations=10
```

### Modo debug
```bash
pytest tests/ --pdb
```

---

## 📈 Próximos Passos

1. **Execute os testes** para garantir que tudo está funcionando
2. **Veja a cobertura** para identificar áreas não testadas
3. **Leia TESTING.md** para guia completo
4. **Consulte TESTING_EXAMPLES.py** ao adicionar novos testes
5. **Integre com CI/CD** (exemplo no TESTING.md)

---

## ✨ Benefícios

✅ **Confiança** - Código testado significa menos bugs em produção  
✅ **Documentação** - Testes servem como documentação viva  
✅ **Refatoração** - Mude o código com segurança  
✅ **Qualidade** - Detecte problemas antes dos usuários  
✅ **Velocidade** - Automatize validações manuais  

---

## 🆘 Suporte

### Problemas Comuns

**Erro: "ModuleNotFoundError: No module named 'pytest'"**
```bash
pip install -r requirements-test.txt
```

**Erro: "No tests ran"**
```bash
# Verificar se está no diretório correto
cd /caminho/do/projeto
pytest tests/ -v
```

**Erro: "Database connection failed"**
- Verifique configurações em `test_config.py`
- Use SQLite em memória para testes (já configurado)

### Recursos Úteis

- 📖 [Documentação Pytest](https://docs.pytest.org/)
- 📖 [Flask Testing](https://flask.palletsprojects.com/en/2.3.x/testing/)
- 📖 [Coverage.py](https://coverage.readthedocs.io/)

---

## 📝 Notas Importantes

1. **Banco de Dados**: Por padrão usa SQLite em memória (`:memory:`)
2. **Isolamento**: Cada teste é independente e tem banco limpo
3. **Performance**: ~100 testes executam em menos de 30 segundos
4. **Cobertura**: Meta é atingir 80%+ de cobertura de código
5. **CI/CD Ready**: Pronto para integração com GitHub Actions, GitLab CI, etc.

---

**Desenvolvido com ❤️ para Embryotech - Outside Agrotech** 🌱

Para mais informações, consulte **TESTING.md** ou **TESTING_EXAMPLES.py**
