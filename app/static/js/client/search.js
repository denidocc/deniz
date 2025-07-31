/**
 * Модуль для поиска по меню
 */

class SearchManager {
    static init() {
        console.log('🔍 Initializing Search Manager');
        
        this.searchInput = document.getElementById('dishSearch');
        this.searchTimeout = null;
        this.searchDelay = 300; // ms
        
        this.setupEventListeners();
        
        console.log('✅ Search Manager initialized');
    }
    
    static setupEventListeners() {
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });
            
            this.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.performSearch(e.target.value);
                }
            });
        }
        
        // Кнопка поиска
        const searchBtn = document.querySelector('.search-btn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                if (this.searchInput) {
                    this.performSearch(this.searchInput.value);
                }
            });
        }
    }
    
    static handleSearchInput(value) {
        // Очищаем предыдущий таймаут
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Устанавливаем новый таймаут для поиска с задержкой
        this.searchTimeout = setTimeout(() => {
            this.performSearch(value);
        }, this.searchDelay);
    }
    
    static performSearch(searchTerm) {
        searchTerm = searchTerm.trim();
        
        console.log('🔍 Performing search:', searchTerm);
        
        // Обновить меню с поисковым запросом
        if (window.MenuManager) {
            window.MenuManager.search(searchTerm);
        }
    }
    
    static clearSearch() {
        if (this.searchInput) {
            this.searchInput.value = '';
            this.performSearch('');
        }
    }
}

// Экспортируем для глобального использования
window.SearchManager = SearchManager;