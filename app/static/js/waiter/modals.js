/**
 * Модальные окна для официантского интерфейса
 */

class WaiterModals {
    constructor() {
        this.activeModal = null;
        this.init();
    }

    init() {
        this.initEventListeners();
        console.log('🪟 Система модальных окон инициализирована');
    }

    /**
     * Инициализировать обработчики событий
     */
    initEventListeners() {
        // Закрытие модалов по ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.hide(this.activeModal);
            }
        });

        // Закрытие по клику вне модала
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.hide(e.target.querySelector('.modal'));
            }
        });
    }

    /**
     * Показать модальное окно
     */
    show(modalId, options = {}) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Модал с ID ${modalId} не найден`);
            return;
        }

        // Закрываем предыдущий модал если есть
        if (this.activeModal && this.activeModal !== modal) {
            this.hide(this.activeModal);
        }

        this.activeModal = modal;
        
        // Показываем модал
        modal.style.display = 'flex';
        modal.classList.add('modal-active');
        
        // Блокируем скролл страницы
        document.body.style.overflow = 'hidden';
        
        // Фокус на модале
        setTimeout(() => {
            const firstInput = modal.querySelector('input, select, textarea, button');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);

        // Инициализируем специфичные для модала обработчики
        this.initModalSpecificHandlers(modal, options);
    }

    /**
     * Скрыть модальное окно
     */
    hide(modal) {
        if (!modal) return;

        modal.classList.remove('modal-active');
        
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);

        // Разблокируем скролл страницы
        document.body.style.overflow = '';

        if (this.activeModal === modal) {
            this.activeModal = null;
        }
    }

    /**
     * Инициализировать специфичные для модала обработчики
     */
    initModalSpecificHandlers(modal, options) {
        // Кнопки закрытия
        const closeButtons = modal.querySelectorAll('[data-dismiss="modal"]');
        closeButtons.forEach(btn => {
            btn.addEventListener('click', () => this.hide(modal));
        });

        // Формы в модалах
        const forms = modal.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                this.handleFormSubmit(e, modal, options);
            });
        });
    }

    /**
     * Обработка отправки формы в модале
     */
    async handleFormSubmit(event, modal, options) {
        event.preventDefault();
        
        const form = event.target;
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Отправка...';
            }

            // Вызываем кастомный обработчик если есть
            if (options.onSubmit) {
                await options.onSubmit(data, modal, form);
            }

            // Автоматически закрываем модал если не указано иное
            if (options.autoClose !== false) {
                this.hide(modal);
            }

        } catch (error) {
            console.error('Ошибка отправки формы:', error);
            waiterNotifications.showError('Ошибка при отправке данных');
        } finally {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = submitBtn.getAttribute('data-original-text') || 'Отправить';
            }
        }
    }

    /**
     * Создать модал подтверждения
     */
    async confirm(message, title = 'Подтверждение', options = {}) {
        return new Promise((resolve) => {
            const modalId = 'dynamic-confirm-modal';
            
            // Удаляем существующий модал если есть
            const existingModal = document.getElementById(modalId);
            if (existingModal) {
                existingModal.remove();
            }

            const modal = document.createElement('div');
            modal.id = modalId;
            modal.className = 'modal modal-overlay';
            modal.style.cssText = `
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                justify-content: center;
                align-items: center;
                z-index: 10001;
            `;

            modal.innerHTML = `
                <div class="modal-content" style="
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    max-width: 400px;
                    margin: 20px;
                    text-align: center;
                ">
                    <h3 style="margin: 0 0 15px; color: #333;">${title}</h3>
                    <p style="margin: 0 0 25px; color: #666;">${message}</p>
                    <div style="display: flex; gap: 10px; justify-content: center;">
                        <button type="button" class="btn btn-secondary" data-action="cancel">
                            ${options.cancelText || 'Отмена'}
                        </button>
                        <button type="button" class="btn btn-primary" data-action="confirm">
                            ${options.confirmText || 'Подтвердить'}
                        </button>
                    </div>
                </div>
            `;

            document.body.appendChild(modal);

            modal.querySelector('[data-action="confirm"]').addEventListener('click', () => {
                modal.remove();
                resolve(true);
            });

            modal.querySelector('[data-action="cancel"]').addEventListener('click', () => {
                modal.remove();
                resolve(false);
            });

            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                    resolve(false);
                }
            });

            this.show(modalId);
        });
    }

    /**
     * Создать модал с произвольным содержимым
     */
    createModal(id, title, content, options = {}) {
        const modal = document.createElement('div');
        modal.id = id;
        modal.className = 'modal modal-overlay';
        modal.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            justify-content: center;
            align-items: center;
            z-index: 10000;
        `;

        const size = options.size || 'medium';
        const maxWidth = {
            small: '400px',
            medium: '600px',
            large: '800px',
            xlarge: '1000px'
        }[size] || '600px';

        modal.innerHTML = `
            <div class="modal-content" style="
                background: white;
                border-radius: 10px;
                max-width: ${maxWidth};
                margin: 20px;
                max-height: 90vh;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
            ">
                <div class="modal-header" style="
                    padding: 20px 30px;
                    border-bottom: 1px solid #eee;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <h3 style="margin: 0; color: #333;">${title}</h3>
                    <button type="button" class="btn-close" data-dismiss="modal" style="
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #999;
                        padding: 0;
                        width: 30px;
                        height: 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                    ">&times;</button>
                </div>
                <div class="modal-body" style="
                    padding: 30px;
                    flex: 1;
                ">
                    ${content}
                </div>
                ${options.footer ? `
                <div class="modal-footer" style="
                    padding: 20px 30px;
                    border-top: 1px solid #eee;
                    display: flex;
                    justify-content: flex-end;
                    gap: 10px;
                ">
                    ${options.footer}
                </div>
                ` : ''}
            </div>
        `;

        document.body.appendChild(modal);
        return modal;
    }

    /**
     * Показать модал загрузки
     */
    showLoader(message = 'Загрузка...') {
        const loaderId = 'waiter-loader-modal';
        
        // Удаляем существующий если есть
        const existing = document.getElementById(loaderId);
        if (existing) {
            existing.remove();
        }

        const modal = this.createModal(loaderId, '', `
            <div style="text-align: center; padding: 20px;">
                <div style="
                    width: 50px;
                    height: 50px;
                    border: 5px solid #f3f3f3;
                    border-top: 5px solid #007bff;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                "></div>
                <div style="font-size: 16px; color: #666;">${message}</div>
            </div>
        `, { size: 'small' });

        // Добавляем CSS анимацию если еще не добавлена
        if (!document.getElementById('waiter-modal-styles')) {
            const style = document.createElement('style');
            style.id = 'waiter-modal-styles';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                .modal-overlay {
                    transition: opacity 0.3s ease;
                }
                .modal-active {
                    opacity: 1;
                }
            `;
            document.head.appendChild(style);
        }

        this.show(loaderId);
        return loaderId;
    }

    /**
     * Скрыть модал загрузки
     */
    hideLoader() {
        const loader = document.getElementById('waiter-loader-modal');
        if (loader) {
            this.hide(loader);
            setTimeout(() => loader.remove(), 400);
        }
    }

    /**
     * Получить активный модал
     */
    getActiveModal() {
        return this.activeModal;
    }

    /**
     * Проверить, открыт ли модал
     */
    isModalOpen(modalId = null) {
        if (modalId) {
            const modal = document.getElementById(modalId);
            return modal && modal.classList.contains('modal-active');
        }
        return this.activeModal !== null;
    }
}

// Глобальный экземпляр системы модальных окон
window.waiterModals = new WaiterModals();