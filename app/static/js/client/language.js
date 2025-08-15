/**
 * Модуль для управления языками
 */

class LanguageManager {
    static init() {
        console.log('🌐 Initializing Language Manager');
        
        // Получаем настройки из конфигурации
        this.loadLanguageSettings();
        
        // Создаем кнопки языков
        this.createLanguageButtons();
        
        this.setupEventListeners();
        this.applyLanguage(this.currentLanguage);
        
        console.log('✅ Language Manager initialized');
        console.log('🔍 Language buttons created:', document.querySelectorAll('.lang-btn').length);
        console.log('🔍 Language selector found:', document.getElementById('languageSelector'));
    }
    
    static createLanguageButtons() {
        const languageSelector = document.getElementById('languageSelector');
        console.log('🔍 Creating language buttons, selector found:', languageSelector);
        
        if (!languageSelector) {
            console.error('❌ Language selector not found!');
            return;
        }
        
        // Очищаем существующие кнопки
        languageSelector.innerHTML = '';
        
        console.log('🔍 Supported languages:', this.supportedLanguages);
        
        // Создаем кнопки для каждого доступного языка
        this.supportedLanguages.forEach(lang => {
            const btn = document.createElement('button');
            btn.className = 'lang-btn';
            btn.setAttribute('data-lang', lang);
            
            // Устанавливаем текст кнопки
            const langTexts = {
                'ru': 'РУ',
                'tk': 'TM', 
                'en': 'EN'
            };
            
            btn.textContent = langTexts[lang] || lang.toUpperCase();
            
            // Устанавливаем активное состояние
            if (lang === this.currentLanguage) {
                btn.classList.add('active');
            }
            
            languageSelector.appendChild(btn);
            console.log('🔍 Added language button:', lang, btn.textContent);
        });
        
        console.log('🔍 Total language buttons created:', languageSelector.querySelectorAll('.lang-btn').length);
    }
    
    static loadLanguageSettings() {
        // Получаем настройки из конфигурации
        const config = window.CLIENT_CONFIG || {};
        const settings = config.settings || {};
        
        console.log('🔍 Loading language settings from config:', config);
        console.log('🔍 Settings object:', settings);
        
        // Язык по умолчанию
        this.currentLanguage = localStorage.getItem('language') || 
                              settings.default_language || 'ru';
        
        // Доступные языки
        const availableLanguages = settings.available_languages || 'ru,en,tk';
        this.supportedLanguages = availableLanguages.split(',');
        
        // Фильтруем только доступные языки
        this.supportedLanguages = this.supportedLanguages.filter(lang => 
            ['ru', 'tk', 'en'].includes(lang)
        );
        
        // Если текущий язык не поддерживается, используем первый доступный
        if (!this.supportedLanguages.includes(this.currentLanguage)) {
            this.currentLanguage = this.supportedLanguages[0] || 'ru';
        }
        
        console.log('🌐 Language settings loaded:', {
            currentLanguage: this.currentLanguage,
            supportedLanguages: this.supportedLanguages,
            availableLanguages: availableLanguages
        });
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