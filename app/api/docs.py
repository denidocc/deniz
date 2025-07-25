"""
Документация API для DENIZ Restaurant.

OpenAPI/Swagger спецификация для всех API endpoints.
"""

API_DOCS = {
    "openapi": "3.0.0",
    "info": {
        "title": "DENIZ Restaurant API",
        "description": "REST API для системы заказов ресторана DENIZ",
        "version": "1.0.0",
        "contact": {
            "name": "DENIZ Restaurant",
            "email": "info@deniz-restaurant.com"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000",
            "description": "Development server"
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
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "example": "error"
                    },
                    "message": {
                        "type": "string",
                        "example": "Описание ошибки"
                    },
                    "data": {
                        "type": "object",
                        "example": {}
                    }
                }
            }
        }
    }
} 