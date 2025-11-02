# 📋 CHECKLIST DE MIGRAÇÃO - ONDE COLOCAR CADA ARQUIVO

## 🎯 Use este checklist para organizar os arquivos corretamente

---

## 📂 ESTRUTURA DE DESTINO

```
D:\RepositorioGithub\Embryotech\Backend\
├── app.py (já existe)
├── models.py (já existe)
├── config.py (já existe)
├── extensions.py (já existe)
├── logging_utils.py (já existe)
├── requirements.txt (já existe)
├── _env (já existe)
│
├── test_config.py ⬅️ COPIAR AQUI
├── pytest.ini ⬅️ COPIAR AQUI
├── requirements-test.txt ⬅️ COPIAR AQUI
├── validar_estrutura.py ⬅️ COPIAR AQUI
├── run_tests.bat ⬅️ COPIAR AQUI
├── run_specific_tests.bat ⬅️ COPIAR AQUI
│
└── tests/ ⬅️ CRIAR ESTA PASTA
    ├── __init__.py ⬅️ COPIAR AQUI
    ├── conftest.py ⬅️ COPIAR AQUI (versão corrigida!)
    ├── test_models.py ⬅️ COPIAR AQUI
    ├── test_auth.py ⬅️ COPIAR AQUI
    ├── test_parametros_api.py ⬅️ COPIAR AQUI
    ├── test_leituras_api.py ⬅️ COPIAR AQUI
    └── test_logging.py ⬅️ COPIAR AQUI
```

---

## ✅ PASSO A PASSO COM CHECKLIST

### Passo 1: Criar a Pasta tests

```powershell
cd D:\RepositorioGithub\Embryotech\Backend
mkdir tests
```

- [ ] Pasta `tests` criada em `Backend/`

---

### Passo 2: Copiar Arquivos para a RAIZ do Backend

**De:** `D:\RepositorioGithub\Embryotech\Backend\outputs\testes\`  
**Para:** `D:\RepositorioGithub\Embryotech\Backend\`

Copiar estes arquivos:

- [ ] `test_config.py`
- [ ] `pytest.ini`
- [ ] `requirements-test.txt`
- [ ] `validar_estrutura.py`
- [ ] `run_tests.bat`
- [ ] `run_specific_tests.bat`

**Comando PowerShell:**
```powershell
cd D:\RepositorioGithub\Embryotech\Backend
copy outputs\testes\test_config.py .
copy outputs\testes\pytest.ini .
copy outputs\testes\requirements-test.txt .
copy outputs\testes\validar_estrutura.py .
copy outputs\testes\run_tests.bat .
copy outputs\testes\run_specific_tests.bat .
```

---

### Passo 3: Copiar Arquivos para Backend\tests\

**De:** `D:\RepositorioGithub\Embryotech\Backend\outputs\testes\`  
**Para:** `D:\RepositorioGithub\Embryotech\Backend\tests\`

Copiar estes arquivos:

- [ ] `__init__.py`
- [ ] `conftest.py` ⚠️ *Use a versão CORRIGIDA!*
- [ ] `test_models.py`
- [ ] `test_auth.py`
- [ ] `test_parametros_api.py`
- [ ] `test_leituras_api.py`
- [ ] `test_logging.py`

**Comando PowerShell:**
```powershell
cd D:\RepositorioGithub\Embryotech\Backend
copy outputs\testes\__init__.py tests\
copy outputs\testes\conftest.py tests\
copy outputs\testes\test_models.py tests\
copy outputs\testes\test_auth.py tests\
copy outputs\testes\test_parametros_api.py tests\
copy outputs\testes\test_leituras_api.py tests\
copy outputs\testes\test_logging.py tests\
```

⚠️ **IMPORTANTE:** Use o arquivo `conftest.py` da versão CORRIGIDA (que ajusta o sys.path)

---

### Passo 4: Instalar Dependências

```powershell
cd D:\RepositorioGithub\Embryotech\Backend
pip install -r requirements-test.txt
```

- [ ] Pytest instalado
- [ ] Todas as dependências instaladas

**Verificar:**
```powershell
pytest --version
```

---

### Passo 5: Validar a Estrutura

```powershell
cd D:\RepositorioGithub\Embryotech\Backend
python validar_estrutura.py
```

- [ ] Script executado
- [ ] Mensagem: "✓ PERFEITO! Tudo está configurado corretamente!"

Se houver erros, o script vai indicar o que está faltando.

---

### Passo 6: Executar os Testes

```powershell
cd D:\RepositorioGithub\Embryotech\Backend
run_tests.bat
```

- [ ] Testes executados
- [ ] Todos os testes passaram
- [ ] Relatório de cobertura gerado

---

## 🎯 ESTRUTURA FINAL ESPERADA

Após concluir todos os passos, execute:

```powershell
cd D:\RepositorioGithub\Embryotech\Backend
dir /B
```

**Você deve ver:**
```
app.py
config.py
extensions.py
logging_utils.py
models.py
pytest.ini ← NOVO
requirements-test.txt ← NOVO
requirements.txt
run_specific_tests.bat ← NOVO
run_tests.bat ← NOVO
test_config.py ← NOVO
tests ← NOVA PASTA
validar_estrutura.py ← NOVO
_env
```

E dentro de `tests`:

```powershell
dir tests /B
```

**Você deve ver:**
```
conftest.py
test_auth.py
test_leituras_api.py
test_logging.py
test_models.py
test_parametros_api.py
__init__.py
```

---

## 🔍 VERIFICAÇÃO FINAL

Execute cada comando e marque se passou:

```powershell
cd D:\RepositorioGithub\Embryotech\Backend
```

- [ ] `python validar_estrutura.py` → ✓ PERFEITO!
- [ ] `pytest tests/test_models.py -v` → Todos passaram
- [ ] `run_tests.bat` → Todos passaram

---

## ⚠️ ARQUIVOS QUE FICAM NA PASTA outputs/testes (NÃO COPIAR)

Estes são apenas documentação, deixe-os lá:

- `README_TESTES.md`
- `README_FINAL.md`
- `GUIA_INSTALACAO.md`
- `TESTING.md`
- `TESTING_EXAMPLES.py`
- `INICIO_RAPIDO.md`
- `.gitignore_tests`
- `run_tests.sh` (para Linux/Mac)
- `run_specific_tests.sh` (para Linux/Mac)

---

## 📊 RESUMO VISUAL

```
ORIGEM: outputs/testes/
    ├── test_config.py ─────────────────────┐
    ├── pytest.ini ─────────────────────────┤
    ├── requirements-test.txt ──────────────┤
    ├── validar_estrutura.py ───────────────┤
    ├── run_tests.bat ──────────────────────┤ COPIAR PARA
    ├── run_specific_tests.bat ─────────────┤ Backend/
    │                                        │ (raiz)
    ├── __init__.py ────────────────────────┼────┐
    ├── conftest.py (corrigido!) ───────────┼────┤
    ├── test_models.py ─────────────────────┼────┤
    ├── test_auth.py ───────────────────────┼────┤ COPIAR PARA
    ├── test_parametros_api.py ─────────────┼────┤ Backend/tests/
    ├── test_leituras_api.py ───────────────┼────┤
    └── test_logging.py ────────────────────┼────┘
                                            │
DESTINO: Backend/                          │
    ├── app.py (já existe) ◄───────────────┘
    ├── models.py (já existe)
    ├── [novos arquivos aqui]
    └── tests/
        └── [arquivos de teste aqui]
```

---

## ✨ PRONTO!

Após completar todos os checkboxes acima, você terá uma estrutura de testes completa e funcional!

**Próximos passos:**
1. ✅ Execute os testes: `run_tests.bat`
2. 📖 Leia a documentação: `README_FINAL.md`
3. 💡 Adicione novos testes conforme necessário

---

**Dúvidas?** Consulte `README_FINAL.md` para instruções detalhadas.
