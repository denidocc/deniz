# API Documentation - DENIZ Restaurant

## Обзор

REST API для системы заказов ресторана DENIZ. API предоставляет endpoints для работы с меню, категориями блюд и поиском.

## Базовый URL

```
http://localhost:5000
```

## Аутентификация

В текущей версии API не требует аутентификации для доступа к меню.

## Endpoints

### 1. Получение полного меню

**GET** `/api/menu`

Возвращает структурированное меню с категориями и блюдами.

#### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `lang` | string | Нет | Язык интерфейса (ru/tk/en). По умолчанию 'ru' |
| `category_id` | integer | Нет | ID конкретной категории для фильтрации |
| `preparation_type` | string | Нет | Тип приготовления (kitchen/bar) |
| `is_active` | boolean | Нет | Только активные позиции. По умолчанию true |

#### Пример запроса

```bash
curl "http://localhost:5000/api/menu?lang=ru&preparation_type=kitchen"
```

#### Пример ответа

```json
{
  "status": "success",
  "message": "Меню успешно загружено",
  "data": {
    "categories": [
      {
        "id": 1,
        "name": "Горячие блюда",
        "name_tk": "Ысык ашлар",
        "name_en": "Hot dishes",
        "sort_order": 1,
        "items": [
          {
            "id": 1,
            "name": "Борщ классический",
            "description": "Традиционный украинский борщ с говядиной",
            "price": 300.00,
            "image_url": "/images/borsch.jpg",
            "preparation_type": "kitchen",
            "estimated_time": 20,
            "has_size_options": false,
            "can_modify_ingredients": true,
            "sort_order": 1
          }
        ],
        "items_count": 3
      }
    ],
    "total_categories": 5,
    "total_items": 10,
    "language": "ru",
    "filters": {
      "preparation_type": "kitchen",
      "is_active": true,
      "category_id": null
    }
  }
}
```

### 2. Получение списка категорий

**GET** `/api/menu/categories`

Возвращает все активные категории меню.

#### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `lang` | string | Нет | Язык интерфейса (ru/tk/en). По умолчанию 'ru' |
| `preparation_type` | string | Нет | Тип приготовления для фильтрации |

#### Пример запроса

```bash
curl "http://localhost:5000/api/menu/categories?lang=tk"
```

#### Пример ответа

```json
{
  "status": "success",
  "message": "Категории загружены",
  "data": {
    "categories": [
      {
        "id": 1,
        "name": "Ысык ашлар",
        "name_tk": "Ысык ашлар",
        "name_en": "Hot dishes",
        "sort_order": 1,
        "items_count": 3
      }
    ],
    "total_categories": 5,
    "language": "tk"
  }
}
```

### 3. Получение информации о блюде

**GET** `/api/menu/items/{item_id}`

Возвращает детальную информацию о конкретном блюде.

#### Параметры пути

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `item_id` | integer | Да | ID блюда |

#### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `lang` | string | Нет | Язык интерфейса (ru/tk/en). По умолчанию 'ru' |

#### Пример запроса

```bash
curl "http://localhost:5000/api/menu/items/15?lang=en"
```

#### Пример ответа

```json
{
  "status": "success",
  "message": "Информация о блюде загружена",
  "data": {
    "item": {
      "id": 15,
      "name": "Beef Steak",
      "description": "Juicy beef steak with vegetables",
      "price": 850.00,
      "image_url": "/images/steak.jpg",
      "preparation_type": "kitchen",
      "estimated_time": 25,
      "has_size_options": true,
      "can_modify_ingredients": true,
      "sort_order": 2,
      "sizes": [
        {
          "id": 1,
          "name": "Small portion",
          "price_modifier": 0.00
        },
        {
          "id": 2,
          "name": "Large portion",
          "price_modifier": 150.00
        }
      ],
      "category": {
        "id": 1,
        "name": "Hot dishes"
      }
    }
  }
}
```

### 4. Поиск блюд

**GET** `/api/menu/search`

Поиск блюд по названию и описанию.

#### Параметры запроса

| Параметр | Тип | Обязательный | Описание |
|----------|-----|--------------|----------|
| `q` | string | Да | Поисковый запрос |
| `lang` | string | Нет | Язык интерфейса (ru/tk/en). По умолчанию 'ru' |
| `category_id` | integer | Нет | Фильтр по категории |
| `preparation_type` | string | Нет | Фильтр по типу приготовления |

#### Пример запроса

```bash
curl "http://localhost:5000/api/menu/search?q=борщ&lang=ru&preparation_type=kitchen"
```

#### Пример ответа

```json
{
  "status": "success",
  "message": "Поиск выполнен",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "Борщ классический",
        "description": "Традиционный украинский борщ с говядиной",
        "price": 300.00,
        "image_url": "/images/borsch.jpg",
        "preparation_type": "kitchen",
        "estimated_time": 20,
        "category_id": 1
      }
    ],
    "total_found": 1,
    "query": "борщ",
    "language": "ru",
    "filters": {
      "category_id": null,
      "preparation_type": "kitchen"
    }
  }
}
```

### 5. Статистика меню

**GET** `/api/menu/stats`

Получение статистики меню.

#### Пример запроса

```bash
curl "http://localhost:5000/api/menu/stats"
```

#### Пример ответа

```json
{
  "status": "success",
  "message": "Статистика загружена",
  "data": {
    "total_categories": 5,
    "total_items": 10,
    "kitchen_items": 7,
    "bar_items": 3,
    "items_with_sizes": 2,
    "average_price": 450.50,
    "price_range": {
      "min": 100.00,
      "max": 850.00
    }
  }
}
```

## Коды ошибок

| Код | Описание |
|-----|----------|
| 200 | Успешный запрос |
| 400 | Ошибка валидации параметров |
| 404 | Ресурс не найден |
| 429 | Превышен лимит запросов |
| 500 | Внутренняя ошибка сервера |

## Формат ошибок

```json
{
  "status": "error",
  "message": "Описание ошибки",
  "data": {}
}
```

## Лимиты запросов

- `/api/menu` - 1000 запросов в час
- `/api/menu/categories` - 500 запросов в час
- `/api/menu/items/{id}` - 2000 запросов в час
- `/api/menu/search` - 300 запросов в час
- `/api/menu/stats` - 100 запросов в час

## Поддерживаемые языки

- `ru` - Русский (по умолчанию)
- `tk` - Туркменский
- `en` - Английский

## Типы приготовления

- `kitchen` - Кухня
- `bar` - Бар

## Интерактивная документация

Доступна по адресу: `http://localhost:5000/api/docs`

## Тестирование API

Для тестирования API можно использовать:

1. **cURL** - командная строка
2. **Postman** - GUI приложение
3. **Swagger UI** - встроенная документация по адресу `/api/docs`

### Примеры тестирования

```bash
# Получение меню на русском языке
curl "http://localhost:5000/api/menu?lang=ru"

# Поиск блюд
curl "http://localhost:5000/api/menu/search?q=стейк"

# Получение статистики
curl "http://localhost:5000/api/menu/stats"

# Получение конкретного блюда
curl "http://localhost:5000/api/menu/items/1"
```

## Структура данных

### Категория

```json
{
  "id": 1,
  "name": "Горячие блюда",
  "name_tk": "Ысык ашлар",
  "name_en": "Hot dishes",
  "sort_order": 1,
  "items": [...],
  "items_count": 3
}
```

### Блюдо

```json
{
  "id": 1,
  "name": "Борщ классический",
  "description": "Традиционный украинский борщ с говядиной",
  "price": 300.00,
  "image_url": "/images/borsch.jpg",
  "preparation_type": "kitchen",
  "estimated_time": 20,
  "has_size_options": false,
  "can_modify_ingredients": true,
  "sort_order": 1,
  "sizes": [...],
  "category": {...}
}
```

### Размер порции

```json
{
  "id": 1,
  "name": "Большая порция",
  "price_modifier": 150.00
}
``` 