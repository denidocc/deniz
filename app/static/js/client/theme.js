/**
 * Модуль для управления темой (светлая/темная)
 */

class ThemeManager {
    static init() {
        console.log('🌙 Initializing Theme Manager');
        
        this.themeToggle = document.getElementById('themeToggle');
        this.currentTheme = localStorage.getItem('theme') || 'light';
        
        this.setupEventListeners();
        this.applyTheme(this.currentTheme);
        
        console.log('✅ Theme Manager initialized');
    }
    
    static setupEventListeners() {
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }
    
    static toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        localStorage.setItem('theme', this.currentTheme);
    }
    
    static applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        
        if (this.themeToggle) {
            const moonIcon = this.themeToggle.querySelector('.moon');
            const sunIcon = this.themeToggle.querySelector('.sun');
            
            if (theme === 'dark') {
                if (moonIcon) moonIcon.style.display = 'none';
                if (sunIcon) sunIcon.style.display = 'block';
            } else {
                if (moonIcon) moonIcon.style.display = 'block';
                if (sunIcon) sunIcon.style.display = 'none';
            }
        }
    }
}

// Экспортируем для глобального использования
window.ThemeManager = ThemeManager;