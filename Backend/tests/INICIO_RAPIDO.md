# ⚡ INÍCIO RÁPIDO - Testes Embryotech

## ✅ Checklist de Configuração (5 minutos)

### 1️⃣ Instalar Dependências
```bash
pip install -r requirements-test.txt
```

### 2️⃣ Tornar Scripts Executáveis (Linux/Mac)
```bash
chmod +x run_tests.sh run_specific_tests.sh
```

### 3️⃣ Executar Testes
```bash
./run_tests.sh
```

## 🎯 Comandos Mais Usados

### Ver Status Geral
```bash
pytest tests/ -v
```

### Cobertura de Código
```bash
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### Testes Específicos
```bash
# Modelos
./run_specific_tests.sh models

# Autenticação  
./run_specific_tests.sh auth

# API
./run_specific_tests.sh api
```

### Apenas Testes Rápidos
```bash
./run_specific_tests.sh fast
```

### Re-executar Falhas
```bash
./run_specific_tests.sh failed
```

## 📊 O que Esperar

✅ **100+ testes** devem passar  
✅ **Tempo**: ~15-30 segundos  
✅ **Cobertura**: 80%+  

## ⚠️ Se Algo Falhar

1. Verifique instalação: `pip list | grep pytest`
2. Verifique Python: `python --version` (3.8+)
3. Veja logs detalhados: `pytest tests/ -v -s`
4. Consulte `TESTING.md` para troubleshooting

## 📚 Próximos Passos

1. ✅ Execute os testes
2. 📖 Leia `TESTING.md` para guia completo
3. 💡 Veja `TESTING_EXAMPLES.py` para exemplos
4. 🚀 Adicione testes para novas features

## 🎉 Parabéns!

Você tem agora uma suíte de testes profissional! 

**Desenvolvido para Embryotech - Outside Agrotech** 🌱
