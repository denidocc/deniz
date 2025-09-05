/**
 * ClientWebSocket - Класс для обработки WebSocket соединений на клиентской стороне
 * Обеспечивает безшовное обновление контента при изменениях в админке
 */

class ClientWebSocket {
    constructor() {
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
        this.isConnected = false;
        
        console.log('🔌 Инициализация ClientWebSocket');
        this.init();
    }
    
    init() {
        try {
            // Подключаемся к WebSocket серверу
            this.socket = io();
            
            // Обработчики событий подключения
            this.socket.on('connect', () => {
                console.log('✅ WebSocket подключен');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                // Присоединяемся к комнате клиентов
                this.socket.emit('join_client_room');
            });
            
            this.socket.on('disconnect', () => {
                console.log('❌ WebSocket отключен');
                this.isConnected = false;
                this.handleReconnect();
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('🚫 Ошибка подключения WebSocket:', error);
                this.isConnected = false;
                this.handleReconnect();
            });
            
            // Основной слушатель обновлений контента
            this.socket.on('content_updated', (data) => {
                this.handleContentUpdate(data);
            });
            
            // Подтверждение присоединения к комнате
            this.socket.on('joined_client_room', (data) => {
                console.log('🏠 Присоединились к клиентской комнате:', data.message);
            });
            
        } catch (error) {
            console.error('💥 Ошибка инициализации WebSocket:', error);
        }
    }
    
    /**
     * Обработка обновлений контента
     * @param {Object} data - Данные об обновлении
     */
    handleContentUpdate(data) {
        console.log('🔄 Получено обновление контента:', data);
        
        // Определяем тип обновления и действие
        const { type, action, message } = data;
        
        switch (type) {
            case 'menu':
                this.handleMenuUpdate(action, message);
                break;
                
            case 'category':
                this.handleCategoryUpdate(action, message);
                break;
                
            case 'banner':
                this.handleBannerUpdate(action, message);
                break;
                
            case 'settings':
                this.handleSettingsUpdate(action, message);
                break;
                
            default:
                // Универсальное обновление для любых других изменений
                this.handleGenericUpdate(message);
                break;
        }
    }
    
    /**
     * Обработка обновлений меню
     */
    handleMenuUpdate(action, message) {
        console.log(`🍽️ Обновление меню: ${action}`);
        
        // Обновляем меню на странице
        if (typeof window.loadMenu === 'function') {
            window.loadMenu();
        } else if (typeof window.refreshMenuData === 'function') {
            window.refreshMenuData();
        } else {
            // Fallback: перезагружаем страницу
            this.reloadPage();
        }
    }
    
    /**
     * Обработка обновлений категорий
     */
    handleCategoryUpdate(action, message) {
        console.log(`📂 Обновление категорий: ${action}`);
        
        // Обновляем категории на странице
        if (typeof window.loadCategories === 'function') {
            window.loadCategories();
        } else {
            this.reloadPage();
        }
    }
    
    /**
     * Обработка обновлений баннеров
     */
    handleBannerUpdate(action, message) {
        console.log(`🎨 Обновление баннеров: ${action}`);
        
        // Обновляем карусель баннеров
        if (typeof window.reloadCarousel === 'function') {
            window.reloadCarousel();
        } else if (window.carousel && typeof window.carousel.reload === 'function') {
            window.carousel.reload();
        } else {
            this.reloadPage();
        }
    }
    
    /**
     * Обработка обновлений настроек
     */
    handleSettingsUpdate(action, message) {
        console.log(`⚙️ Обновление настроек: ${action}`);
        
        // Настройки могут влиять на всё - перезагружаем страницу
        this.reloadPage();
    }
    
    /**
     * Универсальная обработка обновлений
     */
    handleGenericUpdate(message) {
        console.log(`🔄 Универсальное обновление: ${message}`);
        
        // Пробуем найти и вызвать функцию обновления
        const updateFunctions = [
            'refreshPage',
            'reloadContent', 
            'updateContent',
            'loadData'
        ];
        
        let updated = false;
        for (const funcName of updateFunctions) {
            if (typeof window[funcName] === 'function') {
                window[funcName]();
                updated = true;
                break;
            }
        }
        
        if (!updated) {
            this.reloadPage();
        }
    }
    
    /**
     * Безшовная перезагрузка страницы
     */
    reloadPage() {
        console.log('🔄 Выполняем безшовное обновление страницы');
        
        // Добавляем небольшую задержку для плавности
        setTimeout(() => {
            window.location.reload();
        }, 500);
    }
    
    /**
     * Обработка переподключения
     */
    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`🔄 Попытка переподключения ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            
            setTimeout(() => {
                this.init();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('💥 Превышено максимальное количество попыток переподключения');
        }
    }
    
    /**
     * Проверка состояния подключения
     */
    isSocketConnected() {
        return this.isConnected && this.socket && this.socket.connected;
    }
    
    /**
     * Отключение WebSocket
     */
    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.isConnected = false;
        console.log('🔌 WebSocket отключен вручную');
    }
}

// Глобальная инициализация
let clientWebSocket = null;

// Инициализируем WebSocket при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 Инициализация клиентского WebSocket');
    clientWebSocket = new ClientWebSocket();
});

// Экспорт для использования в других скриптах
window.ClientWebSocket = ClientWebSocket;
window.clientWebSocket = clientWebSocket;
