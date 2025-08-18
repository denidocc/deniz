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
        this.autoplayDelay = 5000; // 5 секунд по умолчанию
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
            // Получаем настройки из конфигурации
            const config = window.CLIENT_CONFIG || {};
            const settings = config.settings || {};
            
            // Загружаем настройки карусели
            this.autoplayDelay = (settings.carousel_slide_duration || 5) * 1000; // в миллисекундах
            this.transitionSpeed = settings.carousel_transition_speed || 0.5;
            this.maxSlides = settings.carousel_slides_count || 3;
            
            // Загружаем баннеры из API
            await this.loadBannersFromAPI();
            
            console.log('🎠 Carousel settings loaded:', {
                autoplayDelay: this.autoplayDelay,
                transitionSpeed: this.transitionSpeed,
                maxSlides: this.maxSlides
            });
            
        } catch (error) {
            console.error('❌ Error loading carousel settings:', error);
            this.createFakeSlides();
        }
    }

    async loadBannersFromAPI() {
        try {
            console.log('🎠 Loading banners from API...');
            // Загружаем активные баннеры из API
            const response = await fetch('/client/api/banners');
            
            console.log('🎠 API Response status:', response.status);
            
            if (response.ok) {
                const data = await response.json();
                console.log('🎠 API Response data:', data);
                
                if (data.status === 'success' && data.data && data.data.length > 0) {
                    console.log('🎠 Banners found:', data.data.length);
                    // Баннеры уже отфильтрованы на сервере
                    this.renderBanners(data.data);
                    return;
                            } else {
                console.log('🎠 No banners found in response');
                console.log('🎠 Response data:', data);
                this.renderEmptyState();
                return;
            }
        } else {
            console.log('🎠 API response not OK:', response.status);
            this.renderEmptyState();
        }
            
            // Если баннеры не загружены, создаем фейковые слайды
            this.createFakeSlides();
            
        } catch (error) {
            console.error('❌ Error loading banners from API:', error);
            this.createFakeSlides();
        }
    }

    renderBanners(banners) {
        console.log('🎠 Rendering banners:', banners);
        
        // Ограничиваем количество слайдов
        const limitedBanners = banners.slice(0, this.maxSlides);
        console.log('🎠 Limited banners:', limitedBanners);
        
        // Очищаем существующие слайды
        this.carousel.innerHTML = '';
        
        // Создаем структуру карусели с track
        const track = document.createElement('div');
        track.className = 'carousel-track';
        track.id = 'carouselTrack';
        this.track = track;
        
        // Создаем слайды из баннеров
        limitedBanners.forEach((banner, index) => {
            console.log('🎠 Processing banner:', banner);
            const slide = document.createElement('div');
            slide.className = 'carousel-slide';
            slide.style.backgroundImage = `url('${banner.image_url}')`;
            
            // Добавляем контент баннера
            slide.innerHTML = `
                <div class="slide-content">
                    <h2 class="slide-title">${banner.title}</h2>
                    ${banner.description ? `<p class="slide-description">${banner.description}</p>` : ''}
                    ${banner.link_url && banner.link_text ? 
                        `<a href="${banner.link_url}" class="slide-link">${banner.link_text}</a>` : 
                        ''}
                </div>
            `;
            
            track.appendChild(slide);
        });
        
        // Добавляем track в карусель
        this.carousel.appendChild(track);
        
        // Обновляем количество слайдов
        this.slides = Array.from(this.carousel.querySelectorAll('.carousel-slide'));
        this.slideCount = this.slides.length;
        
        // Обновляем ширину слайдов
        this.updateSlideWidth();
        
        // Создаем точки навигации
        this.createDots();
        
        // Показываем первый слайд
        if (this.slideCount > 0) {
            try {
                this.goToSlide(0);
            } catch (error) {
                console.error('🎠 Error showing first slide:', error);
            }
        }
        
        console.log(`🎠 Loaded ${this.slideCount} banners from API`);
    }

    createFakeSlides() {
        // Если баннеры не загружены, показываем пустое состояние
        this.renderEmptyState();
    }

    renderEmptyState() {
        console.log('🎠 Rendering empty state');
        this.carousel.innerHTML = `
            <div class="carousel-empty-state">
                <div class="empty-state-content">
                    <i class="bi bi-images"></i>
                    <h3>Баннеры не найдены</h3>
                    <p>В данный момент нет активных баннеров для отображения</p>
                </div>
            </div>
        `;
        
        this.slides = [];
        this.slideCount = 0;
        
        console.log('🎠 No banners available, showing empty state');
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
        // Проверяем, что track существует
        if (!this.track) {
            console.warn('🎠 Track not initialized, skipping slide navigation');
            return;
        }
        
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