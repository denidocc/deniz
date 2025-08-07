/**
 * Управление сменами официанта
 */

class WaiterShift {
    constructor() {
        this.currentShift = null;
        this.shiftTimer = null;
        this.init();
    }

    async init() {
        try {
            await this.loadCurrentShift();
            this.initShiftControls();
            this.startShiftTimer();
            console.log('⏰ Система смен инициализирована');
        } catch (error) {
            console.error('Ошибка инициализации системы смен:', error);
        }
    }

    /**
     * Загрузить информацию о текущей смене
     */
    async loadCurrentShift() {
        try {
            // Проверяем что API готов
            if (!window.WaiterAPI || typeof window.WaiterAPI.getShiftInfo !== 'function') {
                return; // Тихо пропускаем если API не готов
            }
            
            const response = await window.WaiterAPI.getShiftInfo();
            if (response.status === 'success') {
                this.currentShift = response.data;
                this.updateShiftDisplay();
            }
        } catch (error) {
            // Логируем ошибку только если это не проблема с API
            if (window.WaiterAPI && typeof window.WaiterAPI.getShiftInfo === 'function') {
                console.error('Ошибка загрузки информации о смене:', error);
                if (window.waiterNotifications) {
                    waiterNotifications.showError('Не удалось загрузить информацию о смене');
                }
            }
        }
    }

    /**
     * Инициализировать элементы управления сменой
     */
    initShiftControls() {
        const shiftButton = document.getElementById('shift-toggle-btn');
        if (shiftButton) {
            shiftButton.addEventListener('click', () => this.toggleShift());
        }

        const shiftInfo = document.getElementById('shift-info');
        if (shiftInfo) {
            shiftInfo.addEventListener('click', () => this.showShiftDetails());
        }
    }

    /**
     * Обновить отображение информации о смене
     */
    updateShiftDisplay() {
        this.updateShiftButton();
        this.updateShiftInfo();
        this.updateShiftTimer();
    }

    /**
     * Обновить кнопку смены
     */
    updateShiftButton() {
        const shiftButton = document.getElementById('shift-toggle-btn');
        if (!shiftButton) return;

        const isActive = this.currentShift && this.currentShift.status === 'active';
        
        shiftButton.textContent = isActive ? 'Завершить смену' : 'Начать смену';
        shiftButton.className = `btn ${isActive ? 'btn-danger' : 'btn-success'}`;
    }

    /**
     * Обновить информацию о смене
     */
    updateShiftInfo() {
        const shiftInfo = document.getElementById('shift-info');
        if (!shiftInfo) return;

        if (this.currentShift && this.currentShift.status === 'active') {
            const startTime = new Date(this.currentShift.start_time);
            shiftInfo.innerHTML = `
                <div class="shift-status active">
                    <i class="fas fa-clock"></i>
                    Смена активна с ${WaiterUtils.formatTime(startTime)}
                </div>
            `;
        } else {
            shiftInfo.innerHTML = `
                <div class="shift-status inactive">
                    <i class="fas fa-clock"></i>
                    Смена не начата
                </div>
            `;
        }
    }

    /**
     * Запустить таймер смены
     */
    startShiftTimer() {
        if (this.shiftTimer) {
            clearInterval(this.shiftTimer);
        }

        this.shiftTimer = setInterval(() => {
            this.updateShiftTimer();
        }, 1000);
    }

    /**
     * Обновить таймер смены
     */
    updateShiftTimer() {
        const timerElement = document.getElementById('shift-timer');
        if (!timerElement) return;

        if (this.currentShift && this.currentShift.status === 'active') {
            const startTime = new Date(this.currentShift.start_time);
            const now = new Date();
            const duration = Math.floor((now - startTime) / 1000);
            
            const hours = Math.floor(duration / 3600);
            const minutes = Math.floor((duration % 3600) / 60);
            const seconds = duration % 60;
            
            timerElement.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            timerElement.className = 'shift-timer active';
        } else {
            timerElement.textContent = '--:--:--';
            timerElement.className = 'shift-timer inactive';
        }
    }

    /**
     * Переключить смену (начать/завершить)
     */
    async toggleShift() {
        const isActive = this.currentShift && this.currentShift.status === 'active';
        
        if (isActive) {
            await this.endShift();
        } else {
            await this.startShift();
        }
    }

    /**
     * Начать смену
     */
    async startShift() {
        try {
            const confirmed = await WaiterUtils.confirm(
                'Вы действительно хотите начать смену?',
                'Начать смену'
            );
            
            if (!confirmed) return;

            const loader = WaiterUtils.showLoader('Начинаем смену...');
            
            const response = await window.WaiterAPI.startShift();
            WaiterUtils.hideLoader();
            
            if (response.status === 'success') {
                this.currentShift = response.data;
                this.updateShiftDisplay();
                waiterNotifications.showSuccess('Смена успешно начата');
            } else {
                waiterNotifications.showError(response.message || 'Не удалось начать смену');
            }
        } catch (error) {
            WaiterUtils.hideLoader();
            console.error('Ошибка начала смены:', error);
            waiterNotifications.showError('Произошла ошибка при начале смены');
        }
    }

    /**
     * Завершить смену
     */
    async endShift() {
        try {
            const confirmed = await WaiterUtils.confirm(
                'Вы действительно хотите завершить смену?',
                'Завершить смену'
            );
            
            if (!confirmed) return;

            const loader = WaiterUtils.showLoader('Завершаем смену...');
            
            const response = await window.WaiterAPI.endShift();
            WaiterUtils.hideLoader();
            
            if (response.status === 'success') {
                this.currentShift = null;
                this.updateShiftDisplay();
                waiterNotifications.showSuccess('Смена успешно завершена');
                
                // Показываем статистику смены
                this.showShiftSummary(response.data);
            } else {
                waiterNotifications.showError(response.message || 'Не удалось завершить смену');
            }
        } catch (error) {
            WaiterUtils.hideLoader();
            console.error('Ошибка завершения смены:', error);
            waiterNotifications.showError('Произошла ошибка при завершении смены');
        }
    }

    /**
     * Показать детали смены
     */
    async showShiftDetails() {
        if (!this.currentShift || this.currentShift.status !== 'active') {
            waiterNotifications.showWarning('Смена не активна');
            return;
        }

        try {
            const response = await window.WaiterAPI.getShiftInfo();
            if (response.status === 'success') {
                const shift = response.data;
                const startTime = new Date(shift.start_time);
                const now = new Date();
                const duration = Math.floor((now - startTime) / 1000);
                
                const hours = Math.floor(duration / 3600);
                const minutes = Math.floor((duration % 3600) / 60);

                const modal = document.createElement('div');
                modal.style.cssText = `
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 10001;
                `;

                modal.innerHTML = `
                    <div style="
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        max-width: 500px;
                        margin: 20px;
                        max-height: 80vh;
                        overflow-y: auto;
                    ">
                        <h3 style="margin: 0 0 20px; color: #333;">Информация о смене</h3>
                        <div style="margin-bottom: 15px;">
                            <strong>Начало смены:</strong> ${WaiterUtils.formatTime(startTime)}
                        </div>
                        <div style="margin-bottom: 15px;">
                            <strong>Продолжительность:</strong> ${hours}ч ${minutes}мин
                        </div>
                        <div style="margin-bottom: 15px;">
                            <strong>Обслужено столов:</strong> ${shift.tables_served || 0}
                        </div>
                        <div style="margin-bottom: 15px;">
                            <strong>Принято заказов:</strong> ${shift.orders_taken || 0}
                        </div>
                        <div style="margin-bottom: 25px;">
                            <strong>Сумма заказов:</strong> ${WaiterUtils.formatPrice(shift.total_sales || 0)}
                        </div>
                        <button id="close-shift-details" style="
                            padding: 10px 20px;
                            background: #007bff;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            cursor: pointer;
                            width: 100%;
                        ">Закрыть</button>
                    </div>
                `;

                document.body.appendChild(modal);

                modal.querySelector('#close-shift-details').addEventListener('click', () => {
                    modal.remove();
                });

                modal.addEventListener('click', (e) => {
                    if (e.target === modal) {
                        modal.remove();
                    }
                });
            }
        } catch (error) {
            console.error('Ошибка получения деталей смены:', error);
            waiterNotifications.showError('Не удалось загрузить детали смены');
        }
    }

    /**
     * Показать сводку по смене
     */
    showShiftSummary(shiftData) {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10001;
        `;

        const startTime = new Date(shiftData.start_time);
        const endTime = new Date(shiftData.end_time);
        const duration = Math.floor((endTime - startTime) / 1000);
        const hours = Math.floor(duration / 3600);
        const minutes = Math.floor((duration % 3600) / 60);

        modal.innerHTML = `
            <div style="
                background: white;
                padding: 30px;
                border-radius: 10px;
                max-width: 500px;
                margin: 20px;
                text-align: center;
            ">
                <h3 style="margin: 0 0 20px; color: #28a745;">🎉 Смена завершена!</h3>
                <div style="margin-bottom: 15px;">
                    <strong>Продолжительность:</strong> ${hours}ч ${minutes}мин
                </div>
                <div style="margin-bottom: 15px;">
                    <strong>Обслужено столов:</strong> ${shiftData.tables_served || 0}
                </div>
                <div style="margin-bottom: 15px;">
                    <strong>Принято заказов:</strong> ${shiftData.orders_taken || 0}
                </div>
                <div style="margin-bottom: 25px; font-size: 18px;">
                    <strong>Общая сумма:</strong> 
                    <span style="color: #28a745; font-size: 24px;">${WaiterUtils.formatPrice(shiftData.total_sales || 0)}</span>
                </div>
                <button id="close-shift-summary" style="
                    padding: 12px 24px;
                    background: #28a745;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                ">Отлично!</button>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('#close-shift-summary').addEventListener('click', () => {
            modal.remove();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Получить статус смены
     */
    getShiftStatus() {
        return this.currentShift ? this.currentShift.status : 'inactive';
    }

    /**
     * Получить продолжительность активной смены в секундах
     */
    getShiftDuration() {
        if (!this.currentShift || this.currentShift.status !== 'active') {
            return 0;
        }

        const startTime = new Date(this.currentShift.start_time);
        const now = new Date();
        return Math.floor((now - startTime) / 1000);
    }

    /**
     * Проверить, активна ли смена
     */
    isShiftActive() {
        return this.currentShift && this.currentShift.status === 'active';
    }

    /**
     * Уничтожить таймер при выгрузке страницы
     */
    destroy() {
        if (this.shiftTimer) {
            clearInterval(this.shiftTimer);
            this.shiftTimer = null;
        }
    }
}

// Создаем экземпляр только когда DOM готов и WaiterAPI доступен
document.addEventListener('DOMContentLoaded', () => {
    // Ждем пока WaiterAPI станет доступным
    const waitForAPI = () => {
        if (window.WaiterAPI && typeof window.WaiterAPI.getShiftInfo === 'function') {
            window.waiterShift = new WaiterShift();
        } else {
            setTimeout(waitForAPI, 50);
        }
    };
    
    waitForAPI();
});

// Очистка при выгрузке страницы
window.addEventListener('beforeunload', () => {
    if (window.waiterShift) {
        window.waiterShift.destroy();
    }
});