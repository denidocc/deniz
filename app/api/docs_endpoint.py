"""
Endpoint для отображения документации API.

Предоставляет Swagger UI для интерактивного просмотра API документации.
"""

from flask import Blueprint, jsonify, render_template_string
from .docs import API_DOCS

# Создание blueprint для документации
docs_api = Blueprint('docs_api', __name__)

# HTML шаблон для Swagger UI
SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DENIZ Restaurant API - Документация</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin:0;
            background: #fafafa;
        }
        .swagger-ui .topbar {
            background-color: #4A90E2;
        }
        .swagger-ui .topbar .download-url-wrapper .select-label {
            color: white;
        }
        .swagger-ui .topbar .download-url-wrapper input[type=text] {
            border: 2px solid #2E5BBA;
        }
        .swagger-ui .info .title {
            color: #2E5BBA;
        }
        .swagger-ui .scheme-container {
            background-color: #7FB069;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/api/docs.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                docExpansion: "list",
                filter: true,
                showExtensions: true,
                showCommonExtensions: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                tryItOutEnabled: true
            });
        };
    </script>
</body>
</html>
"""


@docs_api.route('/api/docs')
def api_docs_ui():
    """
    Отображение Swagger UI для интерактивной документации API.
    
    Returns:
        HTML страница с Swagger UI
    """
    return render_template_string(SWAGGER_UI_TEMPLATE)


@docs_api.route('/api/docs.json')
def api_docs_json():
    """
    Возвращает OpenAPI спецификацию в формате JSON.
    
    Returns:
        JSON объект с OpenAPI спецификацией
    """
    return jsonify(API_DOCS) 