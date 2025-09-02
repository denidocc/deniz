/**
 * Утилиты для официантского интерфейса
 */

class WaiterUtils {
    /**
     * Форматирование времени
     */
    static formatTime(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleTimeString('ru-RU', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    /**
     * Форматирование даты
     */
    static formatDate(date) {
        if (!date) return '';
        const d = new Date(date);
        return d.toLocaleDateString('ru-RU');
    }

    /**
     * Форматирование цены
     */
    static formatPrice(price) {
        if (!price && price !== 0) return '';
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0
        }).format(price);
    }

    /**
     * Получение цвета статуса заказа
     */
    static getOrderStatusColor(status) {
        const colors = {
            'новый': '#007bff',
            'оплачен': '#28a745'
        };
        return colors[status] || '#6c757d';
    }

    /**
     * Получение иконки статуса заказа
     */
    static getOrderStatusIcon(status) {
        const icons = {
            'новый': '🆕',
            'оплачен': '✅'
        };
        return icons[status] || '❓';
    }

    /**
     * Получение текста статуса стола
     */
    static getTableStatusText(status) {
        const texts = {
            'free': 'Свободен',
            'occupied': 'Занят',
            'reserved': 'Забронирован',
            'cleaning': 'Уборка'
        };
        return texts[status] || status;
    }

    /**
     * Получение цвета статуса стола
     */
    static getTableStatusColor(status) {
        const colors = {
            'free': '#28a745',
            'occupied': '#dc3545',
            'reserved': '#ffc107',
            'cleaning': '#6c757d'
        };
        return colors[status] || '#6c757d';
    }

    /**
     * Показать уведомление
     */
    static showNotification(message, type = 'info', duration = 3000) {
        // Создаем контейнер для уведомлений если его нет
        let container = document.getElementById('waiter-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'waiter-notifications';
            container.className = 'waiter-notifications-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 350px;
            `;
            document.body.appendChild(container);
        }

        // Создаем уведомление
        const notification = document.createElement('div');
        notification.className = `waiter-notification waiter-notification-${type}`;
        notification.style.cssText = `
            margin-bottom: 10px;
            padding: 12px 16px;
            border-radius: 6px;
            color: white;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateX(100%);
            transition: all 0.3s ease;
            cursor: pointer;
        `;

        // Цвета для разных типов
        const colors = {
            'success': '#28a745',
            'error': '#dc3545', 
            'warning': '#ffc107',
            'info': '#007bff'
        };
        notification.style.backgroundColor = colors[type] || colors.info;

        notification.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${message}</span>
                <span style="margin-left: 10px; cursor: pointer; font-size: 18px;">&times;</span>
            </div>
        `;

        // Добавляем в контейнер
        container.appendChild(notification);

        // Анимация появления
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Автоматическое скрытие
        const hideNotification = () => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        };

        // Скрытие по клику
        notification.addEventListener('click', hideNotification);

        // Автоматическое скрытие через время
        if (duration > 0) {
            setTimeout(hideNotification, duration);
        }
    }

    /**
     * Показать индикатор загрузки
     */
    static showLoader(message = 'Загрузка...') {
        const loader = document.createElement('div');
        loader.id = 'waiter-loader';
        loader.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
        `;

        loader.innerHTML = `
            <div style="
                background: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                min-width: 200px;
            ">
                <div style="
                    width: 40px;
                    height: 40px;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #007bff;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 15px;
                "></div>
                <div>${message}</div>
            </div>
        `;

        // Добавляем CSS анимацию
        if (!document.getElementById('waiter-loader-styles')) {
            const style = document.createElement('style');
            style.id = 'waiter-loader-styles';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(loader);
        return loader;
    }

    /**
     * Скрыть индикатор загрузки
     */
    static hideLoader() {
        const loader = document.getElementById('waiter-loader');
        if (loader) {
            loader.remove();
        }
    }

    /**
     * Подтверждение действия
     */
    static async confirm(message, title = 'Подтверждение') {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10001;
            `;

            modal.innerHTML = `
                <div style="
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    text-align: center;
                    max-width: 400px;
                    margin: 20px;
                ">
                    <h3 style="margin: 0 0 15px; color: #333;">${title}</h3>
                    <p style="margin: 0 0 25px; color: #666;">${message}</p>
                    <div>
                        <button id="confirm-cancel" style="
                            padding: 10px 20px;
                            margin: 0 10px;
                            border: 1px solid #ccc;
                            background: white;
                            border-radius: 5px;
                            cursor: pointer;
                        ">Отмена</button>
                        <button id="confirm-ok" style="
                            padding: 10px 20px;
                            margin: 0 10px;
                            border: none;
                            background: #007bff;
                            color: white;
                            border-radius: 5px;
                            cursor: pointer;
                        ">Подтвердить</button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            modal.querySelector('#confirm-ok').addEventListener('click', () => {
                modal.remove();
                resolve(true);
            });

            modal.querySelector('#confirm-cancel').addEventListener('click', () => {
                modal.remove();
                resolve(false);
            });

            // Закрытие по клику вне модального окна
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                    resolve(false);
                }
            });
        });
    }

    /**
     * Безопасный вызов API с обработкой ошибок
     */
    static async safeApiCall(apiCall, errorMessage = 'Произошла ошибка') {
        try {
            return await apiCall();
        } catch (error) {
            console.error('API Error:', error);
            this.showNotification(errorMessage, 'error');
            throw error;
        }
    }
}

// Экспортируем в глобальную область
window.WaiterUtils = WaiterUtils;