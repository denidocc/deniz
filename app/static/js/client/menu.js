/**
 * Модуль для работы с меню и категориями
 */

class MenuManager {
    static async init() {
        console.log('📱 Initializing Menu Page');
        
        this.currentLanguage = window.CLIENT_CONFIG?.currentLanguage || 'ru';
        this.currentCategory = null;
        this.searchTerm = '';
        this.menuData = null;
        
        // Инициализируем компоненты
        this.initializeElements();
        this.setupEventListeners();
        
        // Загружаем меню
        await this.loadMenu();
        

    }

    static initializeElements() {
        this.categoriesMenu = document.getElementById('categoriesMenu');
        this.dishesGrid = document.getElementById('dishesGrid');
        this.loadingState = document.getElementById('loadingState');
        this.errorState = document.getElementById('errorState');
        this.emptyState = document.getElementById('emptyState');
        this.searchInput = document.getElementById('dishSearch');
    }

    static setupEventListeners() {
        // Поиск блюд
        if (this.searchInput) {
            const debouncedSearch = APIUtils.debounce((term) => {
                this.searchTerm = term;
                this.loadMenu();
            }, 300);
            
            this.searchInput.addEventListener('input', (e) => {
                debouncedSearch(e.target.value.trim());
            });
        }

        // Переключение языков
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const lang = e.target.dataset.lang;
                this.switchLanguage(lang);
            });
        });

        // Очистка поиска при ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.searchInput) {
                this.searchInput.value = '';
                this.searchTerm = '';
                this.loadMenu();
            }
        });
    }

    static async loadMenu() {
        try {
            if (!window.ClientAPI || typeof window.ClientAPI.getMenu !== 'function') {
                throw new Error('window.ClientAPI.getMenu is not available');
            }
            
            this.showLoadingState();
            
            const params = {
                lang: this.currentLanguage
            };
            
            if (this.currentCategory) {
                params.category_id = this.currentCategory;
            }
            
            if (this.searchTerm) {
                params.search = this.searchTerm;
            }
            
            const response = await window.ClientAPI.getMenu(params);
            
            if (response.status === 'success') {
                this.menuData = response.data;
                this.renderMenu();
                this.hideGlobalPreloader();
            } else {
                throw new Error(response.message || 'Ошибка загрузки меню');
            }
            
        } catch (error) {
            console.error('Menu loading error:', error);
            this.showErrorState();
            this.hideGlobalPreloader();
            APIUtils.handleError(error, 'Не удалось загрузить меню');
        }
    }

    static renderMenu() {
        this.renderCategories();
        this.renderDishes();
        this.showContentState();
    }

    static renderCategories() {
        if (!this.categoriesMenu || !this.menuData.categories) return;
        
        const categoriesHTML = this.menuData.categories.map(category => `
            <div class="category-item ${this.currentCategory === category.id ? 'active' : ''}" 
                 data-category-id="${category.id}"
                 onclick="MenuManager.selectCategory(${category.id})">
                <div class="category-name">${this.escapeHTML(category.name)}</div>
                <div class="category-count">${category.count} блюд</div>
            </div>
        `).join('');
        
        // Добавляем "Все меню"
        const allMenuHTML = `
            <div class="category-item ${!this.currentCategory ? 'active' : ''}" 
                 data-category-id="all"
                 onclick="MenuManager.selectCategory(null)">
                <div class="category-name">Все меню</div>
                <div class="category-count">${this.getTotalDishesCount()} блюд</div>
            </div>
        `;
        
        this.categoriesMenu.innerHTML = allMenuHTML + categoriesHTML;
    }

    static renderDishes() {
        if (!this.dishesGrid || !this.menuData.dishes) return;
        
        if (this.menuData.dishes.length === 0) {
            this.showEmptyState();
            return;
        }
        
        const dishesHTML = this.menuData.dishes.map(dish => this.createDishCard(dish)).join('');
        this.dishesGrid.innerHTML = dishesHTML;
    }

    static createDishCard(dish) {
        const typeIcon = dish.preparation_type === 'kitchen' ? 
            '<svg class="dish-type-icon" viewBox="0 0 24 24"><path d="M8.1 13.34L11.9 9.54A5.029 5.029 0 1 0 7.46 15.08L8.1 13.34ZM12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L19 5V4A2 2 0 0 0 17 2H15A2 2 0 0 0 13 4V5L11 7V9A2 2 0 0 0 13 11H15V12L16 13V22H18V13L19 12V11A2 2 0 0 0 21 9M7 22A2 2 0 0 0 9 20V18A2 2 0 0 0 7 16H5A2 2 0 0 0 3 18V20A2 2 0 0 0 5 22H7Z"/></svg>' : 
            '<svg class="dish-type-icon" viewBox="0 0 24 24"><path d="M5 4V7H10.5V19H13.5V7H19V4H5Z"/></svg>';
        
        const cartQuantity = CartManager.getItemQuantity(dish.id);
        const actionsHTML = cartQuantity > 0 ? `
            <div class="dish-actions">
                <button class="btn-round btn-minus" onclick="CartManager.removeItem(${dish.id})">−</button>
                <span class="quantity-display">${cartQuantity}</span>
                <button class="btn-round btn-plus" onclick="CartManager.addItem(${dish.id})">+</button>
            </div>
        ` : `
            <div class="dish-actions">
                <button class="btn-round btn-plus" onclick="CartManager.addItem(${dish.id})">+</button>
            </div>
        `;
        
        return `
            <div class="dish-card" data-dish-id="${dish.id}">
                
                <img class="dish-image" 
                     src="${dish.image_url || '/static/assets/images/fish.png'}" 
                     alt="${this.escapeHTML(dish.name)}"
                     loading="lazy">
                
                <div class="dish-content">
                    <div class="dish-header">
                        <h3 class="dish-name">${this.escapeHTML(dish.name)}</h3>
                        <p class="dish-description">${this.escapeHTML(dish.description)}</p>
                    </div>
                    
                    <div class="dish-footer">
                        <div class="dish-price">
                            ${APIUtils.formatPrice(dish.price)}
                        </div>
                        ${actionsHTML}
                    </div>
                </div>
            </div>
        `;
    }

    static selectCategory(categoryId) {
        this.currentCategory = categoryId;
        this.loadMenu();
        
        // Обновляем активное состояние категорий
        document.querySelectorAll('.category-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = categoryId ? 
            document.querySelector(`[data-category-id="${categoryId}"]`) :
            document.querySelector('[data-category-id="all"]');
        
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }

    static switchLanguage(language) {
        if (this.currentLanguage === language) return;
        
        this.currentLanguage = language;
        
        // Обновляем активную кнопку языка
        document.querySelectorAll('.lang-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeBtn = document.querySelector(`[data-lang="${language}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
        
        // Сохраняем выбор языка
        StorageManager.set('language', language);
        
        // Перезагружаем меню
        this.loadMenu();
        
        // Обновляем переводы интерфейса
        this.updateInterfaceTexts(language);
        
        NotificationManager.showSuccess('Язык изменен');
    }

    static updateInterfaceTexts(language) {
        const translations = {
            'ru': {
                'search-placeholder': 'Введите название блюда',
                'cart-title': 'Корзина',
                'clear-cart': 'Очистить',
                'empty-cart': 'Корзина пуста, но море полное.\nЗагляните в меню — там волны вкуса.',
                'loading': 'Загружаем меню...',
                'error-title': 'Ошибка загрузки меню',
                'error-button': 'Обновить',
                'empty-title': 'Ничего не найдено',
                'empty-subtitle': 'Попробуйте изменить поисковый запрос'
            },
            'tk': {
                'search-placeholder': 'Nahar adyny giriziň',
                'cart-title': 'Sebetim',
                'clear-cart': 'Arassala',
                'empty-cart': 'Sebet boş, ýöne deňiz doly.\nMenýuny göriň — ol ýerde tagam tolkunlary bar.',
                'loading': 'Menýu ýüklenýär...',
                'error-title': 'Menýu ýüklenmedi',
                'error-button': 'Täzelä',
                'empty-title': 'Hiç zat tapylmady',
                'empty-subtitle': 'Gözleg sözlerini üýtgediň'
            },
            'en': {
                'search-placeholder': 'Enter dish name',
                'cart-title': 'Cart',
                'clear-cart': 'Clear',
                'empty-cart': 'Cart is empty, but the sea is full.\nCheck the menu — there are waves of taste.',
                'loading': 'Loading menu...',
                'error-title': 'Menu loading error',
                'error-button': 'Refresh',
                'empty-title': 'Nothing found',
                'empty-subtitle': 'Try changing your search query'
            }
        };
        
        const texts = translations[language] || translations['ru'];
        
        // Обновляем тексты элементов
        const searchInput = document.getElementById('dishSearch');
        if (searchInput) searchInput.placeholder = texts['search-placeholder'];
        
        const cartTitle = document.querySelector('.cart-title');
        if (cartTitle) cartTitle.textContent = texts['cart-title'];
        
        const clearBtn = document.getElementById('clearCartBtn');
        if (clearBtn) clearBtn.textContent = texts['clear-cart'];
        
        const emptyCartText = document.querySelector('.empty-cart-text');
        if (emptyCartText) emptyCartText.textContent = texts['empty-cart'];
    }

    static showLoadingState() {
        this.hideAllStates();
        if (this.loadingState) this.loadingState.style.display = 'flex';
    }

    static showErrorState() {
        this.hideAllStates();
        if (this.errorState) this.errorState.style.display = 'flex';
    }

    static showEmptyState() {
        this.hideAllStates();
        if (this.emptyState) this.emptyState.style.display = 'flex';
    }

    static showContentState() {
        this.hideAllStates();
        if (this.dishesGrid) this.dishesGrid.style.display = 'grid';
    }

    static hideAllStates() {
        [this.loadingState, this.errorState, this.emptyState, this.dishesGrid].forEach(element => {
            if (element) element.style.display = 'none';
        });
    }

    static getTotalDishesCount() {
        if (!this.menuData || !this.menuData.categories) return 0;
        return this.menuData.categories.reduce((total, category) => total + category.count, 0);
    }

    static escapeHTML(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static refreshMenu() {
        this.loadMenu();
    }

    static search(term) {
        this.searchTerm = term;
        this.loadMenu();
    }

    static clearSearch() {
        this.searchTerm = '';
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        this.loadMenu();
    }

    static hideGlobalPreloader() {
        const preloader = document.getElementById('globalPreloader');
        if (preloader) {
            preloader.style.display = 'none';
            console.log('🔧 Global preloader hidden');
        }
    }
}

// Экспортируем в глобальную область
window.MenuManager = MenuManager;