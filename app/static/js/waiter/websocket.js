/**
 * WebSocket клиент для официантов
 */

class WaiterWebSocket {
    constructor(waiterId) {
        this.waiterId = waiterId;
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        
        // Добавляем флаг для предотвращения дублирования
        this.lastOrderId = null;
        this.lastCallId = null;
        
        this.init();
    }
    
    init() {
        // Подключение к WebSocket серверу
        this.connect();
        
        // Обработка событий страницы
        this.setupPageEvents();
    }
    
    setupPageEvents() {}
    
    connect() {
        try {
            // Подключение к Socket.IO серверу
            this.socket = io();
            
            // Обработчики событий
            this.socket.on('connect', () => {
                this.isConnected = true;
                this.reconnectAttempts = 0;
                console.log('WebSocket подключен');
                
                // Присоединяемся к комнате официанта
                this.joinWaiterRoom();
            });
            
            this.socket.on('disconnect', () => {
                this.isConnected = false;
                console.log('WebSocket отключен');
                this.scheduleReconnect();
            });
            
            this.socket.on('error', (error) => {
                console.error('WebSocket ошибка:', error);
            });
            
            // Обработка уведомлений
            this.socket.on('new_order', (data) => {
                this.handleNewOrder(data);
            });
            
            this.socket.on('order_updated', (data) => {
                this.handleOrderUpdated(data);
            });
            
            this.socket.on('waiter_call', (data) => {
                this.handleWaiterCall(data);
            });
            
            this.socket.on('joined_room', (data) => {
                console.log('Присоединились к комнате:', data.message);
            });
            
            this.socket.on('error', (data) => {
                console.error('Ошибка от сервера:', data.message);
            });
            
        } catch (error) {
            console.error('Ошибка инициализации WebSocket:', error);
        }
    }
    
    joinWaiterRoom() {
        if (this.socket && this.isConnected) {
            this.socket.emit('join_waiter_room', {
                waiter_id: this.waiterId
            });
        }
    }
    
    handleNewOrder(data) {
        // Защита от дублирования: проверяем ID заказа
        if (this.lastOrderId === data.order_id) {
            console.log('Заказ уже обработан, пропускаем:', data.order_id);
            return;
        }
        
        console.log('Новый заказ:', data);
        this.lastOrderId = data.order_id;
        
        // Воспроизводим звук ОДИН РАЗ
        playNotificationSound();
        
        // Показываем уведомление через систему уведомлений
        if (window.waiterNotifications) {
            window.waiterNotifications.show(
                data.message || `Новый заказ со стола №${data.table_number}`,
                'success',
                8000
            );
        }
        
        // Добавляем заказ в список заказов (если страница открыта)
        this.addNewOrderToList(data);
        
        // Обновляем счетчик заказов
        this.updateOrderCounter();
    }
    
    handleOrderUpdated(data) {
        console.log('🔄 Обновление заказа:', data);
        
        // Обновляем заказ в списке заказов
        this.updateOrderInList(data);
        
        // Показываем уведомление
        if (window.waiterNotifications) {
            window.waiterNotifications.show(
                data.message || `Заказ №${data.order_id} обновлен`,
                'info',
                5000
            );
        }
    }
    
    handleWaiterCall(data) {
        // Защита от дублирования: проверяем ID вызова
        if (this.lastCallId === data.call_id) {
            console.log('Вызов уже обработан, пропускаем:', data.call_id);
            return;
        }
        
        console.log('Вызов официанта:', data);
        this.lastCallId = data.call_id;
        
        // Воспроизводим звук ОДИН РАЗ
        playNotificationSound();
        
        // Показываем уведомление
        this.showNotification('Вызов официанта', data.message, 'call');
        
        // Добавляем вызов в список вызовов (если страница открыта)
        this.addNewCallToList(data);
        
        // Обновляем счетчик вызовов
        this.updateCallCounter();
    }
    
    playNotificationSound() {
        // Используем HTML5 Audio решение
        playNotificationSound();
    }
    
    showNotification(title, message, type) {
        // Проверяем поддержку уведомлений
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                body: message,
                icon: '/static/images/logo.svg',
                tag: type
            });
        }
        
        // Показываем встроенное уведомление
        this.showInlineNotification(title, message, type);
    }
    
    showInlineNotification(title, message, type) {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-header">
                <span class="notification-title">${title}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
            <div class="notification-body">${message}</div>
        `;
        
        // Добавляем стили
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
        `;
        
        // Добавляем в DOM
        document.body.appendChild(notification);
        
        // Автоматически скрываем через 5 секунд
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    updateOrdersList() {
        // Обновляем список заказов (если есть такой элемент)
        const ordersList = document.getElementById('orders-list');
        if (ordersList) {
            // Здесь можно добавить логику обновления списка
            console.log('Обновляем список заказов');
        }
    }
    
    updateCallsList() {
        // Обновляем список вызовов (если есть такой элемент)
        const callsList = document.getElementById('callsList');
        if (callsList) {
            console.log('Обновляем список вызовов');
            
            // Если есть функция loadCalls, вызываем её для обновления
            if (typeof window.loadCalls === 'function') {
                window.loadCalls();
            } else {
                // Иначе делаем принудительное обновление страницы
                console.log('Функция loadCalls не найдена, обновляем страницу');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        }
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Попытка переподключения ${this.reconnectAttempts}/${this.maxReconnectAttempts} через ${this.reconnectDelay}ms`);
            
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay);
        } else {
            console.error('Превышено максимальное количество попыток переподключения');
        }
    }
    
    disconnect() {
        if (this.socket) {
            this.socket.emit('leave_waiter_room', {
                waiter_id: this.waiterId
            });
            this.socket.disconnect();
        }
    }

    // ДОБАВЛЯЕМ ЭТОТ МЕТОД
    addNewOrderToList(orderData) {
        // Проверяем, что мы на странице заказов
        if (!window.location.pathname.includes('/waiter/orders')) {
            console.log('Не на странице заказов, пропускаем добавление в список');
            return;
        }
        
        console.log('Добавляем новый заказ в список:', orderData);
        
        const ordersContainer = document.getElementById('ordersList');
        if (!ordersContainer) {
            console.log('Контейнер заказов не найден');
            return;
        }
        
        // Создание HTML для нового заказа
        const orderHtml = this.createOrderCard(orderData);
        
        // Находим группу "Новые заказы" (pending)
        let pendingGroup = ordersContainer.querySelector('.pending-group');
        
        if (!pendingGroup) {
            console.log('Группа pending не найдена, создаем новую');
            // Если группы нет, создаем её
            const statusInfo = window.statusReference?.pending || { name: 'Новые заказы', icon: '🟢' };
            pendingGroup = document.createElement('div');
            pendingGroup.className = 'status-group pending-group';
            pendingGroup.innerHTML = `<h3 class="status-group-title pending-title">${statusInfo.icon} ${statusInfo.name}</h3>`;
            
            // Добавляем в начало списка
            ordersContainer.insertBefore(pendingGroup, ordersContainer.firstChild);
        }
        
        // Добавляем заказ в группу
        pendingGroup.insertAdjacentHTML('beforeend', orderHtml);
        
        // Анимация появления
        const newOrder = pendingGroup.lastElementChild;
        newOrder.style.opacity = '0';
        newOrder.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            newOrder.style.transition = 'all 0.3s ease';
            newOrder.style.opacity = '1';
            newOrder.style.transform = 'translateY(0)';
        }, 100);
        
        console.log('Заказ успешно добавлен в список');
    }
    
    // ДОБАВЛЯЕМ МЕТОД СОЗДАНИЯ КАРТОЧКИ
    createOrderCard(order) {
        const statusColor = this.getStatusColor(order.status || 'pending');
        const statusIcon = this.getStatusIcon(order.status || 'pending');
        
        return `
            <div class="order-card" data-order-id="${order.order_id}">
                <div class="order-header">
                    <div class="order-info">
                        <div class="order-title">
                            <h3>Заказ #${order.order_id}</h3>
                            <span class="order-status ${order.status || 'pending'}" style="background: ${statusColor};">
                                ${statusIcon} ${(order.status || 'pending').toUpperCase()}
                            </span>
                        </div>
                        <div class="order-table-info">
                            <i class="fas fa-table"></i>
                            <span>Стол: ${order.table_number}</span>
                            <i class="fas fa-users"></i>
                            <span>Гостей: ${order.guest_count || 1}</span>
                        </div>
                    </div>
                </div>
                <div class="order-body">
                    <div class="order-total">
                        <div class="total-label">Итого к оплате:</div>
                        <div class="total-amount">${order.total_amount} TMT</div>
                    </div>
                    <div class="order-meta">
                        <div class="meta-item">
                            <i class="fas fa-clock"></i>
                            <span>Создан: ${new Date(order.created_at).toLocaleString('ru-RU')}</span>
                        </div>
                        <div class="meta-item">
                            <i class="fas fa-language"></i>
                            <span>Язык: ${(order.language || 'ru').toUpperCase()}</span>
                        </div>
                    </div>
                </div>
                <div class="order-actions">
                    <button class="btn btn-primary" onclick="window.viewOrderDetails(${order.order_id})">
                        <i class="fas fa-eye"></i> Подробности
                    </button>
                    <button class="btn btn-danger" onclick="window.cancelOrder(${order.order_id})">
                        <i class="fas fa-times"></i> Отменить заказ
                    </button>
                </div>
            </div>
        `;
    }
    
    // ДОБАВЛЯЕМ МЕТОДЫ ДЛЯ СТАТУСОВ
    getStatusColor(status) {
        if (window.statusReference && window.statusReference[status] && window.statusReference[status].color) {
            return window.statusReference[status].color;
        }
        const fallbackColors = {
            'pending': '#28a745',    // Зеленый
            'confirmed': '#ffc107',  // Желтый
            'completed': '#6c757d',  // Серый
            'cancelled': '#dc3545'   // Красный
        };
        return fallbackColors[status] || '#6c757d';
    }
    
    getStatusIcon(status) {
        if (window.statusReference && window.statusReference[status] && window.statusReference[status].icon) {
            return window.statusReference[status].icon;
        }
        const fallbackIcons = {
            'pending': '🟢',
            'confirmed': '✅',
            'completed': '⚫',
            'cancelled': '❌'
        };
        return fallbackIcons[status] || '⚫';
    }
    
    // ДОБАВЛЯЕМ МЕТОД ОБНОВЛЕНИЯ СЧЕТЧИКА
    updateOrderCounter() {
        const counter = document.querySelector('.orders-counter');
        if (counter) {
            const currentCount = parseInt(counter.textContent) || 0;
            counter.textContent = currentCount + 1;
            counter.classList.add('pulse');
            
            setTimeout(() => {
                counter.classList.remove('pulse');
            }, 1000);
        }
    }
    
    // ДОБАВЛЯЕМ МЕТОД ОБНОВЛЕНИЯ ЗАКАЗА В СПИСКЕ
    updateOrderInList(data) {
        // Проверяем, что мы на странице заказов
        if (!window.location.pathname.includes('/waiter/orders')) {
            console.log('Не на странице заказов, пропускаем обновление');
            return;
        }
        
        console.log(`🔄 Обновляем заказ ${data.order_id} со статусом ${data.status}`);
        
        // Простое решение: перезагружаем список заказов
        if (typeof window.loadOrders === 'function') {
            console.log('♻️ Перезагружаем список заказов');
            window.loadOrders();
        } else {
            console.log('⚠️ Функция loadOrders не найдена, пробуем обновить карточку');
            
            // Fallback: обновляем только статус карточки
            const orderCard = document.querySelector(`[data-order-id="${data.order_id}"]`);
            if (orderCard) {
                const statusElement = orderCard.querySelector('.order-status');
                if (statusElement && data.status) {
                    const statusColor = this.getStatusColor(data.status);
                    const statusIcon = this.getStatusIcon(data.status);
                    
                    statusElement.textContent = `${statusIcon} ${data.status.toUpperCase()}`;
                    statusElement.style.background = statusColor;
                    statusElement.className = `order-status ${data.status}`;
                }
            }
        }
        
        console.log(`✅ Заказ ${data.order_id} обновлен в списке`);
    }


    // ДОБАВЛЯЕМ МЕТОД ДЛЯ ВЫЗОВОВ
    addNewCallToList(callData) {
        // Проверяем, что мы на странице вызовов
        if (!window.location.pathname.includes('/waiter/calls')) {
            console.log('Не на странице вызовов, пропускаем добавление в список');
            return;
        }
        
        console.log('Добавляем новый вызов в список:', callData);
        
        const callsContainer = document.getElementById('callsList');
        if (!callsContainer) {
            console.log('Контейнер вызовов не найден');
            return;
        }
        
        // Создание HTML для нового вызова
        const callHtml = this.createCallCard(callData);
        
        // Добавляем вызов в начало списка
        callsContainer.insertAdjacentHTML('afterbegin', callHtml);
        
        // Анимация появления
        const newCall = callsContainer.firstElementChild;
        newCall.style.opacity = '0';
        newCall.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            newCall.style.transition = 'all 0.3s ease';
            newCall.style.opacity = '1';
            newCall.style.transform = 'translateY(0)';
        }, 100);
        
        console.log('Вызов успешно добавлен в список');
    }
    
    // МЕТОД СОЗДАНИЯ КАРТОЧКИ ВЫЗОВА
    createCallCard(call) {
        return `
            <div class="call-card call-pending priority-средний" data-call-id="${call.call_id}">
                <div class="call-header">
                    <div class="call-table">
                        <i class="fas fa-utensils"></i>
                        <strong>Стол ${call.table_number || 'Неизвестно'}</strong>
                    </div>
                    <div class="call-time">
                        <i class="fas fa-clock"></i>
                        Только что
                    </div>
                    <div class="call-status-badge">
                        <span class="status-badge status-pending">
                            Новый
                        </span>
                    </div>
                </div>
                <div class="call-content">
                    <div class="call-message">
                        <i class="fas fa-comment"></i>
                        ${call.message || 'Вызов официанта'}
                    </div>
                    <div class="call-from">
                        <i class="fas fa-user"></i>
                        Клиент стола ${call.table_number || 'Неизвестно'}
                    </div>
                </div>
                <div class="call-footer">
                    <div class="call-actions">
                        <button class="btn btn-primary" onclick="markAsRead(${call.call_id})">
                            <i class="fas fa-eye"></i> Прочитать
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // ДОБАВЛЯЕМ МЕТОД ОБНОВЛЕНИЯ СЧЕТЧИКА ВЫЗОВОВ
    updateCallCounter() {
        // Обновляем счетчик вызовов на странице
        const callCounter = document.getElementById('pendingCallsCount');
        if (callCounter) {
            // Увеличиваем счетчик на 1
            const currentCount = parseInt(callCounter.textContent.match(/\d+/)?.[0] || '0');
            callCounter.textContent = `${currentCount + 1} активных`;
        }
    }
}

// В начало файла, ПЕРЕД классом WaiterWebSocket
let __audioElement = null;
let __audioUnlocked = false;
let __lastPlayTime = 0;

// Создаем HTML5 Audio элемент с простым звуком
function createAudioElement() {
    if (__audioElement) return __audioElement;
    
    const audio = new Audio();
    
    // Используем простой звук через Web Audio API
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Настройки звука "бип"
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        // Создаем MediaStream для записи
        const destination = audioContext.createMediaStreamDestination();
        oscillator.connect(destination);
        
        const mediaRecorder = new MediaRecorder(destination.stream);
        const chunks = [];
        
        mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
        mediaRecorder.onstop = () => {
            const blob = new Blob(chunks, { type: 'audio/wav' });
            const url = URL.createObjectURL(blob);
            audio.src = url;
            audio.load();
            
            // ДОБАВЛЯЕМ: сохраняем URL для последующей очистки
            audio._blobUrl = url;
        };
        
        oscillator.start();
        mediaRecorder.start();
        
        setTimeout(() => {
            oscillator.stop();
            mediaRecorder.stop();
        }, 100);
        
    } catch (e) {
        console.log('Web Audio API недоступен, создаем простой звук');
        
        // Fallback: создаем простой звук через генерацию
        const sampleRate = 44100;
        const duration = 0.1; // 100ms
        const samples = sampleRate * duration;
        
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const buffer = audioContext.createBuffer(1, samples, sampleRate);
        const data = buffer.getChannelData(0);
        
        for (let i = 0; i < samples; i++) {
            const t = i / sampleRate;
            data[i] = Math.sin(2 * Math.PI * 800 * t) * Math.exp(-t * 10);
        }
        
        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);
        source.start();
        
        // Создаем пустой аудио элемент для совместимости
        audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT';
    }
    
    audio.volume = 0.3;
    audio.preload = 'auto';
    
    __audioElement = audio;
    return audio;
}

// Функция воспроизведения звука
function playNotificationSound() {
    const now = Date.now();
    
    // Защита от дублирования: не воспроизводим звук чаще чем раз в 500мс
    if (now - __lastPlayTime < 500) {
        console.log('🔇 Звук заблокирован (слишком часто)');
        return;
    }
    
    try {
        // Пробуем воспроизвести через Web Audio API напрямую
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Если контекст приостановлен, возобновляем
        if (audioContext.state === 'suspended') {
            audioContext.resume();
        }
        
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        // Настройки звука "бип"
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
        
        console.log('🔊 Звук воспроизведен через Web Audio API');
        __lastPlayTime = now;
        
    } catch (error) {
        console.warn('Web Audio API недоступен, пробуем HTML5 Audio:', error);
        
        // Fallback на HTML5 Audio
        try {
            const audio = createAudioElement();
            
            if (audio.src && audio.src !== 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT') {
                audio.currentTime = 0;
                const playPromise = audio.play();
                
                if (playPromise !== undefined) {
                    playPromise
                        .then(() => {
                            console.log('🔊 Звук воспроизведен через HTML5 Audio');
                            __lastPlayTime = now;
                        })
                        .catch(error => {
                            console.warn('Ошибка HTML5 Audio:', error);
                        });
                }
            }
        } catch (fallbackError) {
            console.warn('Все методы воспроизведения звука недоступны:', fallbackError);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Очищаем старые аудио элементы при загрузке
    if (__audioElement) {
        __audioElement.pause();
        __audioElement.src = '';
        __audioElement = null;
    }
    
    // Предварительно создаем аудио элемент
    createAudioElement();
    
    // Получаем ID официанта из данных страницы
    const waiterId = document.body.dataset.waiterId;
    
    if (waiterId) {
        // Создаем экземпляр WebSocket клиента
        window.waiterWebSocket = new WaiterWebSocket(waiterId);
        
        // Запрашиваем разрешение на уведомления
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
});

// Очистка при выгрузке страницы
window.addEventListener('beforeunload', function() {
    if (__audioElement) {
        // Очищаем blob URL если он есть
        if (__audioElement._blobUrl) {
            URL.revokeObjectURL(__audioElement._blobUrl);
        }
        __audioElement.pause();
        __audioElement.src = '';
        __audioElement = null;
    }
    
    if (window.waiterWebSocket) {
        window.waiterWebSocket.disconnect();
    }
});

// Добавляем CSS для анимации
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .notification-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid #eee;
        background: #f8f9fa;
        border-radius: 8px 8px 0 0;
    }
    
    .notification-title {
        font-weight: 600;
        color: #333;
    }
    
    .notification-close {
        background: none;
        border: none;
        font-size: 18px;
        cursor: pointer;
        color: #666;
        padding: 0;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .notification-close:hover {
        color: #333;
    }
    
    .notification-body {
        padding: 16px;
        color: #555;
        line-height: 1.4;
    }
    
    .notification-order {
        border-left: 4px solid #28a745;
    }
    
    .notification-call {
        border-left: 4px solid #dc3545;
    }

    /* Стили для кнопки звука */
    #enable-sound-btn {
        transition: all 0.3s ease;
        margin-left: 10px;
    }

    #enable-sound-btn:hover {
        transform: scale(1.05);
    }

    #enable-sound-btn:disabled {
        opacity: 0.8;
        cursor: not-allowed;
    }

    #enable-sound-btn .fas {
        margin-right: 5px;
    }

    /* Анимация для иконки звука */
    @keyframes soundPulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.2); }
        100% { transform: scale(1); }
    }

    #enable-sound-btn.btn-success .fas {
        animation: soundPulse 2s infinite;
    }
`;
document.head.appendChild(style);
