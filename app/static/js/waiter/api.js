/**
 * WaiterAPI - API для официантов
 */

class WaiterAPI {
    constructor() {
        this.baseUrl = ''; // Убираем базовый URL, будем использовать полные пути
        this.token = this.getAuthToken();
        
        // Привязываем все методы к контексту класса
        this.getDashboardStats = this.getDashboardStats.bind(this);

        this.getCalls = this.getCalls.bind(this);
        this.getOrders = this.getOrders.bind(this);
        this.getTables = this.getTables.bind(this);
        this.respondToCall = this.respondToCall.bind(this);
    }

    /**
     * Получение токена авторизации
     */
    getAuthToken() {
        // Для сессионной авторизации токен не нужен
        return null;
    }

    /**
     * Выполнение HTTP запроса
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin' // Включаем cookies для сессий
        };

        const requestOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        try {
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API Error for ${endpoint}:`, error);
            throw error;
        }
    }

    /**
     * GET запрос
     */
    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    /**
     * POST запрос
     */
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT запрос
     */
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE запрос
     */
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // === DASHBOARD API ===

    /**
     * Получение статистики дашборда
     */
    async getDashboardStats() {
        return this.get('/waiter/api/dashboard/stats');
    }

    // === ORDERS API ===

    /**
     * Получение списка заказов
     */
    async getOrders(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        const endpoint = queryParams ? `/waiter/api/orders?${queryParams}` : '/waiter/api/orders';
        return this.get(endpoint);
    }

    /**
     * Получение заказа по ID
     */
    async getOrder(orderId) {
        return this.get(`/waiter/api/orders/${orderId}`);
    }

    /**
     * Обновление статуса заказа
     */
    async updateOrderStatus(orderId, status) {
        return this.put(`/orders/${orderId}/status`, { status });
    }

    // === TABLES API ===

    /**
     * Получение списка столов
     */
    async getTables() {
        return this.get('/waiter/api/tables');
    }

    /**
     * Получение стола по ID
     */
    async getTable(tableId) {
        return this.get(`/tables/${tableId}`);
    }

    // === CALLS API ===

    /**
     * Получение вызовов официанта
     */
    async getCalls(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        const endpoint = queryParams ? `/waiter/api/calls?${queryParams}` : '/waiter/api/calls';
        return this.get(endpoint);
    }

    /**
     * Ответ на вызов
     */
    async respondToCall(callId, action = 'respond') {
        return this.put(`/calls/${callId}`, { action });
    }


}

// Глобальный экземпляр API
window.WaiterAPI = new WaiterAPI();
