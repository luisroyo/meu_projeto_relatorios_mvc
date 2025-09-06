// help-system.js - Sistema de ajuda e feedback visual

/**
 * Sistema de Ajuda e Feedback Visual
 * Gerencia tooltips, validações, loading states e mensagens de feedback
 */
class HelpSystem {
    constructor() {
        this.init();
    }

    /**
     * Inicializa o sistema de ajuda
     */
    init() {
        this.initTooltips();
        this.initFormValidation();
        this.initLoadingStates();
        this.initCharacterCounters();
        this.initConfirmationModals();
        this.bindEvents();
    }

    /**
     * Inicializa tooltips do Bootstrap
     */
    initTooltips() {
        // Inicializa todos os tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl, {
                html: true,
                delay: { show: 300, hide: 100 }
            });
        });
    }

    /**
     * Inicializa validação de formulários em tempo real
     */
    initFormValidation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            
            inputs.forEach(input => {
                // Validação em tempo real
                input.addEventListener('blur', () => this.validateField(input));
                input.addEventListener('input', () => this.clearFieldErrors(input));
            });
        });
    }

    /**
     * Valida um campo específico
     */
    validateField(field) {
        const value = field.value.trim();
        const isRequired = field.hasAttribute('required');
        const fieldWrapper = field.closest('.form-field-wrapper') || field.parentElement;
        
        // Remove classes de validação existentes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Validação básica
        if (isRequired && !value) {
            this.showFieldError(field, 'Este campo é obrigatório');
            return false;
        }
        
        // Validações específicas por tipo
        switch (field.type) {
            case 'email':
                if (value && !this.isValidEmail(value)) {
                    this.showFieldError(field, 'Digite um e-mail válido');
                    return false;
                }
                break;
                
            case 'date':
                if (value && !this.isValidDate(value)) {
                    this.showFieldError(field, 'Digite uma data válida');
                    return false;
                }
                break;
                
            case 'tel':
                if (value && !this.isValidPhone(value)) {
                    this.showFieldError(field, 'Digite um telefone válido');
                    return false;
                }
                break;
        }
        
        // Campo válido
        if (value) {
            field.classList.add('is-valid');
            this.clearFieldErrors(field);
            return true;
        }
        
        return true;
    }

    /**
     * Exibe erro em um campo específico
     */
    showFieldError(field, message) {
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        
        const fieldWrapper = field.closest('.form-field-wrapper') || field.parentElement;
        let feedback = fieldWrapper.querySelector('.invalid-feedback');
        
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            fieldWrapper.appendChild(feedback);
        }
        
        feedback.innerHTML = `<i class="bi bi-exclamation-triangle me-1"></i>${message}`;
    }

    /**
     * Remove erros de um campo específico
     */
    clearFieldErrors(field) {
        field.classList.remove('is-invalid');
        
        const fieldWrapper = field.closest('.form-field-wrapper') || field.parentElement;
        const feedback = fieldWrapper.querySelector('.invalid-feedback');
        
        if (feedback && !feedback.classList.contains('d-block')) {
            feedback.remove();
        }
    }

    /**
     * Inicializa estados de loading para botões e formulários
     */
    initLoadingStates() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn) {
                    this.setButtonLoading(submitBtn, true);
                }
            });
        });
    }

    /**
     * Define estado de loading de um botão
     */
    setButtonLoading(button, isLoading) {
        console.log('setButtonLoading:', isLoading ? 'Iniciando loading' : 'Finalizando loading', button);
        
        if (isLoading) {
            // Evita ativar loading se já estiver ativo
            if (button.classList.contains('btn-loading')) {
                console.log('setButtonLoading: Loading já ativo, ignorando');
                return;
            }
            
            button.classList.add('btn-loading');
            button.disabled = true;
            
            // Salva o HTML original se ainda não foi salvo
            if (!button.dataset.originalHTML) {
                button.dataset.originalHTML = button.innerHTML;
                console.log('setButtonLoading: HTML original salvo');
            }
            
            // Substitui o conteúdo por um spinner
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processando...';
            console.log('setButtonLoading: Loading ativado');
        } else {
            // Evita desativar loading se já estiver desativo
            if (!button.classList.contains('btn-loading')) {
                console.log('setButtonLoading: Loading já desativo, ignorando');
                return;
            }
            
            button.classList.remove('btn-loading');
            button.disabled = false;
            
            // Restaura o HTML original
            if (button.dataset.originalHTML) {
                button.innerHTML = button.dataset.originalHTML;
                console.log('setButtonLoading: HTML original restaurado');
            } else {
                // Fallback: restaura texto padrão
                button.innerHTML = '<i class="bi bi-save-fill me-1"></i>Registrar Ocorrência';
                console.log('setButtonLoading: Fallback - texto padrão restaurado');
            }
        }
        
        console.log('setButtonLoading: Estado final do botão:', {
            disabled: button.disabled,
            innerHTML: button.innerHTML.substring(0, 50) + '...',
            hasOriginalHTML: !!button.dataset.originalHTML
        });
    }

    /**
     * Inicializa contadores de caracteres
     */
    initCharacterCounters() {
        const textareas = document.querySelectorAll('textarea[data-max-chars]');
        
        textareas.forEach(textarea => {
            const maxChars = parseInt(textarea.dataset.maxChars);
            this.setupCharacterCounter(textarea, maxChars);
        });
    }

    /**
     * Configura contador de caracteres para um textarea
     */
    setupCharacterCounter(textarea, maxChars) {
        const wrapper = textarea.closest('.form-field-wrapper') || textarea.parentElement;
        let counter = wrapper.querySelector('.char-counter');
        
        if (!counter) {
            counter = document.createElement('small');
            counter.className = 'char-counter form-text text-muted';
            counter.innerHTML = `Caracteres: <span class="char-count">0</span> / ${maxChars}`;
            textarea.parentElement.appendChild(counter);
        }
        
        const charCountSpan = counter.querySelector('.char-count');
        
        const updateCounter = () => {
            const count = textarea.value.length;
            charCountSpan.textContent = count;
            
            // Atualiza cores baseado no limite
            counter.classList.remove('text-muted', 'text-warning', 'text-danger');
            
            if (count > maxChars) {
                counter.classList.add('text-danger');
            } else if (count > maxChars * 0.8) {
                counter.classList.add('text-warning');
            } else {
                counter.classList.add('text-muted');
            }
        };
        
        textarea.addEventListener('input', updateCounter);
        updateCounter();
    }

    /**
     * Inicializa modais de confirmação
     */
    initConfirmationModals() {
        const dangerButtons = document.querySelectorAll('[data-confirm]');
        
        dangerButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                this.showConfirmationModal(
                    button.dataset.confirm || 'Tem certeza que deseja continuar?',
                    () => {
                        // Executa ação confirmada
                        if (button.href) {
                            window.location.href = button.href;
                        } else if (button.form) {
                            button.form.submit();
                        }
                    }
                );
            });
        });
    }

    /**
     * Exibe modal de confirmação
     */
    showConfirmationModal(message, onConfirm, options = {}) {
        const modal = this.createConfirmationModal(message, onConfirm, options);
        document.body.appendChild(modal);
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Remove modal do DOM após fechar
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }

    /**
     * Cria modal de confirmação
     */
    createConfirmationModal(message, onConfirm, options = {}) {
        const {
            title = 'Confirmação',
            confirmText = 'Confirmar',
            cancelText = 'Cancelar',
            type = 'warning'
        } = options;
        
        const modal = document.createElement('div');
        modal.className = 'modal fade confirmation-modal';
        modal.tabIndex = -1;
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="bi bi-exclamation-triangle"></i>
                            ${title}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-0">${message}</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                            ${cancelText}
                        </button>
                        <button type="button" class="btn btn-confirm-danger" id="confirmAction">
                            ${confirmText}
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Bind confirm action
        modal.querySelector('#confirmAction').addEventListener('click', () => {
            onConfirm();
            bootstrap.Modal.getInstance(modal).hide();
        });
        
        return modal;
    }

    /**
     * Exibe mensagem de feedback
     */
    showFeedback(message, type = 'info', duration = 5000) {
        const feedback = this.createFeedbackMessage(message, type);
        
        // Adiciona ao topo da página
        const container = document.querySelector('.container, .container-fluid, main, body');
        if (container.firstChild) {
            container.insertBefore(feedback, container.firstChild);
        } else {
            container.appendChild(feedback);
        }
        
        // Remove automaticamente após duração especificada
        if (duration > 0) {
            setTimeout(() => {
                feedback.remove();
            }, duration);
        }
        
        return feedback;
    }

    /**
     * Cria elemento de mensagem de feedback
     */
    createFeedbackMessage(message, type) {
        const feedback = document.createElement('div');
        feedback.className = `feedback-message ${type} fade-in`;
        
        const icons = {
            success: 'bi bi-check-circle-fill',
            error: 'bi bi-x-circle-fill',
            warning: 'bi bi-exclamation-triangle-fill',
            info: 'bi bi-info-circle-fill'
        };
        
        feedback.innerHTML = `
            <i class="${icons[type] || icons.info}"></i>
            <span>${message}</span>
            <button type="button" class="btn-close btn-close-sm ms-auto" onclick="this.parentElement.remove()"></button>
        `;
        
        return feedback;
    }

    /**
     * Bind eventos globais
     */
    bindEvents() {
        // Escape para fechar modais
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModals = document.querySelectorAll('.modal.show');
                openModals.forEach(modal => {
                    bootstrap.Modal.getInstance(modal)?.hide();
                });
            }
        });
        
        // Auto-focus no primeiro campo com erro
        const firstError = document.querySelector('.is-invalid');
        if (firstError) {
            firstError.focus();
        }
    }

    /**
     * Utilitários de validação
     */
    isValidEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    isValidDate(dateString) {
        const date = new Date(dateString);
        return date instanceof Date && !isNaN(date);
    }

    isValidPhone(phone) {
        const re = /^[\+]?[1-9][\d]{0,15}$/;
        return re.test(phone.replace(/[\s\(\)\-]/g, ''));
    }
}

// Inicializa sistema quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.helpSystem = new HelpSystem();
});

// Exporta para uso global
window.HelpSystem = HelpSystem;

// Cria instância global para métodos estáticos
window.HelpSystemInstance = new HelpSystem();