/**
 * Система уведомлений для официантов
 */

class WaiterNotifications {
    constructor() {
        this.notifications = [];
        this.soundEnabled = true;
        this.init();
    }

    init() {
        // Создаем контейнер для уведомлений
        this.createContainer();
        
        // Запускаем периодическую проверку новых уведомлений
        this.startPolling();
        
        console.log('🔔 Система уведомлений официанта инициализирована');
    }

    createContainer() {
        if (document.getElementById('waiter-notifications-container')) {
            return;
        }

        const container = document.createElement('div');
        container.id = 'waiter-notifications-container';
        container.className = 'waiter-notifications-container';
        container.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 9999;
            max-width: 350px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    /**
     * Показать уведомление
     */
    show(message, type = 'info', duration = 5000, options = {}) {
        const notification = {
            id: Date.now() + Math.random(),
            message,
            type,
            duration,
            timestamp: new Date(),
            ...options
        };

        this.notifications.push(notification);
        this.renderNotification(notification);

        // Воспроизводим звук если включен
        if (this.soundEnabled && (type === 'warning' || type === 'error')) {
            this.playNotificationSound();
        }

        return notification.id;
    }

    renderNotification(notification) {
        const container = document.getElementById('waiter-notifications-container');
        if (!container) return;

        const notificationEl = document.createElement('div');
        notificationEl.id = `notification-${notification.id}`;
        notificationEl.className = `waiter-notification waiter-notification-${notification.type}`;
        notificationEl.style.cssText = `
            margin-bottom: 10px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            transform: translateX(100%);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            pointer-events: auto;
            position: relative;
            max-width: 100%;
            word-wrap: break-word;
        `;

        // Цвета для разных типов
        const colors = {
            'success': '#28a745',
            'error': '#dc3545',
            'warning': '#ffc107',
            'info': '#007bff',
            'call': '#fd7e14'
        };
        notificationEl.style.backgroundColor = colors[notification.type] || colors.info;

        // Иконки для типов
        const icons = {
            'success': '✅',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'call': '🔔'
        };

        notificationEl.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1; padding-right: 10px;">
                    <div style="display: flex; align-items: center; margin-bottom: 5px;">
                        <span style="margin-right: 8px; font-size: 16px;">${icons[notification.type] || ''}</span>
                        <strong>${this.getTypeTitle(notification.type)}</strong>
                    </div>
                    <div style="font-size: 14px; opacity: 0.9;">${notification.message}</div>
                    <div style="font-size: 11px; opacity: 0.7; margin-top: 5px;">
                        ${WaiterUtils.formatTime(notification.timestamp)}
                    </div>
                </div>
                <button style="
                    background: none;
                    border: none;
                    color: white;
                    font-size: 20px;
                    cursor: pointer;
                    padding: 0;
                    margin-left: 10px;
                    opacity: 0.7;
                    line-height: 1;
                " title="Закрыть">&times;</button>
            </div>
        `;

        // Добавляем в контейнер
        container.appendChild(notificationEl);

        // Анимация появления
        setTimeout(() => {
            notificationEl.style.transform = 'translateX(0)';
        }, 50);

        // Обработчик закрытия
        const closeBtn = notificationEl.querySelector('button');
        const hideNotification = () => {
            this.hide(notification.id);
        };

        closeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            hideNotification();
        });

        // Закрытие по клику на уведомление
        notificationEl.addEventListener('click', hideNotification);

        // Автоматическое скрытие
        if (notification.duration > 0) {
            setTimeout(() => {
                this.hide(notification.id);
            }, notification.duration);
        }
    }

    /**
     * Скрыть уведомление
     */
    hide(notificationId) {
        const notificationEl = document.getElementById(`notification-${notificationId}`);
        if (!notificationEl) return;

        notificationEl.style.transform = 'translateX(100%)';
        notificationEl.style.opacity = '0';

        setTimeout(() => {
            if (notificationEl.parentNode) {
                notificationEl.parentNode.removeChild(notificationEl);
            }
        }, 400);

        // Удаляем из массива
        this.notifications = this.notifications.filter(n => n.id !== notificationId);
    }

    /**
     * Получить заголовок типа уведомления
     */
    getTypeTitle(type) {
        const titles = {
            'success': 'Успешно',
            'error': 'Ошибка',
            'warning': 'Внимание',
            'info': 'Информация',
            'call': 'Вызов официанта'
        };
        return titles[type] || 'Уведомление';
    }

    /**
     * Воспроизвести звук уведомления
     */
    playNotificationSound() {
        try {
            // Создаем простой звуковой сигнал
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);

            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (error) {
            console.warn('Не удалось воспроизвести звук уведомления:', error);
        }
    }

    /**
     * Запустить периодическую проверку новых уведомлений
     */
    startPolling() {
        // Проверяем новые вызовы каждые 30 секунд
        setInterval(() => {
            this.checkForNewCalls();
        }, 30000);
    }

    /**
     * Проверить новые вызовы официанта
     */
    async checkForNewCalls() {
        try {
            // Проверяем что API готов
            if (!window.WaiterAPI || typeof window.WaiterAPI.getCalls !== 'function') {
                return; // Тихо пропускаем если API не готов
            }
            
            const response = await window.WaiterAPI.getCalls({ status: 'новый' });
            if (response.status === 'success' && response.data.length > 0) {
                response.data.forEach(call => {
                    this.show(
                        `Стол ${call.table_number}: ${call.message || 'Вызов официанта'}`,
                        'call',
                        0, // Не скрывать автоматически
                        { callId: call.id }
                    );
                });
            }
        } catch (error) {
            // Логируем ошибку только если это не проблема с API
            if (window.WaiterAPI && typeof window.WaiterAPI.getCalls === 'function') {
                console.error('Ошибка проверки вызовов:', error);
            }
        }
    }

    /**
     * Показать уведомление о новом заказе
     */
    showNewOrder(order) {
        this.show(
            `Новый заказ #${order.id} на стол ${order.table_number}`,
            'info',
            8000
        );
    }

    /**
     * Показать уведомление о готовом заказе
     */
    showOrderReady(order) {
        this.show(
            `Заказ #${order.id} готов к подаче (стол ${order.table_number})`,
            'success',
            0 // Не скрывать автоматически
        );
    }

    /**
     * Показать уведомление об ошибке
     */
    showError(message) {
        this.show(message, 'error', 10000);
    }

    /**
     * Показать уведомление об успехе
     */
    showSuccess(message) {
        this.show(message, 'success', 4000);
    }

    /**
     * Показать предупреждение
     */
    showWarning(message) {
        this.show(message, 'warning', 6000);
    }

    /**
     * Очистить все уведомления
     */
    clearAll() {
        this.notifications.forEach(notification => {
            this.hide(notification.id);
        });
    }

    /**
     * Переключить звук
     */
    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        this.show(
            `Звук уведомлений ${this.soundEnabled ? 'включен' : 'отключен'}`,
            'info',
            2000
        );
    }
}

// Инициализация после загрузки WaiterAPI
document.addEventListener('DOMContentLoaded', () => {
    const initNotifications = () => {
        if (window.WaiterAPI && typeof window.WaiterAPI.getCalls === 'function') {
            window.waiterNotifications = new WaiterNotifications();
        } else {
            setTimeout(initNotifications, 50);
        }
    };
    
    initNotifications();
});