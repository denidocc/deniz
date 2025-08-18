/**
 * Модуль управления корзиной
 */

class CartManager {
    static init() {
    
        
        this.items = new Map();
        // Используем tableId из конфигурации или значение по умолчанию
        this.tableId = window.CLIENT_CONFIG?.tableId || null;
        this.tableNumber = undefined;
        this.bonusCard = null;
        
        // Получаем настройки из конфигурации
        this.loadSettings();
        
        // Загружаем корзину из localStorage
        this.loadFromStorage();
        
        // Инициализируем элементы
        this.initializeElements();
        
        // Синхронизируем отображаемый номер стола, если сохранён только id
        this.ensureTableNumberConsistency();

        // Устанавливаем обработчики
        this.setupEventListeners();
        
        // Рендерим корзину
        this.render();
        
        // Логируем для отладки
        console.log('🛒 CartManager initialized with tableId:', this.tableId);

    }

    static loadSettings() {
        // Получаем настройки из конфигурации
        const config = window.CLIENT_CONFIG || {};
        const settings = config.settings || {};
        
        // Сервисный сбор
        this.serviceChargePercent = settings.service_charge || 5;
        this.serviceChargeEnabled = settings.service_charge_enabled !== 'false';
        
        // Валюта
        this.currency = settings.currency || 'TMT';
        this.currencySymbol = this.getCurrencySymbol(this.currency);
        
        // Название ресторана
        this.restaurantName = settings.restaurant_name || 'DENIZ Restaurant';
        

    }
    
    static getCurrencySymbol(currency) {
        const symbols = {
            'TMT': 'тмт',
            'RUB': '₽',
            'USD': '$',
            'EUR': '€'
        };
        return symbols[currency] || currency;
    }

    static initializeElements() {
        this.cartContent = document.getElementById('cartContent');
        this.cartFooter = document.getElementById('cartFooter');
        this.clearCartBtn = document.getElementById('clearCartBtn');
        this.tableSelectBtn = document.getElementById('tableSelectBtn');
        this.currentTableNumber = document.getElementById('currentTableNumber');
    }

    static setupEventListeners() {
        // Очистка корзины
        if (this.clearCartBtn) {
            this.clearCartBtn.addEventListener('click', () => {
                this.clear();
            });
        }

        // Выбор стола - обработчик перенесен в base.html для единообразия

        // Слушаем события изменения корзины
        document.addEventListener('cartUpdated', () => {
            this.render();
            this.saveToStorage();
        });

        // Автосохранение при изменении
        window.addEventListener('beforeunload', () => {
            this.saveToStorage();
        });
    }

    static addItem(dishId, quantity = 1) {

        
        // Получаем данные блюда из меню
        const dish = this.getDishById(dishId);
        if (!dish) {

            NotificationManager.showError('Блюдо не найдено');
            return;
        }

        const currentQuantity = this.items.get(dishId) || 0;
        const newQuantity = currentQuantity + quantity;
        
        if (newQuantity <= 0) {
            this.removeItem(dishId);
            return;
        }

        this.items.set(dishId, newQuantity);
        
        // Триггерим событие обновления
        this.triggerUpdate();
        
        // Показываем уведомление
        NotificationManager.showSuccess(`${dish.name} добавлено в корзину`);
        
        // Обновляем кнопки в карточках блюд
        this.updateDishButtons();
    }

    static removeItem(dishId, quantity = 1) {
        
        const currentQuantity = this.items.get(dishId) || 0;
        const newQuantity = currentQuantity - quantity;
        
        if (newQuantity <= 0) {
            this.items.delete(dishId);
        } else {
            this.items.set(dishId, newQuantity);
        }
        
        this.triggerUpdate();
        this.updateDishButtons();
    }

    static setItemQuantity(dishId, quantity) {
        if (quantity <= 0) {
            this.items.delete(dishId);
        } else {
            this.items.set(dishId, quantity);
        }
        
        this.triggerUpdate();
        this.updateDishButtons();
    }

    static getItemQuantity(dishId) {
        return this.items.get(dishId) || 0;
    }

    static clear() {
        if (this.items.size === 0) {
            NotificationManager.showInfo('Корзина уже пуста');
            return;
        }

        // Показываем подтверждение
        ModalManager.showConfirm('Очистить корзину?', 'Все товары будут удалены из корзины', () => {
            this.items.clear();
            this.bonusCard = null;
            this.triggerUpdate();
            this.updateDishButtons();
            NotificationManager.showSuccess('Корзина очищена');
        });
    }

    static getTotalItems() {
        let total = 0;
        this.items.forEach(quantity => {
            total += quantity;
        });
        return total;
    }

    static getSubtotal() {
        let subtotal = 0;
        this.items.forEach((quantity, dishId) => {
            const dish = this.getDishById(dishId);
            if (dish) {
                subtotal += dish.price * quantity;
            }
        });
        return subtotal;
    }

    static getServiceCharge() {
        if (!this.serviceChargeEnabled) return 0;
        return this.getSubtotal() * (this.serviceChargePercent / 100);
    }

    static getDiscount() {
        if (!this.bonusCard) return 0;
        return this.getSubtotal() * (this.bonusCard.discount_percent / 100);
    }

    static getTotal() {
        return this.getSubtotal() + this.getServiceCharge() - this.getDiscount();
    }

    static render() {
        if (!this.cartContent) return;

        if (this.items.size === 0) {
            this.renderEmpty();
        } else {
            this.renderItems();
        }
    }

    static renderEmpty() {
        this.cartContent.innerHTML = `
            <div class="empty-cart">
                <div class="empty-cart-illustration">
                    <img src="/static/assets/images/fish.png" alt="Рыба" class="fish-image">
                </div>
                <p class="empty-cart-text">
                    <strong>Корзина пуста, но море полное.</strong><br>
                    Загляните в меню — там волны вкуса.
                </p>
            </div>
            <div class="rudder-pattern"></div>
        `;
        
        if (this.cartFooter) {
            this.cartFooter.style.display = 'none';
        }
    }

    static renderItems() {
        const itemsHTML = Array.from(this.items.entries()).map(([dishId, quantity]) => {
            const dish = this.getDishById(dishId);
            if (!dish) return '';
            
            return `
                <div class="cart-item" data-dish-id="${dishId}">
                    <button class="cart-item-remove" onclick="CartManager.removeItem(${dishId}, ${quantity})" title="Удалить блюдо">×</button>
                    
                    <img class="cart-item-image" 
                         src="${dish.image_url || '/static/assets/images/fish.png'}" 
                         alt="${this.escapeHTML(dish.name)}">
                    
                    <div class="cart-item-info">
                        <div class="cart-item-name">${this.escapeHTML(dish.name)}</div>
                        <div class="cart-item-price">${APIUtils.formatPrice(dish.price)}</div>
                    </div>
                    
                    <div class="cart-item-controls">
                        <button class="btn-round btn-minus" onclick="CartManager.removeItem(${dishId})" title="Убрать одно">−</button>
                        <span class="quantity-display">${quantity}</span>
                        <button class="btn-round btn-plus" onclick="CartManager.addItem(${dishId})" title="Добавить еще">+</button>
                    </div>
                </div>
            `;
        }).join('');

        this.cartContent.innerHTML = `
            <div class="cart-items">
                ${itemsHTML}
            </div>
            <div class="rudder-pattern"></div>
        `;

        this.renderFooter();
    }

    static renderFooter() {
        if (!this.cartFooter) return;

        const subtotal = this.getSubtotal();
        const serviceCharge = this.getServiceCharge();
        const discount = this.getDiscount();
        const total = this.getTotal();

        const discountHTML = discount > 0 ? `
            <div class="summary-line discount">
                <span class="summary-label">Скидка -${this.bonusCard.discount_percent}%</span>
                <span class="summary-value">-${APIUtils.formatPrice(discount)}</span>
            </div>
        ` : '';

        this.cartFooter.innerHTML = `
            <div class="cart-summary">
                <div class="summary-line subtotal">
                    <span class="summary-label">Подытог</span>
                    <span class="summary-value">${APIUtils.formatPrice(subtotal)}</span>
                </div>
                
                ${this.serviceChargeEnabled ? `
                <div class="summary-line service-charge">
                    <span class="summary-label">Сервисный сбор ${this.serviceChargePercent}%</span>
                    <span class="summary-value">${APIUtils.formatPrice(serviceCharge)}</span>
                </div>
                ` : ''}
                
                ${discountHTML}
                
                <div class="summary-line total">
                    <span class="summary-label">Итого</span>
                    <span class="summary-value">${APIUtils.formatPrice(total)}</span>
                </div>
            </div>
            
            <button class="btn bonus-card-btn" onclick="CartManager.openBonusCard()">
                ${this.bonusCard ? '💳 Бонусная карта применена' : '💳 Бонусная карта'}
            </button>
            
            <button class="btn btn-primary continue-order-btn" onclick="CartManager.proceedToOrder()">
                Продолжить заказ
            </button>
        `;

        this.cartFooter.style.display = 'block';
    }

    static updateDishButtons() {
        // Обновляем кнопки во всех карточках блюд
        document.querySelectorAll('.dish-card').forEach(card => {
            const dishId = parseInt(card.dataset.dishId);
            const quantity = this.getItemQuantity(dishId);
            const actionsDiv = card.querySelector('.dish-footer .dish-actions');
            
            if (actionsDiv) {
                if (quantity > 0) {
                    actionsDiv.innerHTML = `
                        <button class="btn-round btn-minus" onclick="CartManager.removeItem(${dishId})">−</button>
                        <span class="quantity-display">${quantity}</span>
                        <button class="btn-round btn-plus" onclick="CartManager.addItem(${dishId})">+</button>
                    `;
                } else {
                    actionsDiv.innerHTML = `
                        <button class="btn-round btn-plus" onclick="CartManager.addItem(${dishId})">+</button>
                    `;
                }
            }
        });
    }

    static setTable(tableId, tableNumber) {
        // tableId здесь - это номер стола (например, 1, 2, 3), а не ID из БД
        this.tableId = tableNumber || tableId; // Используем номер стола
        this.tableNumber = tableNumber || tableId;
        
        console.log('🛒 setTable called with:', { tableId, tableNumber, finalTableId: this.tableId });
        
        if (this.currentTableNumber) {
            this.currentTableNumber.textContent = this.tableNumber;
        }
        
        // Сохраняем в localStorage
        StorageManager.set('tableId', this.tableId);
        StorageManager.set('tableNumber', this.tableNumber);
        
        NotificationManager.showSuccess(`Выбран стол #${this.tableNumber}`);
    }

    static getCurrentTableId() {
        console.log('🔍 getCurrentTableId called, current tableId:', this.tableId);
        return this.tableId;
    }

    static openBonusCard() {
        ModalManager.openBonusCard((cardData) => {
            this.bonusCard = cardData;
            this.render();
            NotificationManager.showSuccess(`Бонусная карта применена! Скидка ${cardData.discount_percent}%`);
        });
    }

    static async proceedToOrder() {
        if (this.items.size === 0) {
            NotificationManager.showWarning('Корзина пуста');
            return;
        }

        try {
            // Подготавливаем данные заказа
            const orderData = {
                table_id: this.tableId,
                items: Array.from(this.items.entries()).map(([dishId, quantity]) => ({
                    dish_id: dishId,
                    quantity: quantity
                })),
                bonus_card: this.bonusCard ? this.bonusCard.card_number : null,
                language: MenuManager.currentLanguage || 'ru'
            };

            // Отправляем заказ
            APIUtils.showLoading(document.querySelector('.continue-order-btn'), 'Отправляем...');
            
            const response = await ClientAPI.createOrder(orderData);
            
            if (response.status === 'success') {
                // Показываем экран подтверждения
                ModalManager.openOrderConfirmation(response.data);
                
                // Очищаем корзину
                this.items.clear();
                this.bonusCard = null;
                this.render();
                this.updateDishButtons();
                
                NotificationManager.showSuccess('Заказ отправлен!');
            } else {
                throw new Error(response.message || 'Ошибка создания заказа');
            }
            
        } catch (error) {
            APIUtils.handleError(error, 'Не удалось отправить заказ');
        } finally {
            APIUtils.hideLoading(document.querySelector('.continue-order-btn'));
        }
    }

    static getDishById(dishId) {
        if (!window.MenuManager || !window.MenuManager.menuData) return null;
        return window.MenuManager.menuData.dishes.find(dish => dish.id === dishId);
    }

    static triggerUpdate() {
        document.dispatchEvent(new CustomEvent('cartUpdated', {
            detail: {
                items: this.items,
                total: this.getTotal(),
                count: this.getTotalItems()
            }
        }));
    }

    static saveToStorage() {
        const cartData = {
            items: Array.from(this.items.entries()),
            tableId: this.tableId,
            bonusCard: this.bonusCard,
            timestamp: Date.now()
        };
        StorageManager.set('cart', cartData);
    }

    static loadFromStorage() {
        const cartData = StorageManager.get('cart');
        if (cartData && cartData.timestamp) {
            // Проверяем, не слишком ли старые данные (24 часа)
            const isExpired = Date.now() - cartData.timestamp > 24 * 60 * 60 * 1000;
            
            if (!isExpired) {
                this.items = new Map(cartData.items || []);
            this.tableId = cartData.tableId || this.tableId;
            this.tableNumber = StorageManager.get('tableNumber') || this.tableId;
                this.bonusCard = cartData.bonusCard || null;
            }
        }
        
        // Загружаем сохраненный стол
        const savedTableId = StorageManager.get('tableId');
        const savedTableNumber = StorageManager.get('tableNumber');
        if (savedTableId) {
            this.tableId = parseInt(savedTableId, 10);
        }
        if (savedTableNumber) {
            this.tableNumber = parseInt(savedTableNumber, 10);
        } else {
            // Отложенно определим по справочнику столов
            this.tableNumber = undefined;
        }
    }

    static async ensureTableNumberConsistency() {
        try {
            // Если номер уже известен, обновим DOM и выйдем
            if (typeof this.tableNumber === 'number' && !Number.isNaN(this.tableNumber)) {
                if (this.currentTableNumber) this.currentTableNumber.textContent = this.tableNumber;
                return;
            }

            // Если id отсутствует, ничего не делаем
            if (!this.tableId) return;

            // Получаем таблицы и ищем соответствие id → table_number
            if (window.ClientAPI && typeof window.ClientAPI.getTables === 'function') {
                const resp = await window.ClientAPI.getTables();
                if (resp && resp.status === 'success' && resp.data && Array.isArray(resp.data.tables)) {
                    const t = resp.data.tables.find(t => t.id === this.tableId);
                    if (t) {
                        this.tableNumber = t.table_number;
                        StorageManager.set('tableNumber', this.tableNumber);
                        if (this.currentTableNumber) this.currentTableNumber.textContent = this.tableNumber;
                        NotificationManager.showInfo(`Выбран стол #${this.tableNumber}`);
                    }
                }
            }
        } catch (e) {
            // Тихо игнорируем, чтобы не мешать UX
        }
    }

    static escapeHTML(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Публичные методы для внешнего использования
    static getCartData() {
        return {
            items: Array.from(this.items.entries()),
            tableId: this.tableId,
            bonusCard: this.bonusCard,
            subtotal: this.getSubtotal(),
            serviceCharge: this.getServiceCharge(),
            discount: this.getDiscount(),
            total: this.getTotal(),
            totalItems: this.getTotalItems()
        };
    }

    // Методы для работы с бонусными картами
    static applyBonusCard(bonusData) {
        this.bonusCard = bonusData;
        this.saveToStorage();
        this.render();
        NotificationManager.showSuccess(`Применена скидка ${bonusData.discount_percent}%!`);
    }

    static removeBonusCard() {
        this.bonusCard = null;
        this.saveToStorage();
        this.render();
        NotificationManager.showInfo('Бонусная карта удалена');
    }

    // Методы ниже переопределены выше: setTable, getCurrentTableId, placeOrder
}

// Экспортируем в глобальную область
window.CartManager = CartManager;