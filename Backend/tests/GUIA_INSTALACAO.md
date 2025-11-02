# 🚀 GUIA DE INSTALAÇÃO - Testes Embryotech

## ⚠️ IMPORTANTE: Onde Colocar os Arquivos

A estrutura **CORRETA** do seu projeto deve ser:

```
D:\RepositorioGithub\Embryotech\Backend\
├── app.py                      ← Seus arquivos principais
├── models.py
├── config.py
├── extensions.py
├── logging_utils.py
├── requirements.txt
├── _env
│
├── test_config.py              ← Arquivo de config de teste (NOVO)
├── pytest.ini                  ← Config do pytest (NOVO)
├── requirements-test.txt       ← Dependências de teste (NOVO)
│
└── tests/                      ← Pasta de testes (NOVA)
    ├── __init__.py
    ├── conftest.py
    ├── test_models.py
    ├── test_auth.py
    ├── test_parametros_api.py
    ├── test_leituras_api.py
    └── test_logging.py
```

## 📋 Passo a Passo para Configurar

### Passo 1: Organizar os Arquivos

```bash
# No diretório Backend (onde está app.py), crie a pasta tests:
cd D:\RepositorioGithub\Embryotech\Backend
mkdir tests
```

### Passo 2: Mover Arquivos para os Lugares Corretos

**Mova da pasta `outputs/testes` para `Backend/`:**
- `test_config.py`
- `pytest.ini`
- `requirements-test.txt`

**Mova da pasta `outputs/testes` para `Backend/tests/`:**
- `__init__.py`
- `conftest.py`
- `test_models.py`
- `test_auth.py`
- `test_parametros_api.py`
- `test_leituras_api.py`
- `test_logging.py`

**Mantenha na pasta `outputs/testes` (são apenas documentação):**
- `README_TESTES.md`
- `TESTING.md`
- `TESTING_EXAMPLES.py`
- `INICIO_RAPIDO.md`

### Passo 3: Instalar Dependências

```bash
# No diretório Backend
pip install -r requirements-test.txt
```

### Passo 4: Verificar Instalação

```bash
# Verificar se pytest foi instalado
pytest --version

# Deve mostrar algo como: pytest 7.4.3
```

## ✅ Como Executar os Testes

### ⚠️ NUNCA faça assim (ERRADO):
```bash
# ❌ ERRADO - Não execute diretamente com python
python test_auth.py
python tests/test_auth.py
```

### ✅ Faça assim (CORRETO):

```bash
# No diretório Backend (onde está app.py)
cd D:\RepositorioGithub\Embryotech\Backend

# Executar TODOS os testes
pytest tests/ -v

# Executar arquivo específico
pytest tests/test_models.py -v

# Executar teste específico
pytest tests/test_models.py::TestUserModel::test_criar_usuario -v

# Executar com cobertura
pytest tests/ --cov=. --cov-report=html
```

## 🔍 Verificar se Está Funcionando

### Teste Rápido:

```bash
cd D:\RepositorioGithub\Embryotech\Backend
pytest tests/test_models.py -v
```

**Saída esperada:**
```
============================= test session starts =============================
collected 25 items

tests/test_models.py::TestUserModel::test_criar_usuario PASSED          [  4%]
tests/test_models.py::TestUserModel::test_set_password PASSED           [  8%]
...
============================= 25 passed in 2.34s ==============================
```

## 🐛 Problemas Comuns

### Erro: "ModuleNotFoundError: No module named 'models'"

**Causa:** Você está executando os testes do lugar errado ou com `python` ao invés de `pytest`

**Solução:**
```bash
# 1. Certifique-se de estar no diretório Backend
cd D:\RepositorioGithub\Embryotech\Backend

# 2. Execute com pytest (não python)
pytest tests/ -v
```

### Erro: "No module named 'pytest'"

**Causa:** pytest não está instalado

**Solução:**
```bash
pip install -r requirements-test.txt
```

### Erro: "DATABASE_URL not configured"

**Causa:** Variáveis de ambiente não configuradas

**Solução:** O test_config.py já está configurado para usar SQLite em memória, então isso não deve acontecer. Se acontecer, verifique se o arquivo test_config.py está no lugar correto.

### Erro: "fixture 'app' not found"

**Causa:** conftest.py não está no lugar correto

**Solução:**
```bash
# Verificar se conftest.py está em Backend/tests/
ls tests/conftest.py

# Se não estiver, mova para lá
```

## 📂 Estrutura Final Verificada

Execute este comando para verificar:

```bash
cd D:\RepositorioGithub\Embryotech\Backend
dir /B
```

**Você deve ver:**
```
app.py
models.py
config.py
extensions.py
logging_utils.py
test_config.py          ← NOVO
pytest.ini              ← NOVO
requirements-test.txt   ← NOVO
tests                   ← NOVA PASTA
```

E dentro de tests:
```bash
dir tests /B
```

**Você deve ver:**
```
__init__.py
conftest.py
test_models.py
test_auth.py
test_parametros_api.py
test_leituras_api.py
test_logging.py
```

## 🎯 Comandos Úteis (Windows)

```powershell
# Executar todos os testes
pytest tests/ -v

# Executar testes de um arquivo específico
pytest tests/test_models.py -v

# Executar testes com output detalhado
pytest tests/ -v -s

# Parar no primeiro erro
pytest tests/ -x

# Ver apenas falhas
pytest tests/ -v --tb=short

# Gerar relatório de cobertura HTML
pytest tests/ --cov=. --cov-report=html
start htmlcov\index.html
```

## 📊 Próximos Passos

1. ✅ Organize os arquivos na estrutura correta
2. ✅ Instale as dependências: `pip install -r requirements-test.txt`
3. ✅ Execute: `pytest tests/ -v`
4. 📖 Se tudo passou, leia TESTING.md para mais detalhes
5. 💡 Consulte TESTING_EXAMPLES.py para adicionar novos testes

## 💬 Ainda com Problemas?

Se após seguir todos os passos ainda houver problemas:

1. Verifique a versão do Python: `python --version` (deve ser 3.8+)
2. Verifique a versão do pytest: `pytest --version`
3. Confirme que está no diretório correto: `cd D:\RepositorioGithub\Embryotech\Backend`
4. Verifique se os imports estão funcionando:
   ```bash
   python -c "import models; print('OK')"
   ```

## ✨ Dica Pro

Crie um arquivo `run_tests.bat` no diretório Backend:

```batch
@echo off
cd /d %~dp0
pytest tests/ -v --cov=. --cov-report=html
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ===================================
    echo   TODOS OS TESTES PASSARAM!
    echo ===================================
    echo.
    echo Abrir relatorio de cobertura?
    pause
    start htmlcov\index.html
) else (
    echo.
    echo ===================================
    echo   ALGUNS TESTES FALHARAM!
    echo ===================================
    pause
)
```

Depois só executar: `run_tests.bat`

---

**🎉 Pronto! Agora você tem uma estrutura de testes profissional e funcional!**
