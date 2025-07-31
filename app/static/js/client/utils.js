/**
 * Утилиты для клиентского интерфейса
 */

/**
 * Основной класс приложения
 */
class ClientApp {
    static init() {
        console.log('🚀 Initializing DENIZ Client App');
        
        // Инициализируем базовые компоненты
        this.initializeComponents();
        
        // Устанавливаем обработчики событий
        this.setupEventListeners();
        
        // Загружаем настройки
        this.loadSettings();
        
        console.log('✅ Client App initialized');
    }

    static initializeComponents() {
        // Инициализируем систему уведомлений
        NotificationManager.init();
        
        // Инициализируем модальные окна
        ModalManager.init();
        
        // Инициализируем корзину
        CartManager.init();
    }

    static setupEventListeners() {
        // Обработчик ошибок JavaScript
        window.addEventListener('error', (event) => {
            console.error('JavaScript Error:', event.error);
            NotificationManager.showError('Произошла ошибка приложения');
        });

        // Обработчик нажатий клавиш
        document.addEventListener('keydown', (event) => {
            // ESC - закрытие модальных окон
            if (event.key === 'Escape') {
                ModalManager.closeAll();
            }
        });

        // Обработчик изменения ориентации
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleOrientationChange();
            }, 100);
        });
    }

    static async loadSettings() {
        try {
            const response = await ClientAPI.getSettings();
            if (response.status === 'success') {
                window.CLIENT_SETTINGS = response.data;
                this.applySettings(response.data);
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    }

    static applySettings(settings) {
        // Применяем CSS переменные из настроек
        const root = document.documentElement;
        
        if (settings.carousel_slide_duration) {
            root.style.setProperty('--carousel-slide-duration', `${settings.carousel_slide_duration}s`);
        }
        
        if (settings.carousel_transition_speed) {
            root.style.setProperty('--carousel-transition-speed', `${settings.carousel_transition_speed}s`);
        }
        
        if (settings.service_charge_percent) {
            root.style.setProperty('--service-charge-percent', settings.service_charge_percent);
        }
        
        if (settings.order_cancel_timeout) {
            root.style.setProperty('--order-cancel-timeout', settings.order_cancel_timeout);
        }
    }

    static handleOrientationChange() {
        // Обновляем layout при изменении ориентации
        document.body.classList.toggle('landscape', window.innerWidth > window.innerHeight);
        document.body.classList.toggle('portrait', window.innerHeight > window.innerWidth);
        
        // Триггерим событие для других компонентов
        window.dispatchEvent(new CustomEvent('orientationChanged'));
    }
}

/**
 * Менеджер уведомлений
 */
class NotificationManager {
    static init() {
        this.container = this.createContainer();
        this.notifications = new Map();
    }

    static createContainer() {
        let container = document.getElementById('notificationContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        return container;
    }

    static show(message, type = 'info', duration = 5000) {
        const id = Date.now() + Math.random();
        const notification = this.createNotification(id, message, type);
        
        this.container.appendChild(notification);
        this.notifications.set(id, notification);
        
        // Анимация появления
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Автоматическое скрытие
        if (duration > 0) {
            setTimeout(() => {
                this.hide(id);
            }, duration);
        }
        
        return id;
    }

    static createNotification(id, message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.setAttribute('data-id', id);
        
        const icon = this.getIcon(type);
        notification.innerHTML = `
            <div class="notification-icon">${icon}</div>
            <div class="notification-content">
                <div class="notification-message">${message}</div>
            </div>
            <button class="notification-close" onclick="NotificationManager.hide(${id})">
                <svg viewBox="0 0 24 24" width="16" height="16">
                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
            </button>
        `;
        
        return notification;
    }

    static getIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    static hide(id) {
        const notification = this.notifications.get(id);
        if (notification) {
            notification.classList.add('hide');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications.delete(id);
            }, 300);
        }
    }

    static showSuccess(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    static showError(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    static showWarning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }

    static showInfo(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }

    static clear() {
        this.notifications.forEach((notification, id) => {
            this.hide(id);
        });
    }
}

/**
 * Менеджер локального хранилища
 */
class StorageManager {
    static set(key, value) {
        try {
            const serializedValue = JSON.stringify(value);
            localStorage.setItem(`deniz_${key}`, serializedValue);
            return true;
        } catch (error) {
            console.error('Storage set error:', error);
            return false;
        }
    }

    static get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(`deniz_${key}`);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Storage get error:', error);
            return defaultValue;
        }
    }

    static remove(key) {
        try {
            localStorage.removeItem(`deniz_${key}`);
            return true;
        } catch (error) {
            console.error('Storage remove error:', error);
            return false;
        }
    }

    static clear() {
        try {
            const keys = Object.keys(localStorage);
            keys.forEach(key => {
                if (key.startsWith('deniz_')) {
                    localStorage.removeItem(key);
                }
            });
            return true;
        } catch (error) {
            console.error('Storage clear error:', error);
            return false;
        }
    }
}

/**
 * Утилиты для работы с DOM
 */
class DOMUtils {
    /**
     * Создание элемента с атрибутами
     */
    static createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        Object.keys(attributes).forEach(key => {
            if (key === 'className') {
                element.className = attributes[key];
            } else if (key === 'innerHTML') {
                element.innerHTML = attributes[key];
            } else if (key === 'textContent') {
                element.textContent = attributes[key];
            } else {
                element.setAttribute(key, attributes[key]);
            }
        });
        
        if (content) {
            element.innerHTML = content;
        }
        
        return element;
    }

    /**
     * Безопасное удаление элемента
     */
    static removeElement(element) {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    }

    /**
     * Анимация скролла к элементу
     */
    static scrollToElement(element, offset = 0) {
        if (!element) return;
        
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }

    /**
     * Проверка видимости элемента
     */
    static isElementVisible(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= window.innerHeight &&
            rect.right <= window.innerWidth
        );
    }

    /**
     * Добавление CSS стилей
     */
    static addStyles(styles) {
        const styleSheet = document.createElement('style');
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }
}

/**
 * Утилиты для форматирования
 */
class FormatUtils {
    /**
     * Форматирование числа с разделителями
     */
    static formatNumber(number, decimals = 2) {
        return Number(number).toLocaleString('ru-RU', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }

    /**
     * Форматирование времени
     */
    static formatTime(date) {
        return date.toLocaleTimeString('ru-RU', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Сокращение текста
     */
    static truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substr(0, maxLength) + '...';
    }

    /**
     * Безопасное извлечение HTML
     */
    static sanitizeHTML(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }
}

/**
 * Детектор касаний и жестов
 */
class TouchUtils {
    static init() {
        this.touchStartX = 0;
        this.touchStartY = 0;
        this.touchEndX = 0;
        this.touchEndY = 0;
        this.minSwipeDistance = 50;
    }

    static detectSwipe(element, onSwipe) {
        element.addEventListener('touchstart', (e) => {
            this.touchStartX = e.changedTouches[0].screenX;
            this.touchStartY = e.changedTouches[0].screenY;
        });

        element.addEventListener('touchend', (e) => {
            this.touchEndX = e.changedTouches[0].screenX;
            this.touchEndY = e.changedTouches[0].screenY;
            this.handleSwipe(onSwipe);
        });
    }

    static handleSwipe(callback) {
        const deltaX = this.touchEndX - this.touchStartX;
        const deltaY = this.touchEndY - this.touchStartY;
        
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > this.minSwipeDistance) {
            if (deltaX > 0) {
                callback('right');
            } else {
                callback('left');
            }
        } else if (Math.abs(deltaY) > this.minSwipeDistance) {
            if (deltaY > 0) {
                callback('down');
            } else {
                callback('up');
            }
        }
    }
}

// Инициализируем TouchUtils
TouchUtils.init();

// Экспортируем классы в глобальную область
window.ClientApp = ClientApp;
window.NotificationManager = NotificationManager;
window.StorageManager = StorageManager;
window.DOMUtils = DOMUtils;
window.FormatUtils = FormatUtils;
window.TouchUtils = TouchUtils;

// CSS стили для уведомлений
DOMUtils.addStyles(`
.notifications-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    pointer-events: none;
}

.notification {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    margin-bottom: 8px;
    background: var(--white);
    border-radius: var(--border-radius);
    box-shadow: var(--shadow-medium);
    pointer-events: auto;
    opacity: 0;
    transform: translateX(100%);
    transition: all 0.3s ease;
    max-width: 400px;
    border-left: 4px solid;
}

.notification.show {
    opacity: 1;
    transform: translateX(0);
}

.notification.hide {
    opacity: 0;
    transform: translateX(100%);
}

.notification-success {
    border-left-color: var(--success-green);
}

.notification-error {
    border-left-color: var(--danger-red);
}

.notification-warning {
    border-left-color: var(--warning-yellow);
}

.notification-info {
    border-left-color: var(--deep-blue);
}

.notification-icon {
    font-size: 20px;
    flex-shrink: 0;
}

.notification-content {
    flex: 1;
}

.notification-message {
    font-size: var(--font-size-sm);
    color: var(--dark-text);
    line-height: 1.4;
}

.notification-close {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    opacity: 0.6;
    transition: opacity 0.2s ease;
    flex-shrink: 0;
}

.notification-close:hover {
    opacity: 1;
}

.notification-close svg {
    fill: var(--gray-text);
}
`);