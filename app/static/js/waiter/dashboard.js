/**
 * Dashboard для официанта
 */

class WaiterDashboard {
    constructor() {
        this.stats = {};
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        try {
            await this.loadDashboardData();
            this.initRefreshInterval();
            this.initEventListeners();
            this.initFlashMessages();
            console.log('📊 Dashboard официанта инициализирован');
        } catch (error) {
            console.error('Ошибка инициализации dashboard:', error);
        }
    }

    /**
     * Загрузить данные дашборда
     */
    async loadDashboardData() {
        try {
            // Проверяем что API готов
            if (!window.WaiterAPI || typeof window.WaiterAPI.getDashboardStats !== 'function') {
                return; // Тихо пропускаем если API не готов
            }
            
            const response = await window.WaiterAPI.getDashboardStats();
            

            if (response.status === 'success') {
                this.stats = response.data;
                this.updateDashboardDisplay();
            }
        } catch (error) {
            // Логируем ошибку только если это не проблема с API
            if (window.WaiterAPI && typeof window.WaiterAPI.getDashboardStats === 'function') {
                console.error('Ошибка загрузки данных dashboard:', error);
                if (window.waiterNotifications) {
                    waiterNotifications.showError('Не удалось загрузить данные dashboard');
                }
            }
        }
    }

    /**
     * Обновить отображение дашборда
     */
    updateDashboardDisplay() {
        this.updateStatsCards();
        this.updateQuickActions();
        this.updateRecentActivity();
        this.loadRecentOrders();

    }

    /**
     * Обновить карточки статистики
     */
    updateStatsCards() {
        // Новые заказы (в быстрых действиях)
        const pendingOrdersEl = document.getElementById('pendingOrdersCount');
        if (pendingOrdersEl) {
            const count = this.stats.pending_orders || 0;
            pendingOrdersEl.textContent = `${count} новых`;
        }

        // Назначенные столы (в быстрых действиях)
        const myTablesEl = document.getElementById('myTablesCount');
        if (myTablesEl) {
            const count = this.stats.assigned_tables || 0;
            myTablesEl.textContent = `${count} столов`;
        }

        // Ожидающие вызовы (в быстрых действиях)
        const pendingCallsEl = document.getElementById('pendingCallsCount');
        if (pendingCallsEl) {
            const count = this.stats.pending_calls || 0;
            pendingCallsEl.textContent = `${count} активных`;
        }


    }





    /**
     * Обновить быстрые действия
     */
    updateQuickActions() {
        // Обновляем счетчики на кнопках быстрых действий
        const ordersBtn = document.querySelector('[data-action="orders"] .badge');
        if (ordersBtn && this.stats.pending_orders > 0) {
            ordersBtn.textContent = this.stats.pending_orders;
            ordersBtn.style.display = 'inline';
        } else if (ordersBtn) {
            ordersBtn.style.display = 'none';
        }

        const callsBtn = document.querySelector('[data-action="calls"] .badge');
        if (callsBtn && this.stats.pending_calls > 0) {
            callsBtn.textContent = this.stats.pending_calls;
            callsBtn.style.display = 'inline';
        } else if (callsBtn) {
            callsBtn.style.display = 'none';
        }
    }

    /**
     * Обновить последнюю активность
     */
    updateRecentActivity() {
        const activityContainer = document.getElementById('recent-activity');
        if (!activityContainer || !this.stats.recent_activity) return;

        if (this.stats.recent_activity.length === 0) {
            activityContainer.innerHTML = `
                <div class="no-activity">
                    <i class="fas fa-coffee"></i>
                    <p>Пока нет активности</p>
                </div>
            `;
            return;
        }

        const activityHtml = this.stats.recent_activity.map(activity => `
            <div class="activity-item">
                <div class="activity-icon">
                    ${this.getActivityIcon(activity.type)}
                </div>
                <div class="activity-content">
                    <div class="activity-text">${activity.description}</div>
                    <div class="activity-time">${WaiterUtils.formatTime(activity.timestamp)}</div>
                </div>
            </div>
        `).join('');

        activityContainer.innerHTML = activityHtml;
    }

    /**
     * Получить иконку для типа активности
     */
    getActivityIcon(type) {
        const icons = {
            'order_created': '📋',
            'order_ready': '✅',
            'call_received': '🔔',
            'table_assigned': '🪑',

        };
        return icons[type] || '📌';
    }

    /**
     * Инициализировать интервал обновления
     */
    initRefreshInterval() {
        // Обновляем данные каждые 30 секунд
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 30000);
    }

    /**
     * Инициализировать обработчики событий
     */
    initEventListeners() {
        // Кнопки быстрых действий
        document.querySelectorAll('[data-action]').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const action = button.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });

        // Кнопка обновления
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshDashboard();
            });
        }

        // Кнопки карточек статистики (делаем их кликабельными)
        const statsCards = document.querySelectorAll('.stats-card[data-action]');
        statsCards.forEach(card => {
            card.style.cursor = 'pointer';
            card.addEventListener('click', (e) => {
                e.preventDefault();
                const action = card.getAttribute('data-action');
                this.handleQuickAction(action);
            });
        });
    }

    /**
     * Инициализировать flash сообщения
     */
    initFlashMessages() {
        const flashMessages = document.querySelectorAll('.flash-message');
        flashMessages.forEach(message => {
            // Автоматическое скрытие через 5 секунд
            setTimeout(() => {
                this.hideFlashMessage(message);
            }, 5000);

            // Кнопка закрытия
            const closeBtn = message.querySelector('.flash-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    this.hideFlashMessage(message);
                });
            }

            // Закрытие по клику на сообщение
            message.addEventListener('click', () => {
                this.hideFlashMessage(message);
            });
        });
    }

    /**
     * Скрыть flash сообщение
     */
    hideFlashMessage(messageElement) {
        messageElement.style.transform = 'translateX(100%)';
        messageElement.style.opacity = '0';
        
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.parentNode.removeChild(messageElement);
            }
        }, 300);
    }

    /**
     * Обработать быстрое действие
     */
    handleQuickAction(action) {
        switch (action) {
            case 'orders':
                window.location.href = '/waiter/orders';
                break;
            case 'tables':
                window.location.href = '/waiter/tables';
                break;
            case 'calls':
                window.location.href = '/waiter/calls';
                break;

            default:
                console.warn('Неизвестное действие:', action);
        }
    }

    /**
     * Обновить дашборд
     */
    async refreshDashboard() {
        const refreshBtn = document.getElementById('refresh-dashboard');
        if (refreshBtn) {
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }

        try {
            await this.loadDashboardData();
            waiterNotifications.showSuccess('Данные обновлены');
        } catch (error) {
            waiterNotifications.showError('Ошибка обновления данных');
        } finally {
            if (refreshBtn) {
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
            }
        }
    }

    /**
     * Показать детали статистики
     */
    showStatsDetails(type) {
        // Здесь можно добавить модальное окно с детальной статистикой
        console.log('Показать детали для:', type);
    }

    /**
     * Уничтожить интервал обновления
     */
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    /**
     * Загрузить последние заказы
     */
    async loadRecentOrders() {
        try {
            const recentOrdersList = document.getElementById('recentOrdersList');
            if (!recentOrdersList) return;

            // Показываем состояние загрузки
            recentOrdersList.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <span>Загрузка заказов...</span>
                </div>
            `;

            // Получаем последние 5 заказов
            const response = await window.WaiterAPI.getOrders();
            
            if (response.status === 'success' && response.data.orders.length > 0) {
                // Берем только последние 5 заказов и сортируем по дате
                const recentOrders = response.data.orders
                    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                    .slice(0, 5);

                let ordersHtml = '';
                recentOrders.forEach(order => {
                    const statusColor = WaiterUtils.getOrderStatusColor(order.status);
                    const statusIcon = WaiterUtils.getOrderStatusIcon(order.status);
                    
                    ordersHtml += `
                        <div class="recent-order-item">
                            <div class="order-info">
                                <div class="order-header">
                                    <span class="order-number">Заказ #${order.id}</span>
                                    <span class="order-status-mini" style="background: ${statusColor};">
                                        ${order.status}
                                    </span>
                                </div>
                                <div class="order-details">
                                    <span class="table-info">Стол ${order.table_number}</span>
                                    <span class="order-total">${order.total_amount} TMT</span>
                                </div>
                                <div class="order-time">
                                    ${new Date(order.created_at).toLocaleString('ru-RU', {
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    })}
                                </div>
                            </div>
                        </div>
                    `;
                });

                recentOrdersList.innerHTML = ordersHtml;
            } else {
                // Нет заказов
                recentOrdersList.innerHTML = `
                    <div class="no-orders">
                        <i class="fas fa-clipboard-list"></i>
                        <span>Нет последних заказов</span>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error loading recent orders:', error);
            const recentOrdersList = document.getElementById('recentOrdersList');
            if (recentOrdersList) {
                recentOrdersList.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Ошибка загрузки заказов</span>
                    </div>
                `;
            }
        }
    }
}

// Инициализация при загрузке DOM после WaiterAPI
document.addEventListener('DOMContentLoaded', () => {
    // Ждем пока WaiterAPI станет доступным
    const waitForAPI = () => {
        if (window.WaiterAPI && typeof window.WaiterAPI.getDashboardStats === 'function') {
            window.waiterDashboard = new WaiterDashboard();
        } else {
            setTimeout(waitForAPI, 50);
        }
    };
    
    waitForAPI();
});

// Очистка при выгрузке страницы
window.addEventListener('beforeunload', () => {
    if (window.waiterDashboard) {
        window.waiterDashboard.destroy();
    }
});