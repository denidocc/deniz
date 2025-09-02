/**
 * Модуль для работы с блюдами
 */

class DishManager {
    static init() {

        
        this.setupEventListeners();
        

    }
    
    static setupEventListeners() {
        // Делегирование событий для динамически создаваемых элементов
        document.addEventListener('click', (e) => {
            // Кнопка добавления в корзину
            if (e.target.closest('.dish-add-btn')) {
                const dishCard = e.target.closest('.dish-card');
                if (dishCard) {
                    this.addToCart(dishCard);
                }
            }
            
            // Кнопка просмотра деталей блюда
            if (e.target.closest('.dish-details-btn')) {
                const dishCard = e.target.closest('.dish-card');
                if (dishCard) {
                    this.showDishDetails(dishCard);
                }
            }
        });
    }
    
    static addToCart(dishCard) {
        const dishData = this.extractDishData(dishCard);
        
        if (dishData && window.CartManager) {
            window.CartManager.addItem(dishData);
            this.showAddedToCartFeedback(dishCard);
        }
    }
    
    static extractDishData(dishCard) {
        try {
            const dishId = dishCard.getAttribute('data-dish-id');
            const dishName = dishCard.querySelector('.dish-name')?.textContent;
            const dishPrice = parseFloat(dishCard.querySelector('.dish-price')?.textContent.replace(/[^\d.]/g, ''));
            const dishImage = dishCard.querySelector('.dish-image')?.src;
            const dishDescription = dishCard.querySelector('.dish-description')?.textContent;
            
            return {
                id: dishId,
                name: dishName,
                price: dishPrice,
                image: dishImage,
                description: dishDescription,
                quantity: 1
            };
        } catch (error) {
            console.error('Error extracting dish data:', error);
            return null;
        }
    }
    
    static showAddedToCartFeedback(dishCard) {
        const btn = dishCard.querySelector('.dish-add-btn');
        if (btn) {
            const originalText = btn.textContent;
            btn.textContent = '✓ Добавлено';
            btn.classList.add('added');
            
            setTimeout(() => {
                btn.textContent = originalText;
                btn.classList.remove('added');
            }, 1500);
        }
    }
    
    static showDishDetails(dishCard) {
        const dishData = this.extractDishData(dishCard);
        
        if (dishData && window.ModalManager) {
            window.ModalManager.openDishDetails(dishData);
        }
    }
    
    static formatPrice(price) {
        return `${price.toFixed(0)} ₼`;
    }
    
    static createDishCard(dish) {
        return `
            <div class="dish-card" data-dish-id="${dish.id}">
                <div class="dish-image-container">
                    <img src="${dish.image_url || '/static/assets/images/fish.png'}" 
                         alt="${dish.name}" 
                         class="dish-image"
                         loading="lazy">
                </div>
                
                <div class="dish-info">
                    <h3 class="dish-name">${dish.name}</h3>
                    <p class="dish-description">${dish.description || ''}</p>
                    
                    <div class="dish-footer">
                        <div class="dish-price">${this.formatPrice(dish.price)}</div>
                        <button class="dish-add-btn btn-plus" type="button">
                            <span class="plus-icon">+</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
}

// Экспортируем для глобального использования
window.DishManager = DishManager;