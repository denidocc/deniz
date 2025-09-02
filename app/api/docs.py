"""
Документация API для DENIZ Restaurant.

OpenAPI/Swagger спецификация для всех API endpoints.
"""

API_DOCS = {
    "openapi": "3.0.0",
    "info": {
        "title": "DENIZ Restaurant API",
        "description": """
        REST API для системы заказов ресторана DENIZ.
        
        ## Функциональность:
        - 🍽️ Получение меню с многоязычной поддержкой (русский, туркменский, английский)
        - 🔍 Поиск и фильтрация блюд
        - 📊 Статистика меню
        - 📋 Управление заказами (планируется)
        - 🖨️ Интеграция с принтерами (планируется)
        
        ## Безопасность:
        - Rate limiting
        - Валидация входных данных
        - Защита от XSS и SQL инъекций
        - Логирование всех запросов
        
        ## Поддерживаемые языки:
        - `ru` - Русский (по умолчанию)
        - `tk` - Туркменский
        - `en` - Английский
        """,
        "version": "1.0.0",
        "contact": {
            "name": "DENIZ Restaurant",
            "email": "info@deniz-restaurant.com"
        },
        "license": {
            "name": "Proprietary",
            "url": "https://deniz-restaurant.com/license"
        }
    },
    "servers": [
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.deniz-restaurant.com",
            "description": "Production server"
        }
    ],
    "tags": [
        {
            "name": "Menu",
            "description": "API endpoints для работы с меню ресторана"
        },
        {
            "name": "Orders",
            "description": "API endpoints для управления заказами (планируется)"
        },
        {
            "name": "System",
            "description": "Системные API endpoints"
        }
    ],
    "paths": {
        "/api/menu": {
            "get": {
                "summary": "Получение полного меню",
                "description": "Возвращает структурированное меню с категориями и блюдами",
                "tags": ["Menu"],
                "parameters": [
                    {
                        "name": "lang",
                        "in": "query",
                        "description": "Язык интерфейса",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["ru", "tk", "en"],
                            "default": "ru"
                        }
                    },
                    {
                        "name": "category_id",
                        "in": "query",
                        "description": "ID конкретной категории для фильтрации",
                        "required": False,
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "preparation_type",
                        "in": "query",
                        "description": "Тип приготовления",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["kitchen", "bar"]
                        }
                    },
                    {
                        "name": "is_active",
                        "in": "query",
                        "description": "Только активные позиции",
                        "required": False,
                        "schema": {
                            "type": "boolean",
                            "default": True
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Меню успешно загружено",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {
                                            "type": "string",
                                            "example": "success"
                                        },
                                        "message": {
                                            "type": "string",
                                            "example": "Меню успешно загружено"
                                        },
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "categories": {
                                                    "type": "array",
                                                    "items": {
                                                        "$ref": "#/components/schemas/Category"
                                                    }
                                                },
                                                "total_categories": {
                                                    "type": "integer",
                                                    "example": 5
                                                },
                                                "total_items": {
                                                    "type": "integer",
                                                    "example": 25
                                                },
                                                "language": {
                                                    "type": "string",
                                                    "example": "ru"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Ошибка валидации",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    },
                    "500": {
                        "description": "Внутренняя ошибка сервера",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/system/info": {
            "get": {
                "summary": "Информация о системе",
                "description": "Получение общей информации о системе и версии API",
                "tags": ["System"],
                "responses": {
                    "200": {
                        "description": "Информация о системе",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {
                                            "type": "string",
                                            "example": "success"
                                        },
                                        "message": {
                                            "type": "string",
                                            "example": "Информация о системе"
                                        },
                                        "data": {
                                            "$ref": "#/components/schemas/SystemInfo"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/system/health": {
            "get": {
                "summary": "Проверка состояния системы",
                "description": "Healthcheck endpoint для мониторинга",
                "tags": ["System"],
                "responses": {
                    "200": {
                        "description": "Система работает нормально",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {
                                            "type": "string",
                                            "example": "healthy"
                                        },
                                        "timestamp": {
                                            "type": "string",
                                            "format": "date-time",
                                            "example": "2025-01-29T10:30:00Z"
                                        },
                                        "version": {
                                            "type": "string",
                                            "example": "1.0.0"
                                        },
                                        "uptime": {
                                            "type": "number",
                                            "description": "Время работы в секундах",
                                            "example": 3600.5
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "503": {
                        "description": "Система недоступна",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/ErrorResponse"
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "Category": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "example": 1
                    },
                    "name": {
                        "type": "string",
                        "example": "Горячие блюда"
                    },
                    "name_tk": {
                        "type": "string",
                        "example": "Ысык ашлар"
                    },
                    "name_en": {
                        "type": "string",
                        "example": "Hot dishes"
                    },
                    "sort_order": {
                        "type": "integer",
                        "example": 1
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/MenuItem"
                        }
                    },
                    "items_count": {
                        "type": "integer",
                        "example": 8
                    }
                }
            },
            "MenuItem": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "example": 15
                    },
                    "name": {
                        "type": "string",
                        "example": "Борщ классический"
                    },
                    "description": {
                        "type": "string",
                        "example": "Традиционный украинский борщ"
                    },
                    "price": {
                        "type": "number",
                        "format": "float",
                        "example": 300.00
                    },
                    "image_url": {
                        "type": "string",
                        "example": "/images/borsch.jpg"
                    },
                    "preparation_type": {
                        "type": "string",
                        "enum": ["kitchen", "bar"],
                        "example": "kitchen"
                    },
                    "estimated_time": {
                        "type": "integer",
                        "example": 15
                    },
                    "has_size_options": {
                        "type": "boolean",
                        "example": False
                    },
                    "can_modify_ingredients": {
                        "type": "boolean",
                        "example": True
                    },
                    "sort_order": {
                        "type": "integer",
                        "example": 1
                    },
                    "category": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "example": 1
                            },
                            "name": {
                                "type": "string",
                                "example": "Горячие блюда"
                            }
                        }
                    }
                }
            },
            "SystemInfo": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "example": "DENIZ Restaurant API"
                    },
                    "version": {
                        "type": "string",
                        "example": "1.0.0"
                    },
                    "build": {
                        "type": "string",
                        "example": "dev"
                    },
                    "environment": {
                        "type": "string",
                        "example": "development"
                    },
                    "features": {
                        "type": "object",
                        "properties": {
                            "menu_api": {
                                "type": "boolean",
                                "example": True
                            },
                            "orders_api": {
                                "type": "boolean",
                                "example": False
                            },
                            "auth_api": {
                                "type": "boolean",
                                "example": False
                            },
                            "printer_integration": {
                                "type": "boolean",
                                "example": False
                            }
                        }
                    },
                    "supported_languages": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "example": ["ru", "tk", "en"]
                    },
                    "database": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "example": "connected"
                            },
                            "type": {
                                "type": "string",
                                "example": "PostgreSQL"
                            }
                        }
                    }
                }
            },
            "ErrorResponse": {
                "type": "object",
                "required": ["status", "message", "data"],
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["error"],
                        "example": "error"
                    },
                    "message": {
                        "type": "string",
                        "example": "Описание ошибки"
                    },
                    "data": {
                        "type": "object",
                        "example": {}
                    },
                    "errors": {
                        "type": "object",
                        "description": "Детали ошибок валидации",
                        "example": {
                            "field_name": "Ошибка в поле"
                        }
                    },
                    "code": {
                        "type": "string",
                        "description": "Код ошибки для программной обработки",
                        "example": "VALIDATION_ERROR"
                    }
                }
            }
        }
    }
}