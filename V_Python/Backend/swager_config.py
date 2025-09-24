"""
Configurações avançadas para Swagger/Flasgger
Este arquivo contém configurações personalizadas para documentação da API
"""

# Configuração principal do Swagger
SWAGGER_CONFIG = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,  # Documenta todas as rotas
            "model_filter": lambda tag: True,  # Inclui todos os modelos
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/",  # URL principal da documentação
    "url_prefix": None,
    "swagger_ui_css": "/flasgger_static/swagger-ui.css",
    "swagger_ui_bundle_js": "/flasgger_static/swagger-ui-bundle.js",
    "swagger_ui_standalone_preset_js": "/flasgger_static/swagger-ui-standalone-preset.js",
    "jquery_js": "/flasgger_static/lib/jquery.min.js",
}

# Template principal do Swagger
SWAGGER_TEMPLATE = {
    "swagger": "2.0",
    "info": {
        "title": "Embryotech API",
        "description": """
        ## Sistema de Monitoramento de Embriões
        
        Esta API fornece funcionalidades completas para:
        
        - **Autenticação**: Login/logout com tokens JWT
        - **Gestão de Usuários**: Registro, listagem e administração de usuários
        - **Leituras**: CRUD completo para leituras de sensores (temperatura, umidade, pressão)
        - **Parâmetros**: Gestão de parâmetros ideais por empresa e lote
        - **Relatórios**: Geração de relatórios em PDF
        - **Auditoria**: Logs completos de todas as ações do sistema
        
        ### Autenticação
        
        Para usar a API, você precisa:
        1. Fazer login em `/api/login` com username e password
        2. Usar o token JWT retornado no header `Authorization: Bearer {token}`
        3. Incluir este token em todas as requisições protegidas
        
        ### Permissões
        
        - **Usuários comuns**: Podem gerenciar leituras e visualizar dados
        - **Administradores**: Acesso completo a todas as funcionalidades
        
        ### Formatos de Data
        
        Use o formato ISO 8601 para datas: `YYYY-MM-DDTHH:mm:ss` ou `YYYY-MM-DD`
        """,
        "contact": {
            "responsibleOrganization": "Embryotech",
            "responsibleDeveloper": "Equipe de Desenvolvimento",
            "email": "suporte@embryotech.com",
            "url": "https://embryotech.com",
        },
        "termsOfService": "https://embryotech.com/termos",
        "version": "2.0.0",
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "host": "localhost:5001",  # Será substituído dinamicamente
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ],
    "consumes": [
        "application/json"
    ],
    "produces": [
        "application/json",
        "application/pdf"
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": """
            Token de autorização JWT obtido através do endpoint `/api/login`.
            
            **Formato:** `Bearer {seu_token_jwt_aqui}`
            
            **Exemplo:** `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`
            """
        }
    },
    "tags": [
        {
            "name": "Sistema",
            "description": "Endpoints de informações do sistema"
        },
        {
            "name": "Autenticação",
            "description": "Login, logout e gestão de tokens JWT"
        },
        {
            "name": "Usuários",
            "description": "Gestão de usuários do sistema"
        },
        {
            "name": "Leituras",
            "description": "CRUD de leituras de sensores (temperatura, umidade, pressão)"
        },
        {
            "name": "Parâmetros",
            "description": "Gestão de parâmetros ideais por empresa e lote"
        },
        {
            "name": "Logs",
            "description": "Sistema de auditoria e logs de atividades"
        },
        {
            "name": "Relatórios",
            "description": "Geração de relatórios em PDF"
        }
    ],
    "responses": {
        "ParseError": {
            "description": "Erro de parsing dos dados enviados",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Dados JSON inválidos"
                    }
                }
            }
        },
        "MaskError": {
            "description": "Erro de validação dos dados",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Campo obrigatório não informado"
                    }
                }
            }
        },
        "UnauthorizedError": {
            "description": "Token inválido ou ausente",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Token is missing or invalid!"
                    }
                }
            }
        },
        "ForbiddenError": {
            "description": "Acesso negado - privilégios insuficientes",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Acesso negado!"
                    }
                }
            }
        },
        "NotFoundError": {
            "description": "Recurso não encontrado",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Recurso não encontrado"
                    }
                }
            }
        }
    },
    "paths": {},
    "definitions": {
        "User": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "ID único do usuário"
                },
                "username": {
                    "type": "string",
                    "description": "Nome de usuário único"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Email do usuário"
                },
                "is_admin": {
                    "type": "boolean",
                    "description": "Se o usuário possui privilégios administrativos"
                }
            }
        },
        "Leitura": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "ID único da leitura"
                },
                "temperatura": {
                    "type": "number",
                    "format": "float",
                    "description": "Temperatura em graus Celsius"
                },
                "umidade": {
                    "type": "number",
                    "format": "float",
                    "description": "Umidade relativa em porcentagem"
                },
                "pressao": {
                    "type": "number",
                    "format": "float",
                    "description": "Pressão atmosférica em hPa"
                },
                "lote": {
                    "type": "string",
                    "description": "Identificador do lote"
                },
                "data_inicial": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Data/hora inicial da leitura"
                },
                "data_final": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Data/hora final da leitura"
                }
            }
        },
        "Parametro": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "ID único do parâmetro"
                },
                "empresa": {
                    "type": "string",
                    "description": "Nome da empresa"
                },
                "lote": {
                    "type": "string",
                    "description": "Identificador do lote"
                },
                "temp_ideal": {
                    "type": "number",
                    "format": "float",
                    "description": "Temperatura ideal em °C"
                },
                "umid_ideal": {
                    "type": "number",
                    "format": "float",
                    "description": "Umidade ideal em %"
                },
                "pressao_ideal": {
                    "type": "number",
                    "format": "float",
                    "description": "Pressão ideal em hPa"
                },
                "lumens": {
                    "type": "number",
                    "format": "float",
                    "description": "Iluminação em lumens"
                },
                "id_sala": {
                    "type": "string",
                    "description": "Identificador da sala"
                },
                "estagio_ovo": {
                    "type": "string",
                    "description": "Estágio de desenvolvimento do ovo"
                }
            }
        },
        "Log": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "ID único do log"
                },
                "usuario_id": {
                    "type": "integer",
                    "description": "ID do usuário que executou a ação"
                },
                "usuario_nome": {
                    "type": "string",
                    "description": "Nome do usuário"
                },
                "acao": {
                    "type": "string",
                    "description": "Ação executada"
                },
                "data_hora": {
                    "type": "string",
                    "format": "date-time",
                    "description": "Data/hora da ação"
                },
                "ip_address": {
                    "type": "string",
                    "description": "Endereço IP de origem"
                },
                "status_code": {
                    "type": "integer",
                    "description": "Código de status HTTP"
                },
                "dados_adicionais": {
                    "type": "object",
                    "description": "Dados adicionais da ação"
                }
            }
        },
        "Error": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensagem de erro"
                }
            }
        },
        "Success": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensagem de sucesso"
                }
            }
        }
    }
}

# Configurações de estilo personalizadas
SWAGGER_CSS = """
.swagger-ui .topbar {
    background-color: #25691b;
}

.swagger-ui .info .title {
    color: #25691b;
}

.swagger-ui .scheme-container {
    background: #f7f7f7;
    border: 1px solid #d3d3d3;
}

.swagger-ui .opblock.opblock-post {
    border-color: #25691b;
}

.swagger-ui .opblock.opblock-post .opblock-summary-method {
    background: #25691b;
}

.swagger-ui .opblock.opblock-get {
    border-color: #61affe;
}

.swagger-ui .opblock.opblock-put {
    border-color: #fca130;
}

.swagger-ui .opblock.opblock-delete {
    border-color: #f93e3e;
}

.swagger-ui .btn.authorize {
    background-color: #25691b;
    border-color: #25691b;
}

.swagger-ui .btn.authorize:hover {
    background-color: #1e5517;
    border-color: #1e5517;
}
"""

# Exemplos de requests para diferentes endpoints
SWAGGER_EXAMPLES = {
    "login_example": {
        "username": "admin",
        "password": "senha123"
    },
    "register_example": {
        "username": "novo_usuario",
        "email": "usuario@email.com",
        "password": "minhasenha123"
    },
    "leitura_example": {
        "temperatura": 37.8,
        "umidade": 65.5,
        "pressao": 1013.2,
        "lote": "LOTE_001",
        "data_inicial": "2024-01-15T10:00:00",
        "data_final": "2024-01-15T11:00:00"
    },
    "parametro_example": {
        "empresa": "Outside Agrotech",
        "lote": "LOTE_001",
        "temp_ideal": 37.8,
        "umid_ideal": 65.0,
        "pressao_ideal": 1013.2,
        "lumens": 1200,
        "id_sala": "SALA_A1",
        "estagio_ovo": "incubacao_inicial"
    }
}