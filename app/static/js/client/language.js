/**
 * Модуль для управления языками
 */

class LanguageManager {
    static init() {
        console.log('🌐 Initializing Language Manager');
        
        this.currentLanguage = localStorage.getItem('language') || 'ru';
        this.supportedLanguages = ['ru', 'tk', 'en'];
        
        this.setupEventListeners();
        this.applyLanguage(this.currentLanguage);
        
        console.log('✅ Language Manager initialized');
    }
    
    static setupEventListeners() {
        const langButtons = document.querySelectorAll('.lang-btn');
        
        langButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const lang = btn.getAttribute('data-lang');
                if (this.supportedLanguages.includes(lang)) {
                    this.setLanguage(lang);
                }
            });
        });
    }
    
    static setLanguage(lang) {
        if (this.currentLanguage === lang) return;
        
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        
        this.applyLanguage(lang);
        this.updateActiveButton(lang);
        
        // Перезагрузить меню с новым языком
        if (window.MenuManager) {
            window.MenuManager.changeLanguage(lang);
        }
    }
    
    static applyLanguage(lang) {
        // Обновить URL параметр
        const url = new URL(window.location);
        url.searchParams.set('lang', lang);
        window.history.replaceState({}, '', url);
        
        // Обновить атрибут языка
        document.documentElement.setAttribute('lang', lang);
    }
    
    static updateActiveButton(lang) {
        const langButtons = document.querySelectorAll('.lang-btn');
        
        langButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-lang') === lang) {
                btn.classList.add('active');
            }
        });
    }
    
    static getCurrentLanguage() {
        return this.currentLanguage;
    }
}

// Экспортируем для глобального использования
window.LanguageManager = LanguageManager;