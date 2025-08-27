/**
 * Модуль управления корзиной
 */

class CartManager {
    static init() {
    
        
        this.items = new Map();
        // Используем tableId из конфигурации или значение по умолчанию
        this.tableId = window.CLIENT_CONFIG?.tableId || 1;
        this.tableNumber = window.CLIENT_CONFIG?.tableNumber || 1;
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

    static async addItem(dishId, quantity = 1) {
        console.log('🛒 CartManager.addItem called:', { dishId, quantity, currentItems: Array.from(this.items.entries()) });
        
        try {
            // Получаем данные блюда из меню
            const dish = await this.getDishById(dishId);
            if (!dish) {
                NotificationManager.showError('Блюдо не найдено');
                return;
            }

            const currentQuantity = this.items.get(dishId) || 0;
            const newQuantity = currentQuantity + quantity;
            
            console.log('🛒 Quantity calculation:', { currentQuantity, newQuantity });
            
            if (newQuantity <= 0) {
                this.removeItem(dishId);
                return;
            }

            this.items.set(dishId, newQuantity);
            
            console.log('🛒 Item added, new cart state:', Array.from(this.items.entries()));
            
            // Триггерим событие обновления
            await this.triggerUpdate();
            
            // Показываем уведомление
            NotificationManager.showSuccess(`${dish.name} добавлено в корзину`);
            
                    // Обновляем кнопки в карточках блюд
        await this.updateDishButtons();
        
        // Сохраняем в localStorage
        this.saveToStorage();
        } catch (error) {
            console.error('🛒 Error adding item:', error);
            NotificationManager.showError('Ошибка добавления блюда');
        }
    }

    static async removeItem(dishId, quantity = 1) {
        
        const currentQuantity = this.items.get(dishId) || 0;
        const newQuantity = currentQuantity - quantity;
        
        if (newQuantity <= 0) {
            this.items.delete(dishId);
        } else {
            this.items.set(dishId, newQuantity);
        }
        
        await this.triggerUpdate();
        await this.updateDishButtons();
    }

    static async setItemQuantity(dishId, quantity) {
        if (quantity <= 0) {
            this.items.delete(dishId);
        } else {
            this.items.set(dishId, quantity);
        }
        
        await this.triggerUpdate();
        await this.updateDishButtons();
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
        ModalManager.showConfirm('Очистить корзину?', 'Все товары будут удалены из корзины', async () => {
            this.items.clear();
            this.bonusCard = null;
            await this.triggerUpdate();
            await this.updateDishButtons();
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

    static async getSubtotal() {
        let subtotal = 0;
        for (const [dishId, quantity] of this.items.entries()) {
            const dish = await this.getDishById(dishId);
            if (dish) {
                subtotal += dish.price * quantity;
            }
        }
        return subtotal;
    }

    static async getServiceCharge() {
        if (!this.serviceChargeEnabled) return 0;
        const subtotal = await this.getSubtotal();
        return subtotal * (this.serviceChargePercent / 100);
    }

    static async getDiscount() {
        if (!this.bonusCard) return 0;
        
        // Получаем discount_percent из правильного места
        const discountPercent = this.bonusCard.discount_percent || 
                              (this.bonusCard.card && this.bonusCard.card.discount_percent);
        
        if (!discountPercent) return 0;
        
        // Скидка рассчитывается от (подытог + сервисный сбор)
        const subtotal = await this.getSubtotal();
        const serviceCharge = await this.getServiceCharge();
        const totalBeforeDiscount = subtotal + serviceCharge;
        
        return totalBeforeDiscount * (discountPercent / 100);
    }

    static async getTotal() {
        try {
            const subtotal = await this.getSubtotal();
            const serviceCharge = await this.getServiceCharge();
            
            // Сначала считаем сумму до скидки
            const totalBeforeDiscount = subtotal + serviceCharge;
            
            // Затем применяем скидку
            let discount = 0;
            if (this.bonusCard) {
                const discountPercent = this.bonusCard.discount_percent || 
                                      (this.bonusCard.card && this.bonusCard.card.discount_percent);
                if (discountPercent) {
                    discount = totalBeforeDiscount * (discountPercent / 100);
                }
            }
            
            // Итоговая сумма: (подытог + сервисный сбор) - скидка
            const total = totalBeforeDiscount - discount;
            
            // Проверяем на корректность
            if (isNaN(total) || total < 0) {
                console.error('Invalid total calculation:', { subtotal, serviceCharge, discount, total });
                return totalBeforeDiscount; // Возвращаем без скидки в случае ошибки
            }
            
            return total;
        } catch (error) {
            console.error('Error calculating total:', error);
            // В случае ошибки возвращаем подытог + сервисный сбор
            const subtotal = await this.getSubtotal();
            const serviceCharge = await this.getServiceCharge();
            return subtotal + serviceCharge;
        }
    }

    static async render() {
        console.log('🛒 CartManager.render called, items count:', this.items.size, 'items:', Array.from(this.items.entries()));
        if (!this.cartContent) return;

        if (this.items.size === 0) {
            this.renderEmpty();
        } else {
            await this.renderItems();
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

    static async renderItems() {
        try {
            const itemsHTMLPromises = Array.from(this.items.entries()).map(async ([dishId, quantity]) => {
                const dish = await this.getDishById(dishId);
                if (!dish) {
                    console.warn('🛒 Dish not found for rendering, dishId:', dishId);
                    return '';
                }
                
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
            });
            
            const itemsHTML = await Promise.all(itemsHTMLPromises);
            const filteredItemsHTML = itemsHTML.filter(html => html !== '');

            this.cartContent.innerHTML = `
                <div class="cart-items">
                    ${filteredItemsHTML.join('')}
                </div>
                <div class="rudder-pattern"></div>
            `;

            await this.renderFooter();
        } catch (error) {
            console.error('🛒 Error rendering items:', error);
            this.renderEmpty();
        }
    }

    static async renderFooter() {
        if (!this.cartFooter) return;

        const subtotal = await this.getSubtotal();
        const serviceCharge = await this.getServiceCharge();
        const discount = await this.getDiscount();
        const total = await this.getTotal();

        console.log('🛒 renderFooter debug:', { 
            subtotal, 
            serviceCharge, 
            discount, 
            total, 
            bonusCard: this.bonusCard 
        });

        // Показываем скидку если есть бонусная карта и скидка больше 0
        const discountHTML = (this.bonusCard && discount > 0) ? `
            <div class="summary-line discount">
                <span class="summary-label">Скидка -${this.bonusCard.discount_percent || (this.bonusCard.card && this.bonusCard.card.discount_percent)}%</span>
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

    static async updateDishButtons() {
        try {
            // Обновляем кнопки во всех карточках блюд
            const dishCards = document.querySelectorAll('.dish-card');
            
            for (const card of dishCards) {
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
            }
        } catch (error) {
            console.error('🛒 Error updating dish buttons:', error);
        }
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

        // Проверяем, выбран ли стол
        if (!this.tableId) {
            NotificationManager.showError('Пожалуйста, выберите стол перед оформлением заказа');
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
                language: window.MenuManager?.currentLanguage || 'ru'
            };

            console.log('🛒 Order data prepared:', orderData);

            // Проверяем готовность API
            if (!window.ClientAPI || typeof window.ClientAPI.createOrder !== 'function') {
                throw new Error('API не готов. Попробуйте обновить страницу.');
            }
            
            // Отправляем заказ
            APIUtils.showLoading(document.querySelector('.continue-order-btn'), 'Отправляем...');
            
            const response = await window.ClientAPI.createOrder(orderData);
            
            if (response.status === 'success') {
                // Сохраняем данные заказа для модалки
                const orderInfo = {
                    order_id: response.data.order_id || response.data.id,
                    table_id: this.tableId,
                    items: Array.from(this.items.entries()),
                    total: await this.getTotal()
                };
                
                // Очищаем корзину
                this.items.clear();
                this.bonusCard = null;
                
                // Сохраняем в localStorage
                this.saveToStorage();
                
                // Обновляем интерфейс
                await this.render();
                await this.updateDishButtons();
                
                // Показываем модалку с таймером
                if (window.ModalManager && typeof window.ModalManager.openOrderConfirmation === 'function') {
                    window.ModalManager.openOrderConfirmation(orderInfo);
                } else {
                    NotificationManager.showSuccess('Заказ отправлен!');
                }
            } else {
                throw new Error(response.message || 'Ошибка создания заказа');
            }
            
        } catch (error) {
            // Проверяем, является ли это ошибкой о существующем заказе
            if (error.message && error.message.includes('уже есть активный заказ')) {
                ModalManager.showExistingOrderModal(error.message);
            } else {
                APIUtils.handleError(error, 'Не удалось отправить заказ');
            }
        } finally {
            APIUtils.hideLoading(document.querySelector('.continue-order-btn'));
        }
    }

    static async getDishById(dishId) {
        if (!window.MenuManager) {
            console.log('🛒 MenuManager not ready, dishId:', dishId);
            return null;
        }
        
        // Сначала пытаемся найти в текущем меню
        if (window.MenuManager.menuData && window.MenuManager.menuData.dishes) {
            const dish = window.MenuManager.menuData.dishes.find(dish => dish.id === dishId);
            if (dish) {
                console.log('🛒 getDishById found in current menu:', { dishId, dish });
                return dish;
            }
        }
        
        // Если не найдено, загружаем все блюда
        console.log('🛒 Dish not found in current menu, loading all dishes for dishId:', dishId);
        const allDishesData = await window.MenuManager.loadAllDishes();
        
        if (allDishesData && allDishesData.dishes) {
            const dish = allDishesData.dishes.find(dish => dish.id === dishId);
            console.log('🛒 getDishById result from all dishes:', { dishId, dish });
            return dish;
        }
        
        console.log('🛒 Dish not found anywhere, dishId:', dishId);
        return null;
    }

    static async triggerUpdate() {
        document.dispatchEvent(new CustomEvent('cartUpdated', {
            detail: {
                items: this.items,
                total: await this.getTotal(),
                count: this.getTotalItems()
            }
        }));
    }
    
    // Метод для обновления корзины после загрузки меню
    static async updateAfterMenuLoad() {
        console.log('🛒 Updating cart after menu load, current items:', Array.from(this.items.entries()));
        await this.render();
        await this.updateDishButtons();
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
        console.log('🛒 CartManager.loadFromStorage called');
        const cartData = StorageManager.get('cart');
        console.log('🛒 Cart data from storage:', cartData);
        
        if (cartData && cartData.timestamp) {
            // Проверяем, не слишком ли старые данные (24 часа)
            const isExpired = Date.now() - cartData.timestamp > 24 * 60 * 60 * 1000;
            console.log('🛒 Cart data expired:', isExpired);
            
            if (!isExpired) {
                this.items = new Map(cartData.items || []);
                this.tableId = cartData.tableId || this.tableId;
                this.tableNumber = StorageManager.get('tableNumber') || this.tableId;
                this.bonusCard = cartData.bonusCard || null;
                console.log('🛒 Cart loaded from storage:', Array.from(this.items.entries()));
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
        
        console.log('🛒 Final cart state after loading:', Array.from(this.items.entries()));
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
    static async getCartData() {
        return {
            items: Array.from(this.items.entries()),
            tableId: this.tableId,
            bonusCard: this.bonusCard,
            subtotal: await this.getSubtotal(),
            serviceCharge: await this.getServiceCharge(),
            discount: await this.getDiscount(),
            total: await this.getTotal(),
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

    // Добавить в CartManager:

    static setBonusCard(bonusCardData) {
        this.bonusCard = bonusCardData;
        console.log('🛒 Bonus card set:', this.bonusCard);
        
        // Перерисовываем корзину с новой скидкой
        this.render();
        
        // Сохраняем в localStorage
        this.saveToStorage();
    }

    static clearBonusCard() {
        this.bonusCard = null;
        console.log('🛒 Bonus card cleared');
        
        // Перерисовываем корзину без скидки
        this.render();
        
        // Сохраняем в localStorage
        this.saveToStorage();
    }
}

// Экспортируем в глобальную область
window.CartManager = CartManager;