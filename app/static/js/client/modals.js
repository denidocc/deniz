/**
 * Модуль управления модальными окнами
 */

class ModalManager {
    static init() {
        console.log('🔲 Initializing Modal Manager');
        
        this.activeModal = null;
        this.overlay = null;
        this.callbacks = new Map();
        
        this.createOverlay();
        this.setupEventListeners();
        
        console.log('✅ Modal Manager initialized');
    }

    static createOverlay() {
        this.overlay = document.getElementById('modalOverlay');
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.id = 'modalOverlay';
            this.overlay.className = 'modal-overlay';
            document.body.appendChild(this.overlay);
        }
    }

    static setupEventListeners() {
        // Закрытие по клику на overlay
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.closeActive();
            }
        });

        // Закрытие по ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.closeActive();
            }
        });
    }

    static show(content, options = {}) {
        const modalId = Date.now() + Math.random();
        
        const modal = this.createModal(modalId, content, options);
        this.overlay.appendChild(modal);
        
        // Показываем overlay
        this.overlay.classList.add('show');
        
        // Анимация появления модального окна
        setTimeout(() => {
            modal.classList.add('modal-animate-in');
        }, 10);
        
        this.activeModal = { id: modalId, element: modal, options };
        
        // Блокируем скролл body
        document.body.style.overflow = 'hidden';
        
        return modalId;
    }

    static createModal(id, content, options) {
        const modal = document.createElement('div');
        modal.className = `modal ${options.className || ''}`;
        modal.setAttribute('data-modal-id', id);
        
        modal.innerHTML = content;
        
        // Добавляем кнопку закрытия если не отключена
        if (!options.hideClose) {
            this.addCloseButton(modal);
        }
        
        return modal;
    }

    static addCloseButton(modal) {
        if (!modal.querySelector('.modal-close')) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'modal-close';
            closeBtn.innerHTML = `
                <svg viewBox="0 0 24 24" width="16" height="16">
                    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                </svg>
            `;
            closeBtn.addEventListener('click', () => this.closeActive());
            modal.appendChild(closeBtn);
        }
    }

    static closeActive() {
        if (!this.activeModal) return;
        
        const { element, options } = this.activeModal;
        
        // Анимация скрытия
        element.classList.remove('modal-animate-in');
        element.classList.add('modal-animate-out');
        
        setTimeout(() => {
            if (element.parentNode) {
                element.parentNode.removeChild(element);
            }
            
            // Скрываем overlay если нет других модальных окон
            if (this.overlay.children.length === 0) {
                this.overlay.classList.remove('show');
                document.body.style.overflow = '';
            }
            
            // Вызываем колбэк закрытия если есть
            if (options.onClose) {
                options.onClose();
            }
            
            this.activeModal = null;
        }, 300);
    }

    static closeAll() {
        while (this.overlay.children.length > 0) {
            this.closeActive();
        }
    }

    // PIN-код модальное окно
    static openPinEntry(callback, title = "Введите пин код") {
        let pinValue = '';
        
        const content = `
            <div class="modal-header">
                <h2 class="modal-title">${title}</h2>
            </div>
            <div class="modal-content">
                <div class="pin-display" id="pinDisplay">
                    <span id="pinValue"></span>
                    <button class="pin-delete" id="pinDelete" style="display: none;">×</button>
                </div>
                <div class="pin-keypad">
                    ${[1,2,3,4,5,6,7,8,9].map(num => 
                        `<button class="pin-key" data-digit="${num}">${num}</button>`
                    ).join('')}
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-primary" id="pinConfirm" disabled>Подтвердить</button>
            </div>
        `;
        
        const modalId = this.show(content, { className: 'pin-modal' });
        
        // Обработчики событий
        const modal = document.querySelector(`[data-modal-id="${modalId}"]`);
        const pinDisplay = modal.querySelector('#pinValue');
        const pinDelete = modal.querySelector('#pinDelete');
        const pinConfirm = modal.querySelector('#pinConfirm');
        
        // Клики по цифрам
        modal.querySelectorAll('.pin-key').forEach(key => {
            key.addEventListener('click', () => {
                const digit = key.dataset.digit;
                if (pinValue.length < 6) {
                    pinValue += digit;
                    this.updatePinDisplay(pinDisplay, pinDelete, pinConfirm, pinValue);
                }
            });
        });
        
        // Удаление последней цифры
        pinDelete.addEventListener('click', () => {
            pinValue = pinValue.slice(0, -1);
            this.updatePinDisplay(pinDisplay, pinDelete, pinConfirm, pinValue);
        });
        
        // Подтверждение
        pinConfirm.addEventListener('click', () => {
            callback(pinValue);
            this.closeActive();
        });
        
        return modalId;
    }

    static updatePinDisplay(display, deleteBtn, confirmBtn, value) {
        display.textContent = value;
        deleteBtn.style.display = value.length > 0 ? 'block' : 'none';
        confirmBtn.disabled = value.length === 0;
    }

    // Выбор стола
    static openTableSelection(currentTableId, callback) {
        const content = `
            <div class="modal-header">
                <h2 class="modal-title">Выберите стол</h2>
            </div>
            <div class="modal-content">
                <div class="tables-grid" id="tablesGrid">
                    <!-- Столы будут загружены динамически -->
                </div>
            </div>
        `;
        
        const modalId = this.show(content, { className: 'table-modal' });
        
        // Загружаем столы
        this.loadTables(modalId, currentTableId, callback);
        
        return modalId;
    }

    static async loadTables(modalId, currentTableId, callback) {
        try {
            console.log('🏪 Loading tables...');
            console.log('🔧 ClientAPI available:', typeof window.ClientAPI);
            console.log('🔧 ClientAPI.getTables available:', typeof window.ClientAPI?.getTables);
            
            if (!window.ClientAPI || typeof window.ClientAPI.getTables !== 'function') {
                throw new Error('ClientAPI.getTables is not available');
            }
            
            const modal = document.querySelector(`[data-modal-id="${modalId}"]`);
            const grid = modal.querySelector('#tablesGrid');
            
            const response = await window.ClientAPI.getTables();
            
            if (response.status === 'success') {
                const tables = response.data.tables;
                
                // Умное вычисление количества колонок для равномерного распределения
                const totalTables = tables.length;
                let columns;
                
                if (totalTables <= 6) {
                    columns = 3; // 1-6 столов: 3 колонки
                } else if (totalTables <= 10) {
                    columns = 5; // 7-10 столов: 5 колонок (10 = 2 ряда по 5)
                } else if (totalTables <= 15) {
                    columns = 5; // 11-15 столов: 5 колонок (12 = 3 ряда: 5+5+2)
                } else if (totalTables <= 20) {
                    columns = 5; // 16-20 столов: 5 колонок (20 = 4 ряда по 5)
                } else if (totalTables <= 28) {
                    columns = 7; // 21-28 столов: 7 колонок
                } else {
                    columns = 8; // >28 столов: 8 колонок
                }
                
                grid.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
                console.log(`📐 Tables: ${totalTables}, Columns: ${columns}, Layout: ${Math.ceil(totalTables/columns)} rows`);
                
                grid.innerHTML = tables.map(table => `
                    <button class="table-option ${table.id === currentTableId ? 'selected' : ''} ${!table.is_available ? 'occupied' : ''}"
                            data-table-id="${table.id}"
                            data-table-number="${table.table_number}"
                            ${!table.is_available ? 'disabled' : ''}>
                        ${table.table_number}
                    </button>
                `).join('');
                
                // Обработчики кликов
                grid.querySelectorAll('.table-option:not(.occupied)').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const tableId = parseInt(btn.dataset.tableId, 10);
                        const tableNumber = parseInt(btn.dataset.tableNumber, 10);
                        
                        // Обновляем выбранный стол
                        grid.querySelectorAll('.table-option').forEach(b => b.classList.remove('selected'));
                        btn.classList.add('selected');
                        
                        // Вызываем callback и закрываем модальное окно
                        setTimeout(() => {
                            if (callback) callback(tableId, tableNumber);
                            this.closeActive();
                        }, 300);
                    });
                });
            } else {
                throw new Error(response.message);
            }
            
        } catch (error) {
            APIUtils.handleError(error, 'Не удалось загрузить столы');
            this.closeActive();
        }
    }

    // Бонусная карта
    static openBonusCard(callback) {
        let cardNumber = '';
        
        const content = `
            <div class="modal-header">
                <h2 class="modal-title">Введите номер карты</h2>
            </div>
            <div class="modal-content">
                <div class="card-number-display" id="cardDisplay">
                    <span id="cardValue"></span>
                    <button class="card-delete" id="cardDelete" style="display: none;">×</button>
                </div>
                <div class="pin-keypad">
                    ${[1,2,3,4,5,6,7,8,9,0].map(num => 
                        `<button class="pin-key" data-digit="${num}">${num}</button>`
                    ).join('')}
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="ModalManager.closeActive()">Отмена</button>
                <button class="btn btn-primary" id="cardConfirm" disabled>Подтвердить</button>
            </div>
        `;
        
        const modalId = this.show(content, { className: 'bonus-modal' });
        
        // Обработчики событий
        const modal = document.querySelector(`[data-modal-id="${modalId}"]`);
        const cardDisplay = modal.querySelector('#cardValue');
        const cardDelete = modal.querySelector('#cardDelete');
        const cardConfirm = modal.querySelector('#cardConfirm');
        
        // Клики по цифрам
        modal.querySelectorAll('.pin-key').forEach(key => {
            key.addEventListener('click', () => {
                const digit = key.dataset.digit;
                if (cardNumber.length < 6) {
                    cardNumber += digit;
                    this.updateCardDisplay(cardDisplay, cardDelete, cardConfirm, cardNumber);
                }
            });
        });
        
        // Удаление последней цифры
        cardDelete.addEventListener('click', () => {
            cardNumber = cardNumber.slice(0, -1);
            this.updateCardDisplay(cardDisplay, cardDelete, cardConfirm, cardNumber);
        });
        
        // Подтверждение
        cardConfirm.addEventListener('click', async () => {
            try {
                APIUtils.showLoading(cardConfirm, 'Проверяем...');
                
                const response = await ClientAPI.verifyBonusCard(cardNumber);
                
                if (response.status === 'success') {
                    callback(response.data);
                    this.closeActive();
                    NotificationManager.showSuccess('Бонусная карта применена!');
                } else {
                    throw new Error(response.message || 'Карта не найдена');
                }
                
            } catch (error) {
                APIUtils.handleError(error, 'Не удалось проверить карту');
            } finally {
                APIUtils.hideLoading(cardConfirm);
            }
        });
        
        return modalId;
    }

    static updateCardDisplay(display, deleteBtn, confirmBtn, value) {
        display.textContent = value;
        deleteBtn.style.display = value.length > 0 ? 'block' : 'none';
        confirmBtn.disabled = value.length !== 6;
    }

    // Подтверждение заказа
    static openOrderConfirmation(orderData) {
        const timeoutSeconds = window.CLIENT_SETTINGS?.order_cancel_timeout || 300;
        let remainingTime = timeoutSeconds;
        let countdownInterval;
        
        const content = `
            <div class="modal-header">
                <h2 class="modal-title">Ваш заказ принят в обработку!</h2>
            </div>
            <div class="modal-content">
                <div class="order-success-icon">✅</div>
                <div class="order-message">Заказ №${orderData.order_id || '0000'}</div>
                <div class="order-submessage">
                    Вы можете отменить или убрать пункты из вашего заказа в течении:
                </div>
                <div class="countdown-timer" id="countdownTimer">${this.formatTime(remainingTime)}</div>
                <div class="order-actions">
                    <button class="btn btn-outline" onclick="ModalManager.closeActive()">Закрыть</button>
                    <button class="btn" style="background: var(--minus-btn); color: var(--white);" id="cancelOrderBtn">
                        Отменить/убрать
                    </button>
                </div>
            </div>
        `;
        
        const modalId = this.show(content, { 
            className: 'order-confirmation-modal',
            hideClose: true
        });
        
        const modal = document.querySelector(`[data-modal-id="${modalId}"]`);
        const timer = modal.querySelector('#countdownTimer');
        const cancelBtn = modal.querySelector('#cancelOrderBtn');
        
        // Запускаем обратный отсчет
        countdownInterval = setInterval(() => {
            remainingTime--;
            
            const formattedTime = this.formatTime(remainingTime);
            timer.textContent = formattedTime;
            
            // Меняем цвет таймера
            if (remainingTime <= 60) {
                timer.className = 'countdown-timer danger';
            } else if (remainingTime <= 120) {
                timer.className = 'countdown-timer warning';
            }
            
            if (remainingTime <= 0) {
                clearInterval(countdownInterval);
                cancelBtn.disabled = true;
                cancelBtn.textContent = 'Время истекло';
                timer.textContent = '0:00';
            }
        }, 1000);
        
        // Обработчик отмены заказа
        cancelBtn.addEventListener('click', () => {
            this.showConfirm(
                'Отменить заказ?',
                'Заказ будет полностью отменен',
                async () => {
                    try {
                        await ClientAPI.cancelOrder(orderData.order_id);
                        clearInterval(countdownInterval);
                        this.closeActive();
                        NotificationManager.showSuccess('Заказ отменен');
                    } catch (error) {
                        APIUtils.handleError(error, 'Не удалось отменить заказ');
                    }
                }
            );
        });
        
        // Очищаем интервал при закрытии
        const originalClose = this.closeActive.bind(this);
        this.closeActive = () => {
            clearInterval(countdownInterval);
            this.closeActive = originalClose;
            originalClose();
        };
        
        return modalId;
    }

    // Подтверждение действия
    static showConfirm(title, message, onConfirm, onCancel = null) {
        const content = `
            <div class="modal-header">
                <h2 class="modal-title">${title}</h2>
            </div>
            <div class="modal-content">
                <div class="confirm-icon">⚠️</div>
                <div class="confirm-message">${message}</div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-outline" id="confirmCancel">Отмена</button>
                <button class="btn btn-primary" id="confirmOk">Подтвердить</button>
            </div>
        `;
        
        const modalId = this.show(content, { className: 'confirm-modal' });
        
        const modal = document.querySelector(`[data-modal-id="${modalId}"]`);
        
        modal.querySelector('#confirmCancel').addEventListener('click', () => {
            if (onCancel) onCancel();
            this.closeActive();
        });
        
        modal.querySelector('#confirmOk').addEventListener('click', () => {
            if (onConfirm) onConfirm();
            this.closeActive();
        });
        
        return modalId;
    }

    // Утилиты
    static formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    // Открытие модального окна выбора стола с PIN-кодом
    static openTableWithPin(currentTableId) {
        this.openPinEntry((pin) => {
            // Проверяем PIN-код
                            window.ClientAPI.verifyTablePin(pin).then(response => {
                if (response.status === 'success') {
                    // Закрываем PIN модальное окно
                    this.closeActive();
                    
                    // Небольшая задержка перед открытием модального окна столов
                    setTimeout(() => {
                        this.openTableSelection(currentTableId, (tableId, tableNumber) => {
                            try {
                                CartManager.setTable(tableId, tableNumber);
                            } catch (e) {
                                NotificationManager.showError('Не удалось выбрать стол');
                            }
                        });
                    }, 300);
                } else {
                    NotificationManager.showError('Неверный PIN-код');
                }
            }).catch(error => {
                APIUtils.handleError(error, 'Ошибка проверки PIN-кода');
            });
        }, "Введите PIN-код для доступа к столам");
    }
}

// Экспортируем в глобальную область
window.ModalManager = ModalManager;