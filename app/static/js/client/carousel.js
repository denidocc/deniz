/**
 * Модуль управления каруселью промо-блюд
 */

class CarouselManager {
    static init() {
        console.log('🎠 Initializing Carousel Manager');
        
        this.currentSlide = 0;
        this.slides = [];
        this.isAutoPlaying = true;
        this.autoPlayInterval = null;
        this.settings = {
            autoPlayDelay: 5000, // 5 секунд по умолчанию
            maxSlides: 5,
            enableAutoPlay: true
        };
        
        // Инициализируем элементы
        this.initializeElements();
        
        // Загружаем настройки и слайды
        this.loadSettings();
        this.loadSlides();
        
        console.log('✅ Carousel Manager initialized');
    }

    static initializeElements() {
        this.carousel = document.getElementById('promoCarousel');
        this.track = null;
        this.indicators = null;
        this.prevBtn = null;
        this.nextBtn = null;
        this.progressBar = null;
        
        if (!this.carousel) {
            console.warn('Carousel container not found');
            return;
        }
    }

    static async loadSettings() {
        try {
            const response = await ClientAPI.getCarouselSettings();
            if (response.status === 'success' && response.data) {
                this.settings = {
                    ...this.settings,
                    ...response.data
                };
            }
        } catch (error) {
            console.warn('Could not load carousel settings:', error);
        }
    }

    static async loadSlides() {
        try {
            // Показываем состояние загрузки
            this.showLoading();
            
            const response = await ClientAPI.getCarouselSlides();
            
            if (response.status === 'success' && response.data.slides) {
                this.slides = response.data.slides.filter(slide => slide.is_active);
                
                if (this.slides.length > 0) {
                    this.render();
                    this.setupEventListeners();
                    if (this.settings.enableAutoPlay) {
                        this.startAutoPlay();
                    }
                } else {
                    this.showEmpty();
                }
            } else {
                throw new Error('No slides data received');
            }
            
        } catch (error) {
            console.error('Error loading carousel slides:', error);
            this.showEmpty();
        }
    }

    static showLoading() {
        if (!this.carousel) return;
        
        this.carousel.innerHTML = `
            <div class="carousel-loading">
                Загрузка промо-акций...
            </div>
        `;
    }

    static showEmpty() {
        if (!this.carousel) return;
        
        this.carousel.innerHTML = `
            <div class="carousel-empty">
                Нет активных промо-акций
            </div>
        `;
    }

    static render() {
        if (!this.carousel || this.slides.length === 0) return;
        
        const slidesHtml = this.slides.map((slide, index) => `
            <div class="carousel-slide" data-slide="${index}">
                <div class="slide-content">
                    <div class="slide-text">
                        <h3 class="slide-title">${this.escapeHTML(slide.title)}</h3>
                        <p class="slide-description">${this.escapeHTML(slide.description)}</p>
                        ${slide.price ? `<div class="slide-price">${APIUtils.formatPrice(slide.price)}</div>` : ''}
                        <div class="slide-action">
                            <button class="slide-btn" onclick="CarouselManager.onSlideAction(${slide.menu_item_id})">
                                ${slide.action_text || 'Заказать'}
                            </button>
                        </div>
                    </div>
                    ${slide.image_url ? `
                        <div class="slide-image">
                            <img src="${slide.image_url}" alt="${this.escapeHTML(slide.title)}" loading="lazy">
                        </div>
                    ` : ''}
                    <div class="slide-pattern"></div>
                </div>
            </div>
        `).join('');
        
        const indicatorsHtml = this.slides.map((_, index) => `
            <div class="indicator ${index === 0 ? 'active' : ''}" data-slide="${index}"></div>
        `).join('');
        
        this.carousel.innerHTML = `
            <div class="carousel-container">
                <div class="carousel-track" id="carouselTrack">
                    ${slidesHtml}
                </div>
                
                ${this.slides.length > 1 ? `
                    <button class="carousel-nav carousel-prev" id="carouselPrev">‹</button>
                    <button class="carousel-nav carousel-next" id="carouselNext">›</button>
                    
                    <div class="carousel-indicators" id="carouselIndicators">
                        ${indicatorsHtml}
                    </div>
                    
                    <div class="carousel-progress" id="carouselProgress"></div>
                ` : ''}
            </div>
        `;
        
        // Обновляем ссылки на элементы
        this.track = document.getElementById('carouselTrack');
        this.indicators = document.getElementById('carouselIndicators');
        this.prevBtn = document.getElementById('carouselPrev');
        this.nextBtn = document.getElementById('carouselNext');
        this.progressBar = document.getElementById('carouselProgress');
        
        // Устанавливаем ширину трека
        if (this.track) {
            this.track.style.width = `${this.slides.length * 100}%`;
            this.track.querySelectorAll('.carousel-slide').forEach(slide => {
                slide.style.width = `${100 / this.slides.length}%`;
            });
        }
    }

    static setupEventListeners() {
        // Кнопки навигации
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.goToPrevSlide());
        }
        
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.goToNextSlide());
        }
        
        // Индикаторы
        if (this.indicators) {
            this.indicators.addEventListener('click', (e) => {
                if (e.target.classList.contains('indicator')) {
                    const slideIndex = parseInt(e.target.dataset.slide);
                    this.goToSlide(slideIndex);
                }
            });
        }
        
        // Пауза при наведении
        if (this.carousel) {
            this.carousel.addEventListener('mouseenter', () => this.pauseAutoPlay());
            this.carousel.addEventListener('mouseleave', () => this.resumeAutoPlay());
        }
        
        // Свайпы для мобильных устройств
        this.setupTouchEvents();
    }

    static setupTouchEvents() {
        if (!this.carousel) return;
        
        let startX = 0;
        let currentX = 0;
        let isDragging = false;
        
        this.carousel.addEventListener('touchstart', (e) => {
            startX = e.touches[0].clientX;
            isDragging = true;
            this.pauseAutoPlay();
        });
        
        this.carousel.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            currentX = e.touches[0].clientX;
            e.preventDefault();
        });
        
        this.carousel.addEventListener('touchend', () => {
            if (!isDragging) return;
            
            const deltaX = currentX - startX;
            const threshold = 50;
            
            if (Math.abs(deltaX) > threshold) {
                if (deltaX > 0) {
                    this.goToPrevSlide();
                } else {
                    this.goToNextSlide();
                }
            }
            
            isDragging = false;
            this.resumeAutoPlay();
        });
    }

    static goToSlide(index, direction = 'next') {
        if (!this.track || index < 0 || index >= this.slides.length) return;
        
        this.currentSlide = index;
        
        // Анимация перехода
        const translateX = -(index * (100 / this.slides.length));
        this.track.style.transform = `translateX(${translateX}%)`;
        
        // Обновляем индикаторы
        this.updateIndicators();
        
        // Сбрасываем прогресс-бар
        this.resetProgressBar();
        
        // Логируем просмотр слайда
        this.logSlideView(index);
    }

    static goToNextSlide() {
        const nextIndex = (this.currentSlide + 1) % this.slides.length;
        this.goToSlide(nextIndex, 'next');
    }

    static goToPrevSlide() {
        const prevIndex = this.currentSlide === 0 ? this.slides.length - 1 : this.currentSlide - 1;
        this.goToSlide(prevIndex, 'prev');
    }

    static updateIndicators() {
        if (!this.indicators) return;
        
        this.indicators.querySelectorAll('.indicator').forEach((indicator, index) => {
            indicator.classList.toggle('active', index === this.currentSlide);
        });
    }

    static startAutoPlay() {
        if (!this.settings.enableAutoPlay || this.slides.length <= 1) return;
        
        this.isAutoPlaying = true;
        this.autoPlayInterval = setInterval(() => {
            if (this.isAutoPlaying) {
                this.goToNextSlide();
            }
        }, this.settings.autoPlayDelay);
        
        this.startProgressBar();
    }

    static pauseAutoPlay() {
        this.isAutoPlaying = false;
        if (this.progressBar) {
            this.progressBar.style.animationPlayState = 'paused';
        }
    }

    static resumeAutoPlay() {
        if (this.settings.enableAutoPlay && this.slides.length > 1) {
            this.isAutoPlaying = true;
            if (this.progressBar) {
                this.progressBar.style.animationPlayState = 'running';
            }
        }
    }

    static stopAutoPlay() {
        this.isAutoPlaying = false;
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
        }
    }

    static startProgressBar() {
        if (!this.progressBar) return;
        
        this.progressBar.style.width = '0%';
        this.progressBar.style.transition = `width ${this.settings.autoPlayDelay}ms linear`;
        
        // Запускаем анимацию
        setTimeout(() => {
            if (this.progressBar && this.isAutoPlaying) {
                this.progressBar.style.width = '100%';
            }
        }, 10);
    }

    static resetProgressBar() {
        if (!this.progressBar) return;
        
        this.progressBar.style.transition = 'none';
        this.progressBar.style.width = '0%';
        
        setTimeout(() => {
            if (this.progressBar) {
                this.startProgressBar();
            }
        }, 50);
    }

    static onSlideAction(menuItemId) {
        console.log('Slide action clicked:', menuItemId);
        
        // Добавляем блюдо в корзину
        if (menuItemId && MenuManager.dishes) {
            const dish = MenuManager.dishes.find(d => d.id === menuItemId);
            if (dish) {
                CartManager.addItem(dish);
                Utils.showToast(`${dish.name} добавлено в корзину!`, 'success');
            }
        }
        
        // Логируем клик
        this.logSlideClick(this.currentSlide, menuItemId);
    }

    static logSlideView(slideIndex) {
        if (this.slides[slideIndex]) {
            console.log('Slide viewed:', {
                slideId: this.slides[slideIndex].id,
                slideIndex: slideIndex,
                title: this.slides[slideIndex].title
            });
        }
    }

    static logSlideClick(slideIndex, menuItemId) {
        if (this.slides[slideIndex]) {
            console.log('Slide clicked:', {
                slideId: this.slides[slideIndex].id,
                slideIndex: slideIndex,
                menuItemId: menuItemId,
                title: this.slides[slideIndex].title
            });
        }
    }

    static escapeHTML(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }



    // Обновление слайдов без перезагрузки страницы
    static async refresh() {
        console.log('🔄 Refreshing carousel...');
        this.stopAutoPlay();
        await this.loadSlides();
    }

    // Уничтожение карусели
    static destroy() {
        this.stopAutoPlay();
        if (this.carousel) {
            this.carousel.innerHTML = '';
        }
        console.log('🗑️ Carousel destroyed');
    }
}

// Экспортируем в глобальную область
window.CarouselManager = CarouselManager;