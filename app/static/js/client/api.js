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
    }

    /**
     * Выполнение HTTP запроса
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            method: 'GET',
            headers: { ...this.defaultHeaders },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * Получение меню
     */
    async getMenu(params = {}) {
        // Полный список блюд (заглушка)
        const allDishes = [
            // Блюда из рыбы (category_id: 1)
            { id: 1, name: 'Лосось на гриле', description: 'Свежий лосось с травами и лимоном', price: 890, image_url: '/static/assets/images/fish.png', category_id: 1, prep_time: 25, allergens: ['fish'], spicy_level: 0 },
            { id: 2, name: 'Дорадо в соли', description: 'Запеченная в морской соли дорадо', price: 1200, image_url: '/static/assets/images/fish.png', category_id: 1, prep_time: 30, allergens: ['fish'], spicy_level: 0 },
            { id: 3, name: 'Тунец стейк', description: 'Обжаренный стейк из тунца', price: 1500, image_url: '/static/assets/images/fish.png', category_id: 1, prep_time: 20, allergens: ['fish'], spicy_level: 0 },
            
            // Морепродукты (category_id: 2)
            { id: 4, name: 'Креветки темпура', description: 'Хрустящие креветки в кляре с соусом', price: 750, image_url: '/static/assets/images/fish.png', category_id: 2, prep_time: 15, allergens: ['seafood', 'gluten'], spicy_level: 1 },
            { id: 5, name: 'Устрицы свежие', description: 'Свежие устрицы с лимоном', price: 450, image_url: '/static/assets/images/fish.png', category_id: 2, prep_time: 5, allergens: ['seafood'], spicy_level: 0 },
            { id: 6, name: 'Мидии в белом вине', description: 'Тушеные мидии в белом вине', price: 650, image_url: '/static/assets/images/fish.png', category_id: 2, prep_time: 20, allergens: ['seafood'], spicy_level: 0 },
            { id: 7, name: 'Кальмары на гриле', description: 'Нежные кольца кальмаров', price: 580, image_url: '/static/assets/images/fish.png', category_id: 2, prep_time: 12, allergens: ['seafood'], spicy_level: 0 },
            
            // Мясные блюда (category_id: 3)
            { id: 8, name: 'Стейк рибай', description: 'Сочный стейк из мраморной говядины', price: 2500, image_url: '/static/assets/images/fish.png', category_id: 3, prep_time: 25, allergens: [], spicy_level: 0 },
            { id: 9, name: 'Баранина на кости', description: 'Ароматная баранина с розмарином', price: 1800, image_url: '/static/assets/images/fish.png', category_id: 3, prep_time: 35, allergens: [], spicy_level: 0 },
            
            // Паста (category_id: 4)  
            { id: 10, name: 'Паста с лобстером', description: 'Паста с мясом лобстера в сливочном соусе', price: 1350, image_url: '/static/assets/images/fish.png', category_id: 4, prep_time: 20, allergens: ['seafood', 'gluten', 'dairy'], spicy_level: 0 },
            { id: 11, name: 'Карбонара классическая', description: 'Традиционная римская паста', price: 780, image_url: '/static/assets/images/fish.png', category_id: 4, prep_time: 15, allergens: ['gluten', 'dairy', 'eggs'], spicy_level: 0 }
        ];
        
        // Фильтрация по категории
        let filteredDishes = allDishes;
        if (params.category_id) {
            filteredDishes = allDishes.filter(dish => dish.category_id === parseInt(params.category_id));
        }
        
        // Фильтрация по поиску
        if (params.search) {
            const searchTerm = params.search.toLowerCase();
            filteredDishes = filteredDishes.filter(dish => 
                dish.name.toLowerCase().includes(searchTerm) ||
                dish.description.toLowerCase().includes(searchTerm)
            );
        }
        
        // Подсчет блюд по категориям
        const categories = [
            { id: 1, name: 'Блюда из рыбы', count: allDishes.filter(d => d.category_id === 1).length },
            { id: 2, name: 'Морепродукты', count: allDishes.filter(d => d.category_id === 2).length },
            { id: 3, name: 'Мясные блюда', count: allDishes.filter(d => d.category_id === 3).length },
            { id: 4, name: 'Паста', count: allDishes.filter(d => d.category_id === 4).length }
        ];
        
        return {
            status: 'success',
            data: {
                categories: categories,
                dishes: filteredDishes
            }
        };
        
        // Реальный API вызов (закомментирован)
        // const searchParams = new URLSearchParams();
        // if (params.lang) searchParams.append('lang', params.lang);
        // if (params.category_id) searchParams.append('category_id', params.category_id);
        // if (params.search) searchParams.append('search', params.search);
        // const endpoint = `/client/api/menu${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
        // return this.request(endpoint);
    }

    /**
     * Получение списка столов
     */
    async getTables() {
        // Временная заглушка с тестовыми данными
        return {
            status: 'success',
            data: {
                tables: [
                    { id: 1, table_number: 1, is_available: true, seats: 2 },
                    { id: 2, table_number: 2, is_available: true, seats: 4 },
                    { id: 3, table_number: 3, is_available: false, seats: 6 },
                    { id: 4, table_number: 4, is_available: true, seats: 4 },
                    { id: 5, table_number: 5, is_available: true, seats: 2 },
                    { id: 6, table_number: 6, is_available: false, seats: 8 },
                    { id: 7, table_number: 7, is_available: true, seats: 4 },
                    { id: 8, table_number: 8, is_available: true, seats: 6 },
                    { id: 9, table_number: 9, is_available: true, seats: 2 },
                    { id: 10, table_number: 10, is_available: true, seats: 4 }
                ]
            }
        };
        
        // Реальный API вызов (закомментирован)
        // return this.request('/client/api/tables');
    }

    /**
     * Проверка PIN-кода стола
     */
    async verifyTablePin(pin) {
        // Временная заглушка - принимаем только PIN 2112
        if (pin === '2112') {
            return {
                status: 'success',
                message: 'PIN-код верный'
            };
        } else {
            return {
                status: 'error',
                message: 'Неверный PIN-код'
            };
        }
        
        // Реальный API вызов (закомментирован)
        // return this.request('/client/api/verify-table-pin', {
        //     method: 'POST',
        //     body: JSON.stringify({ pin })
        // });
    }

    /**
     * Получение настроек клиента
     */
    async getSettings() {
        return this.request('/client/api/settings');
    }

    async getCarouselSettings() {
        // Временная заглушка пока нет backend endpoint
        return {
            status: 'success',
            data: {
                autoplay: true,
                interval: 5000,
                showDots: true,
                showNavigation: false
            }
        };
        // return this.request('/client/api/carousel/settings');
    }

    /**
     * Проверка бонусной карты
     */
    async verifyBonusCard(cardNumber) {
        return this.request('/api/bonus-cards/verify', {
            method: 'POST',
            body: JSON.stringify({ card_number: cardNumber })
        });
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
    async callWaiter(tableId) {
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

        // Показываем уведомление об ошибке
        NotificationManager.showError(message);
        
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
    console.log('🔧 ClientAPI initialized successfully:', !!window.ClientAPI);
    console.log('🔧 getMenu method type:', typeof window.ClientAPI.getMenu);
    console.log('🔧 getCarouselSettings method type:', typeof window.ClientAPI.getCarouselSettings);
    
    // Добавляем флаг готовности
    window.ClientAPI._ready = true;
} catch (error) {
    console.error('🚨 Failed to initialize ClientAPI:', error);
}

// Экспортируем утилиты
window.APIUtils = APIUtils;