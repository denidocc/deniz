/**
 * API модуль для клиентского интерфейса
 */

class ClientAPI {
    constructor() {
        this.baseUrl = '/client/api';
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };
        this.updateCSRFToken();
    }
    
    /**
     * Обновление CSRF токена из meta тега
     */
    updateCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        if (metaTag) {
            this.defaultHeaders['X-CSRFToken'] = metaTag.getAttribute('content');
        }
    }

    /**
     * Выполнение HTTP запроса
     */
    async request(endpoint, options = {}) {
        // Обновляем CSRF токен перед каждым запросом
        this.updateCSRFToken();
        
        // Если endpoint начинается с /api/, используем абсолютный путь без baseUrl
        const url = endpoint.startsWith('/api/') ? endpoint : `${this.baseUrl}${endpoint}`;
        const config = {
            method: 'GET',
            headers: { ...this.defaultHeaders },
            ...options
        };

        try {
            console.log(`Making request to: ${url}`, config);
            const response = await fetch(url, config);
            
            if (!response.ok) {
                // Пытаемся получить детали ошибки из ответа
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    if (errorData.message) {
                        errorMessage = errorData.message;
                    }
                } catch (jsonError) {
                    // Если не удалось распарсить JSON, используем стандартное сообщение
                }
                
                throw new Error(errorMessage);
            }
            
            const text = await response.text();
            if (!text) {
                throw new Error('Empty response');
            }
            
            try {
                const data = JSON.parse(text);
                return data;
            } catch (jsonError) {
                throw new Error(`Failed to decode JSON object: ${jsonError.message}`);
            }
            
        } catch (error) {
            console.error('Request failed:', error);
            throw error;
        }
    }

    /**
     * Получение меню
     */
    async getMenu(params = {}) {
        // Подготовка параметров запроса
        const searchParams = new URLSearchParams();
        if (params.lang) searchParams.append('lang', params.lang);
        if (params.category_id) searchParams.append('category_id', params.category_id);
        if (params.search) searchParams.append('search', params.search);
        
        const endpoint = `/menu${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
        return this.request(endpoint);
    }

    /**
     * Получение списка столов
     */
    async getTables() {
        return this.request('/tables');
    }

    /**
     * Проверка PIN-кода стола
     */
    async verifyTablePin(pin) {
        // Используем публичный клиентский эндпоинт без авторизации
        return this.request('/verify-table-pin', {
            method: 'POST',
            body: JSON.stringify({ pin })
        });
    }

    /**
     * Получение настроек клиента
     */
    async getSettings() {
        return this.request('/settings');
    }

    async getCarouselSettings() {
        return this.request('/carousel');
    }

    /**
     * Проверка бонусной карты
     */
    async verifyBonusCard(cardNumber) {
        return this.request('/api/bonus-cards/check', {
            method: 'POST',
            body: JSON.stringify({ card_number: cardNumber })
        });
    }

    /**
     * Применение бонусной карты
     */
    async applyBonusCard(cardNumber) {
        // Сначала проверяем карту
        const verifyResponse = await this.verifyBonusCard(cardNumber);
        
        if (verifyResponse.status === 'success') {
            // Применяем карту через CartManager
            if (window.CartManager && typeof window.CartManager.applyBonusCard === 'function') {
                window.CartManager.applyBonusCard(verifyResponse.data);
                return { status: 'success', message: 'Бонусная карта применена' };
            } else {
                throw new Error('CartManager не готов');
            }
        } else {
            throw new Error(verifyResponse.message || 'Карта недействительна');
        }
    }

    // Метод verifyTablePin перенесен выше с заглушкой

    // Метод getTables перенесен выше с заглушкой

    /**
     * Создание заказа
     */
    async createOrder(orderData) {
        return this.request('/orders', {
            method: 'POST',
            body: JSON.stringify(orderData)
        });
    }

    /**
     * Отмена заказа
     */
    async cancelOrder(orderId) {
        return this.request(`/orders/${orderId}/cancel`, {
            method: 'POST'
        });
    }

    /**
     * Вызов официанта
     */
    callWaiter = async (tableId) => {
        return this.request('/waiter-call', {
            method: 'POST',
            body: JSON.stringify({ table_id: tableId })
        });
    }

    /**
     * Получение слайдов карусели
     */
    async getCarouselSlides() {
        return this.request('/api/carousel/slides');
    }

    // Метод getCarouselSettings перенесен выше с заглушкой
}

// Старое создание экземпляра убрано - см. конец файла

/**
 * Утилиты для работы с API
 */
class APIUtils {
    /**
     * Обработка ошибок API
     */
    static handleError(error, defaultMessage = 'Произошла ошибка') {
        let message = defaultMessage;
        
        if (error.message) {
            message = error.message;
        } else if (typeof error === 'string') {
            message = error;
        }

        // Показываем уведомление об ошибке, если NotificationManager доступен
        if (window.NotificationManager && typeof window.NotificationManager.showError === 'function') {
            window.NotificationManager.showError(message);
        } else {
            console.warn('NotificationManager not available, showing alert instead');
            alert(message);
        }
        
        console.error('API Error:', error);
        return message;
    }

    /**
     * Показ состояния загрузки
     */
    static showLoading(element, text = 'Загрузка...') {
        if (element) {
            element.classList.add('loading');
            element.setAttribute('aria-busy', 'true');
            
            const loadingText = element.querySelector('.loading-text');
            if (loadingText) {
                loadingText.textContent = text;
            }
        }
    }

    /**
     * Скрытие состояния загрузки
     */
    static hideLoading(element) {
        if (element) {
            element.classList.remove('loading');
            element.removeAttribute('aria-busy');
        }
    }

    /**
     * Дебаунс для поиска
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Форматирование цены
     */
    static formatPrice(price, currency = 'тмт') {
        if (typeof price !== 'number') {
            price = parseFloat(price) || 0;
        }
        return `${price.toFixed(2)} ${currency}`;
    }

    /**
     * Форматирование времени приготовления
     */
    static formatPrepTime(minutes) {
        if (minutes < 60) {
            return `${minutes} мин`;
        }
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return `${hours}ч ${remainingMinutes}м`;
    }
}

// Создаем глобальный экземпляр API сразу
try {
    window.ClientAPI = new ClientAPI();
    window.ClientAPI._ready = true;
    console.log('✅ ClientAPI initialized successfully:', window.ClientAPI);
    console.log('✅ Available methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(window.ClientAPI)));
} catch (error) {
    console.error('❌ Failed to initialize ClientAPI:', error);
}

// Экспортируем утилиты
window.APIUtils = APIUtils;