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
        // Упрощаем - просто обновляем счетчики, которые уже работают
        // Убираем сложную логику с data-action, так как она не нужна
        
        // Счетчики уже обновляются в updateStatsCards()
        console.log('✅ Быстрые действия обновлены');
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
        // Убираем сложную логику с data-action
        // Простые клики по ссылкам работают автоматически
        
        console.log('✅ Обработчики событий инициализированы');
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
            console.log('🔄 Начинаем загрузку последних заказов...');
            
            const recentOrdersList = document.getElementById('recentOrdersList');
            if (!recentOrdersList) {
                console.log('❌ Элемент recentOrdersList не найден');
                return;
            }

            // Показываем состояние загрузки
            recentOrdersList.innerHTML = `
                <div class="loading-state">
                    <div class="spinner"></div>
                    <span>Загрузка заказов...</span>
                </div>
            `;

            console.log('🔍 Проверяем WaiterAPI:', window.WaiterAPI);
            console.log('🔍 getOrders функция:', typeof window.WaiterAPI.getOrders);

            // Получаем последние 5 заказов
            console.log('📡 Отправляем запрос getOrders...');
            const response = await window.WaiterAPI.getOrders();
            console.log('📡 Ответ от API:', response);
            
            if (response.status === 'success' && response.data.orders.length > 0) {
                console.log(`✅ Получено ${response.data.orders.length} заказов`);
                
                // Берем только последние 5 заказов и сортируем по дате
                const recentOrders = response.data.orders
                    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                    .slice(0, 5);

                let ordersHtml = '';
                recentOrders.forEach(order => {
                    console.log(' Обрабатываем заказ:', order);
                    
                    // ИСПРАВЛЯЕМ: объявляем переменные внутри цикла
                    const statusColor = WaiterUtils.getOrderStatusColor(order.status);
                    const statusIcon = WaiterUtils.getOrderStatusIcon(order.status);
                    
                    // Создаем HTML для каждого заказа
                    const orderHtml = `
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
                    
                    // Добавляем HTML в общую строку
                    ordersHtml += orderHtml;
                });

                recentOrdersList.innerHTML = ordersHtml;
                console.log('✅ HTML для заказов обновлен');
            } else {
                console.log('📭 Нет заказов или ошибка в ответе');
                // Нет заказов
                recentOrdersList.innerHTML = `
                    <div class="no-orders">
                        <i class="fas fa-clipboard-list"></i>
                        <span>Нет последних заказов</span>
                    </div>
                `;
            }
        } catch (error) {
            console.error('❌ Ошибка загрузки последних заказов:', error);
            const recentOrdersList = document.getElementById('recentOrdersList');
            if (recentOrdersList) {
                recentOrdersList.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <span>Ошибка загрузки заказов: ${error.message}</span>
                    </div>
                `;
            }
        }
    }
}

// Добавляем функцию обновления счетчиков
function updateCounters() {
    fetch('/waiter/api/counters')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Обновляем счетчик заказов
                const ordersCount = document.getElementById('pendingOrdersCount');
                if (ordersCount) {
                    ordersCount.textContent = `${data.data.pending_orders} новых`;
                }
                
                // Обновляем счетчик вызовов
                const callsCount = document.getElementById('pendingCallsCount');
                if (callsCount) {
                    callsCount.textContent = `${data.data.pending_calls} активных`;
                }
                
                // Обновляем счетчик столов
                const tablesCount = document.getElementById('myTablesCount');
                if (tablesCount) {
                    tablesCount.textContent = `${data.data.assigned_tables} столов`;
                }
            }
        })
        .catch(error => {
            console.error('Error updating counters:', error);
        });
}

// Обновляем счетчики при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    updateCounters();
    
    // Обновляем счетчики каждые 30 секунд
    setInterval(updateCounters, 30000);
});

// Очистка при выгрузке страницы
window.addEventListener('beforeunload', () => {
    if (window.waiterDashboard) {
        window.waiterDashboard.destroy();
    }
});

console.log(' dashboard.js загружен');

// Инициализация dashboard при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM загружен, инициализируем dashboard');
    
    // Проверяем, что все необходимые компоненты загружены
    if (window.WaiterAPI) {
        console.log('✅ WaiterAPI доступен');
    } else {
        console.log('❌ WaiterAPI НЕ доступен');
    }
    
    if (window.WaiterUtils) {
        console.log('✅ WaiterUtils доступен');
    } else {
        console.log('❌ WaiterUtils НЕ доступен');
    }
    
    // Создаем экземпляр dashboard
    window.waiterDashboard = new WaiterDashboard();
    console.log('✅ Dashboard создан');
});