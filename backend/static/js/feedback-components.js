// feedback-components.js - Componentes visuais de feedback

/**
 * Sistema de Feedback Visual Avançado
 * Gerencia toasts, overlays de loading, progress bars e outros componentes de feedback
 */
class FeedbackComponents {
    constructor() {
        this.toasts = [];
        this.loadingOverlays = new Map();
        this.progressBars = new Map();
        this.init();
    }

    /**
     * Inicializa o sistema de feedback
     */
    init() {
        this.createToastContainer();
        this.bindEvents();
    }

    /**
     * Cria container para toasts
     */
    createToastContainer() {
        if (!document.getElementById('toast-container')) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1055;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }
    }

    /**
     * Exibe toast de feedback
     */
    showToast(options = {}) {
        const {
            title = '',
            message = '',
            type = 'info',
            duration = 5000,
            actions = []
        } = options;

        const toast = this.createToast({ title, message, type, actions });
        const container = document.getElementById('toast-container');
        container.appendChild(toast);
        
        this.toasts.push(toast);

        // Animação de entrada
        requestAnimationFrame(() => {
            toast.style.pointerEvents = 'auto';
        });

        // Auto-remove após duração especificada
        if (duration > 0) {
            setTimeout(() => {
                this.removeToast(toast);
            }, duration);
        }

        return toast;
    }

    /**
     * Cria elemento de toast
     */
    createToast({ title, message, type, actions }) {
        const toast = document.createElement('div');
        toast.className = `feedback-toast toast-${type} mb-2`;
        
        const icons = {
            success: 'bi-check-circle-fill',
            error: 'bi-x-circle-fill',
            warning: 'bi-exclamation-triangle-fill',
            info: 'bi-info-circle-fill'
        };

        const colors = {
            success: '#198754',
            error: '#dc3545',
            warning: '#fd7e14',
            info: '#0dcaf0'
        };

        const now = new Date();
        const timeString = now.toLocaleTimeString('pt-BR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        toast.innerHTML = `
            <div class="toast-header">
                <i class="toast-icon bi ${icons[type]}" style="color: ${colors[type]}"></i>
                <strong class="toast-title">${title || this.getDefaultTitle(type)}</strong>
                <small class="toast-time">${timeString}</small>
                <button type="button" class="toast-close" onclick="window.feedbackComponents.removeToast(this.closest('.feedback-toast'))">&times;</button>
            </div>
            <div class="toast-body">
                ${message}
                ${actions.length > 0 ? this.createToastActions(actions) : ''}
            </div>
        `;

        return toast;
    }

    /**
     * Cria ações para toast
     */
    createToastActions(actions) {
        const actionsHtml = actions.map(action => 
            `<button type="button" class="btn btn-sm btn-outline-${action.variant || 'primary'} me-2" onclick="${action.onclick}">${action.text}</button>`
        ).join('');

        return `<div class="mt-2">${actionsHtml}</div>`;
    }

    /**
     * Remove toast
     */
    removeToast(toast) {
        if (toast && toast.parentNode) {
            toast.style.animation = 'toast-slide-out 0.3s ease-in forwards';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
                this.toasts = this.toasts.filter(t => t !== toast);
            }, 300);
        }
    }

    /**
     * Obtém título padrão baseado no tipo
     */
    getDefaultTitle(type) {
        const titles = {
            success: 'Sucesso',
            error: 'Erro',
            warning: 'Atenção',
            info: 'Informação'
        };
        return titles[type] || 'Notificação';
    }

    /**
     * Exibe overlay de loading
     */
    showLoading(target, options = {}) {
        const {
            text = 'Carregando...',
            spinner = 'default',
            backdrop = true
        } = options;

        // Remove loading existente se houver
        this.hideLoading(target);

        const overlay = this.createLoadingOverlay({ text, spinner, backdrop });
        
        if (typeof target === 'string') {
            target = document.querySelector(target);
        }

        if (target) {
            target.style.position = 'relative';
            target.appendChild(overlay);
            this.loadingOverlays.set(target, overlay);
        }

        return overlay;
    }

    /**
     * Cria overlay de loading
     */
    createLoadingOverlay({ text, spinner, backdrop }) {
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay fade-in';
        
        if (!backdrop) {
            overlay.style.background = 'transparent';
        }

        overlay.innerHTML = `
            <div class="loading-content">
                ${this.createSpinner(spinner)}
                <div class="loading-text">${text}</div>
            </div>
        `;

        return overlay;
    }

    /**
     * Cria spinner baseado no tipo
     */
    createSpinner(type) {
        switch (type) {
            case 'dots':
                return `
                    <div class="spinner-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                `;
            case 'pulse':
                return '<div class="spinner-pulse"></div>';
            case 'wave':
                return `
                    <div class="spinner-wave">
                        <span></span>
                        <span></span>
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                `;
            default:
                return '<div class="spinner spinner-lg"></div>';
        }
    }

    /**
     * Remove overlay de loading
     */
    hideLoading(target) {
        if (typeof target === 'string') {
            target = document.querySelector(target);
        }

        const overlay = this.loadingOverlays.get(target);
        if (overlay && overlay.parentNode) {
            overlay.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
                this.loadingOverlays.delete(target);
            }, 300);
        }
    }

    /**
     * Exibe loading fullscreen
     */
    showFullscreenLoading(options = {}) {
        const {
            text = 'Processando...',
            spinner = 'default'
        } = options;

        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay loading-overlay-fullscreen fade-in';
        overlay.id = 'fullscreen-loading';
        
        overlay.innerHTML = `
            <div class="loading-content">
                ${this.createSpinner(spinner)}
                <div class="loading-text">${text}</div>
            </div>
        `;

        document.body.appendChild(overlay);
        return overlay;
    }

    /**
     * Remove loading fullscreen
     */
    hideFullscreenLoading() {
        const overlay = document.getElementById('fullscreen-loading');
        if (overlay) {
            overlay.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
            }, 300);
        }
    }

    /**
     * Cria progress bar
     */
    createProgressBar(container, options = {}) {
        const {
            title = 'Progresso',
            value = 0,
            max = 100,
            showPercentage = true,
            showSteps = false,
            steps = []
        } = options;

        if (typeof container === 'string') {
            container = document.querySelector(container);
        }

        const progressContainer = document.createElement('div');
        progressContainer.className = 'progress-container';
        
        progressContainer.innerHTML = `
            <div class="progress-header">
                <div class="progress-title">${title}</div>
                ${showPercentage ? '<div class="progress-percentage">0%</div>' : ''}
            </div>
            <div class="progress-bar-custom">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
            ${showSteps ? this.createProgressSteps(steps) : ''}
        `;

        container.appendChild(progressContainer);
        
        const progressId = 'progress-' + Date.now();
        this.progressBars.set(progressId, {
            container: progressContainer,
            fill: progressContainer.querySelector('.progress-fill'),
            percentage: progressContainer.querySelector('.progress-percentage'),
            steps: progressContainer.querySelectorAll('.step-circle'),
            max
        });

        return progressId;
    }

    /**
     * Cria steps para progress bar
     */
    createProgressSteps(steps) {
        const stepsHtml = steps.map((step, index) => `
            <div class="progress-step">
                <div class="step-circle" data-step="${index + 1}">${index + 1}</div>
                <div class="step-label">${step}</div>
            </div>
        `).join('');

        return `<div class="progress-steps">${stepsHtml}</div>`;
    }

    /**
     * Atualiza progress bar
     */
    updateProgress(progressId, value, options = {}) {
        const progress = this.progressBars.get(progressId);
        if (!progress) return;

        const { text = '', currentStep = null } = options;
        const percentage = Math.min(100, Math.max(0, (value / progress.max) * 100));

        // Atualiza barra
        progress.fill.style.width = `${percentage}%`;
        
        // Atualiza porcentagem
        if (progress.percentage) {
            progress.percentage.textContent = `${Math.round(percentage)}%`;
        }

        // Atualiza texto se fornecido
        if (text) {
            const titleElement = progress.container.querySelector('.progress-title');
            if (titleElement) {
                titleElement.textContent = text;
            }
        }

        // Atualiza steps se fornecido
        if (currentStep !== null && progress.steps.length > 0) {
            progress.steps.forEach((step, index) => {
                step.classList.remove('active', 'completed');
                if (index < currentStep - 1) {
                    step.classList.add('completed');
                } else if (index === currentStep - 1) {
                    step.classList.add('active');
                }
            });
        }
    }

    /**
     * Remove progress bar
     */
    removeProgress(progressId) {
        const progress = this.progressBars.get(progressId);
        if (progress && progress.container.parentNode) {
            progress.container.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => {
                if (progress.container.parentNode) {
                    progress.container.parentNode.removeChild(progress.container);
                }
                this.progressBars.delete(progressId);
            }, 300);
        }
    }

    /**
     * Cria badge de status
     */
    createStatusBadge(text, type = 'info', showPulse = false) {
        const badge = document.createElement('span');
        badge.className = `status-badge ${type}`;
        
        if (showPulse) {
            badge.innerHTML = `
                <span class="pulse-indicator ${type}"></span>
                ${text}
            `;
        } else {
            badge.textContent = text;
        }

        return badge;
    }

    /**
     * Bind eventos globais
     */
    bindEvents() {
        // Adiciona CSS para animação de saída
        if (!document.getElementById('feedback-animations')) {
            const style = document.createElement('style');
            style.id = 'feedback-animations';
            style.textContent = `
                @keyframes toast-slide-out {
                    to { transform: translateX(100%); opacity: 0; }
                }
                @keyframes fadeOut {
                    to { opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }

        // Remove toasts ao clicar fora
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.feedback-toast')) {
                // Não faz nada - toasts devem ser removidos explicitamente
            }
        });
    }

    /**
     * Métodos de conveniência
     */
    success(message, title = null, duration = 5000) {
        return this.showToast({
            title: title || 'Sucesso',
            message,
            type: 'success',
            duration
        });
    }

    error(message, title = null, duration = 8000) {
        return this.showToast({
            title: title || 'Erro',
            message,
            type: 'error',
            duration
        });
    }

    warning(message, title = null, duration = 6000) {
        return this.showToast({
            title: title || 'Atenção',
            message,
            type: 'warning',
            duration
        });
    }

    info(message, title = null, duration = 5000) {
        return this.showToast({
            title: title || 'Informação',
            message,
            type: 'info',
            duration
        });
    }
}

// Inicializa sistema quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.feedbackComponents = new FeedbackComponents();
});

// Exporta para uso global
window.FeedbackComponents = FeedbackComponents;
