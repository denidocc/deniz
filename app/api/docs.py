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
        - 👥 Система авторизации персонала (планируется)
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
            "name": "Auth",
            "description": "API endpoints для аутентификации персонала (планируется)"
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
        "/api/menu/categories": {
            "get": {
                "summary": "Получение списка категорий",
                "description": "Возвращает все активные категории меню",
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
                        "name": "preparation_type",
                        "in": "query",
                        "description": "Тип приготовления для фильтрации",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["kitchen", "bar"]
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Категории загружены",
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
                                            "example": "Категории загружены"
                                        },
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "categories": {
                                                    "type": "array",
                                                    "items": {
                                                        "$ref": "#/components/schemas/CategorySummary"
                                                    }
                                                },
                                                "total_categories": {
                                                    "type": "integer",
                                                    "example": 5
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
                    }
                }
            }
        },
        "/api/menu/items/{item_id}": {
            "get": {
                "summary": "Получение информации о блюде",
                "description": "Возвращает детальную информацию о конкретном блюде",
                "tags": ["Menu"],
                "parameters": [
                    {
                        "name": "item_id",
                        "in": "path",
                        "description": "ID блюда",
                        "required": True,
                        "schema": {
                            "type": "integer"
                        }
                    },
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
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Информация о блюде загружена",
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
                                            "example": "Информация о блюде загружена"
                                        },
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "item": {
                                                    "$ref": "#/components/schemas/MenuItem"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Блюдо не найдено",
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
        "/api/menu/search": {
            "get": {
                "summary": "Поиск блюд",
                "description": "Поиск блюд по названию и описанию",
                "tags": ["Menu"],
                "parameters": [
                    {
                        "name": "q",
                        "in": "query",
                        "description": "Поисковый запрос",
                        "required": True,
                        "schema": {
                            "type": "string"
                        }
                    },
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
                        "description": "Фильтр по категории",
                        "required": False,
                        "schema": {
                            "type": "integer"
                        }
                    },
                    {
                        "name": "preparation_type",
                        "in": "query",
                        "description": "Фильтр по типу приготовления",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "enum": ["kitchen", "bar"]
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Поиск выполнен",
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
                                            "example": "Поиск выполнен"
                                        },
                                        "data": {
                                            "type": "object",
                                            "properties": {
                                                "items": {
                                                    "type": "array",
                                                    "items": {
                                                        "$ref": "#/components/schemas/MenuItem"
                                                    }
                                                },
                                                "total_found": {
                                                    "type": "integer",
                                                    "example": 2
                                                },
                                                "query": {
                                                    "type": "string",
                                                    "example": "борщ"
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/menu/stats": {
            "get": {
                "summary": "Статистика меню",
                "description": "Получение статистики меню",
                "tags": ["Menu"],
                "responses": {
                    "200": {
                        "description": "Статистика загружена",
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
                                            "example": "Статистика загружена"
                                        },
                                        "data": {
                                            "$ref": "#/components/schemas/MenuStats"
                                        }
                                    }
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
            "CategorySummary": {
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
                    "sizes": {
                        "type": "array",
                        "items": {
                            "$ref": "#/components/schemas/MenuItemSize"
                        }
                    },
                    "category": {
                        "$ref": "#/components/schemas/CategorySummary"
                    }
                }
            },
            "MenuItemSize": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "example": 1
                    },
                    "name": {
                        "type": "string",
                        "example": "Большая порция"
                    },
                    "price_modifier": {
                        "type": "number",
                        "format": "float",
                        "example": 50.00
                    }
                }
            },
            "MenuStats": {
                "type": "object",
                "properties": {
                    "total_categories": {
                        "type": "integer",
                        "example": 5
                    },
                    "total_items": {
                        "type": "integer",
                        "example": 25
                    },
                    "kitchen_items": {
                        "type": "integer",
                        "example": 18
                    },
                    "bar_items": {
                        "type": "integer",
                        "example": 7
                    },
                    "items_with_sizes": {
                        "type": "integer",
                        "example": 3
                    },
                    "average_price": {
                        "type": "number",
                        "format": "float",
                        "example": 450.50
                    },
                    "price_range": {
                        "type": "object",
                        "properties": {
                            "min": {
                                "type": "number",
                                "format": "float",
                                "example": 50.00
                            },
                            "max": {
                                "type": "number",
                                "format": "float",
                                "example": 1200.00
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