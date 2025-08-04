/**
 * Touch-карусель с поддержкой свайпов и перетаскивания
 */
class CarouselManager {
    constructor() {

        
        this.carousel = null;
        this.track = null;
        this.dots = null;
        this.slides = [];
        this.currentSlide = 0;
        this.slideCount = 0;
        
        // Touch/Mouse состояние
        this.isDragging = false;
        this.startX = 0;
        this.currentX = 0;
        this.initialTranslate = 0;
        this.translateX = 0;
        this.animationId = null;
        
        // Автопрокрутка
        this.autoplayInterval = null;
        this.autoplayDelay = 5000; // 5 секунд
        this.isPaused = false;
        
        // Настройки
        this.swipeThreshold = 50; // Минимальное расстояние для свайпа
        this.slideWidth = 0;
        
        this.init();
    }

    static init() {
        if (!window.carouselManagerInstance) {
            window.carouselManagerInstance = new CarouselManager();
        }
        return window.carouselManagerInstance;
    }

    async init() {
        try {
            this.setupElements();
            await this.loadSettings();
            this.setupEventListeners();
            this.startAutoplay();

        } catch (error) {
            console.error('❌ Carousel initialization failed:', error);
        }
    }

    setupElements() {
        this.carousel = document.getElementById('promoCarousel');
        this.dotsContainer = document.getElementById('carouselDots');
        
        if (!this.carousel || !this.dotsContainer) {
            throw new Error('Carousel elements not found');
        }
    }

    async loadSettings() {
        try {
            if (!window.ClientAPI || typeof window.ClientAPI.getCarouselSettings !== 'function') {
                this.createFakeSlides();
                return;
            }
            
            const response = await window.ClientAPI.getCarouselSettings();
            
            if (response.status === 'success' && response.data && response.data.slides) {
                this.renderSlides(response.data.slides);
            } else {
                this.createFakeSlides();
            }
            
        } catch (error) {
            console.error('❌ Error loading carousel settings:', error);
            this.createFakeSlides();
        }
    }

    createFakeSlides() {
        const fakeSlides = [
            {
                id: 1,
                title: 'РЫБНЫЙ МИКС ДНЯ',
                description: 'Ассорти из лучших сортов рыбы с авторским соусом и свежими овощами',
                price: 1250,
                image_url: '/static/assets/images/fish.png',
                is_active: true
            },
            {
                id: 2,
                title: 'КОРОЛЕВСКИЕ КРЕВЕТКИ',
                description: 'Тигровые креветки на гриле с ароматными травами и лимонным маслом',
                price: 1850,
                image_url: '/static/assets/images/fish.png',
                is_active: true
            },
            {
                id: 3,
                title: 'МРАМОРНАЯ ГОВЯДИНА',
                description: 'Стейк Рибай из отборной мраморной говядины с трюфельным соусом',
                price: 2900,
                image_url: '/static/assets/images/fish.png',
                is_active: true
            },
            {
                id: 4,
                title: 'ЛОБСТЕР С ПАСТОЙ',
                description: 'Домашняя паста с мясом омара в сливочно-коньячном соусе',
                price: 2150,
                image_url: '/static/assets/images/fish.png',
                is_active: true
            }
        ];
        
        this.renderSlides(fakeSlides);
    }

    renderSlides(slides) {
        this.slides = slides.filter(slide => slide.is_active);
        this.slideCount = this.slides.length;
        
        if (this.slideCount === 0) {
            this.renderEmptyState();
            return;
        }
        
        this.createCarouselHTML();
        this.createDots();
        this.updateSlideWidth();
        this.goToSlide(0);
    }

    createCarouselHTML() {
        const trackHTML = `
            <div class="carousel-track" id="carouselTrack">
                ${this.slides.map((slide, index) => `
                    <div class="carousel-slide ${index === 0 ? 'active' : ''}" data-slide="${index}">
                        <div class="slide-content">
                            <div class="slide-text">
                                <div class="slide-title">${this.escapeHTML(slide.title)}</div>
                                <div class="slide-description">${this.escapeHTML(slide.description)}</div>
                                <div class="slide-price">${slide.price} ТМТ</div>
                            </div>
                            <div class="slide-image">
                                <img src="${slide.image_url}" alt="${this.escapeHTML(slide.title)}" loading="lazy">
                            </div>
                        </div>
                        <div class="slide-pattern"></div>
                    </div>
                `).join('')}
            </div>
        `;
        
        this.carousel.innerHTML = trackHTML;
        
        this.track = document.getElementById('carouselTrack');
        
        // Установка ширины трека
        this.track.style.width = `${this.slideCount * 100}%`;
        
        // Установка ширины каждого слайда
        const slideElements = this.track.querySelectorAll('.carousel-slide');
        slideElements.forEach(slide => {
            slide.style.width = `${100 / this.slideCount}%`;
        });
    }

    createDots() {
        const dotsHTML = this.slides.map((_, index) => 
            `<div class="carousel-dot ${index === 0 ? 'active' : ''}" data-slide="${index}"></div>`
        ).join('');
        
        this.dotsContainer.innerHTML = dotsHTML;
        this.dots = this.dotsContainer.querySelectorAll('.carousel-dot');
    }

    updateSlideWidth() {
        this.slideWidth = this.carousel.offsetWidth;
    }

    setupEventListeners() {
        // Изменение размера окна
        window.addEventListener('resize', () => {
            this.updateSlideWidth();
            this.goToSlide(this.currentSlide, false);
        });
        
        // Touch события
        this.carousel.addEventListener('touchstart', this.onTouchStart.bind(this), { passive: false });
        this.carousel.addEventListener('touchmove', this.onTouchMove.bind(this), { passive: false });
        this.carousel.addEventListener('touchend', this.onTouchEnd.bind(this));
        
        // Mouse события для desktop
        this.carousel.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.carousel.addEventListener('mousemove', this.onMouseMove.bind(this));
        this.carousel.addEventListener('mouseup', this.onMouseUp.bind(this));
        this.carousel.addEventListener('mouseleave', this.onMouseUp.bind(this));
        
        // Предотвращение выделения текста
        this.carousel.addEventListener('selectstart', e => e.preventDefault());
        this.carousel.addEventListener('dragstart', e => e.preventDefault());
        
        // Клики по точкам
        this.dotsContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('carousel-dot')) {
                const slideIndex = parseInt(e.target.dataset.slide);
                this.goToSlide(slideIndex);
            }
        });
        
        // Пауза на hover/focus
        this.carousel.addEventListener('mouseenter', () => this.pauseAutoplay());
        this.carousel.addEventListener('mouseleave', () => this.resumeAutoplay());
        this.carousel.addEventListener('focus', () => this.pauseAutoplay());
        this.carousel.addEventListener('blur', () => this.resumeAutoplay());
        
        // Клавиатурная навигация
        document.addEventListener('keydown', (e) => {
            if (e.target.closest('.promo-carousel')) {
                switch (e.key) {
                    case 'ArrowLeft':
                        e.preventDefault();
                        this.previousSlide();
                        break;
                    case 'ArrowRight':
                        e.preventDefault();
                        this.nextSlide();
                        break;
                }
            }
        });
    }

    // Touch события
    onTouchStart(e) {
        this.startDrag(e.touches[0].clientX);
        this.pauseAutoplay();
    }

    onTouchMove(e) {
        if (!this.isDragging) return;
        e.preventDefault();
        this.onDragMove(e.touches[0].clientX);
    }

    onTouchEnd(e) {
        this.endDrag();
        this.resumeAutoplay();
    }

    // Mouse события
    onMouseDown(e) {
        e.preventDefault();
        this.startDrag(e.clientX);
        this.pauseAutoplay();
    }

    onMouseMove(e) {
        if (!this.isDragging) return;
        e.preventDefault();
        this.onDragMove(e.clientX);
    }

    onMouseUp() {
        this.endDrag();
        this.resumeAutoplay();
    }

    // Общая логика перетаскивания
    startDrag(clientX) {
        this.isDragging = true;
        this.startX = clientX;
        this.initialTranslate = this.translateX;
        this.track.classList.add('dragging');
        
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
    }

    onDragMove(clientX) {
        if (!this.isDragging) return;
        
        this.currentX = clientX;
        const deltaX = this.currentX - this.startX;
        this.translateX = this.initialTranslate + deltaX;
        
        // Для бесконечной прокрутки не нужны жесткие ограничения
        
        this.animationId = requestAnimationFrame(() => {
            this.track.style.transform = `translateX(${this.translateX}px)`;
        });
    }

    endDrag() {
        if (!this.isDragging) return;
        
        this.isDragging = false;
        this.track.classList.remove('dragging');
        
        const deltaX = this.currentX - this.startX;
        const slideIndex = Math.round(-this.translateX / this.slideWidth);
        
        // Определяем направление свайпа
        if (Math.abs(deltaX) > this.swipeThreshold) {
            if (deltaX > 0) {
                this.goToSlide(this.currentSlide - 1);
            } else if (deltaX < 0) {
                this.goToSlide(this.currentSlide + 1);
            } else {
                this.goToSlide(this.currentSlide);
            }
        } else {
            // Возвращаемся к ближайшему слайду
            this.goToSlide(slideIndex);
        }
    }

    goToSlide(index, animate = true) {
        // Нормализуем индекс для бесконечной прокрутки
        if (index >= this.slideCount) {
            index = 0;
        } else if (index < 0) {
            index = this.slideCount - 1;
        }
        
        this.currentSlide = index;
        this.translateX = -index * this.slideWidth;
        
        if (animate) {
            this.track.style.transition = 'transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        } else {
            this.track.style.transition = 'none';
        }
        
        this.track.style.transform = `translateX(${this.translateX}px)`;
        
        // Обновляем активные состояния
        this.updateActiveStates();
        
        // Сбрасываем переход после анимации
        if (animate) {
            setTimeout(() => {
                this.track.style.transition = '';
            }, 300);
        }
    }

    updateActiveStates() {
        // Обновляем слайды
        const slideElements = this.track.querySelectorAll('.carousel-slide');
        slideElements.forEach((slide, index) => {
            slide.classList.toggle('active', index === this.currentSlide);
        });
        
        // Обновляем точки
        this.dots.forEach((dot, index) => {
            dot.classList.toggle('active', index === this.currentSlide);
        });
    }

    nextSlide() {
        const nextIndex = (this.currentSlide + 1) % this.slideCount;
        this.goToSlide(nextIndex);
    }

    previousSlide() {
        const prevIndex = (this.currentSlide - 1 + this.slideCount) % this.slideCount;
        this.goToSlide(prevIndex);
    }

    // Автопрокрутка
    startAutoplay() {
        if (this.slideCount <= 1) return;
        
        this.autoplayInterval = setInterval(() => {
            if (!this.isPaused) {
                this.nextSlide();
            }
        }, this.autoplayDelay);
        

    }

    pauseAutoplay() {
        this.isPaused = true;
        this.carousel.classList.add('paused');
    }

    resumeAutoplay() {
        this.isPaused = false;
        this.carousel.classList.remove('paused');

    }

    stopAutoplay() {
        if (this.autoplayInterval) {
            clearInterval(this.autoplayInterval);
            this.autoplayInterval = null;
        }
    }

    renderEmptyState() {
        this.carousel.innerHTML = `
            <div class="carousel-empty">
                <p>Промо-слайды не настроены</p>
            </div>
        `;
        this.dotsContainer.innerHTML = '';
    }

    escapeHTML(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Публичные методы для внешнего управления
    destroy() {
        this.stopAutoplay();
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        // Удаляем обработчики событий
        window.removeEventListener('resize', this.updateSlideWidth);
        
        console.log('🎠 Carousel destroyed');
    }
}

// Глобальная инициализация
window.CarouselManager = CarouselManager;