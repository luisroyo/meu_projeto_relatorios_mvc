// date-config.js - Configuração de formato de data para o sistema
// Padroniza todas as datas para formato brasileiro (dd/mm/yyyy)

const DATE_CONFIG = {
    // Locale brasileiro para formatação de datas
    locale: 'pt-BR',
    
    // Formatos de data suportados
    formats: {
        display: 'dd/mm/yyyy',           // Para exibição ao usuário
        input: 'yyyy-mm-dd',             // Para inputs HTML type="date"
        datetime: 'dd/mm/yyyy HH:mm',    // Para data e hora
        time: 'HH:mm',                   // Para apenas hora
        month: 'MMMM yyyy',              // Para mês e ano (Janeiro 2025)
        day: 'dd/MM',                    // Para dia e mês (15/01)
        year: 'yyyy'                     // Para apenas ano
    },
    
    // Configurações de localização
    localeOptions: {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    },
    
    // Nomes dos meses em português
    monthNames: [
        'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ],
    
    // Nomes dos meses abreviados
    monthNamesShort: [
        'Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun',
        'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'
    ],
    
    // Nomes dos dias da semana
    dayNames: [
        'Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira',
        'Quinta-feira', 'Sexta-feira', 'Sábado'
    ],
    
    // Nomes dos dias abreviados
    dayNamesShort: ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
};

// Funções utilitárias para formatação de data
const DateUtils = {
    /**
     * Formata uma data para exibição no formato brasileiro
     * @param {Date|string} date - Data a ser formatada
     * @param {string} format - Formato desejado (opcional)
     * @returns {string} Data formatada
     */
    formatDate(date, format = 'display') {
        if (!date) return '';
        
        const dateObj = typeof date === 'string' ? new Date(date) : date;
        
        if (isNaN(dateObj.getTime())) return '';
        
        switch (format) {
            case 'display':
                return dateObj.toLocaleDateString(DATE_CONFIG.locale);
            case 'datetime':
                return dateObj.toLocaleString(DATE_CONFIG.locale);
            case 'month':
                return dateObj.toLocaleDateString(DATE_CONFIG.locale, { 
                    month: 'long', 
                    year: 'numeric' 
                });
            case 'day':
                return dateObj.toLocaleDateString(DATE_CONFIG.locale, { 
                    day: 'numeric', 
                    month: 'short' 
                });
            case 'year':
                return dateObj.getFullYear().toString();
            default:
                return dateObj.toLocaleDateString(DATE_CONFIG.locale);
        }
    },
    
    /**
     * Converte uma data do formato brasileiro para ISO
     * @param {string} dateStr - Data no formato dd/mm/yyyy
     * @returns {string} Data no formato yyyy-mm-dd
     */
    parseBrazilianDate(dateStr) {
        if (!dateStr) return '';
        
        const parts = dateStr.split('/');
        if (parts.length === 3) {
            const [day, month, year] = parts;
            return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
        }
        
        return dateStr;
    },
    
    /**
     * Converte uma data ISO para formato brasileiro
     * @param {string} isoDate - Data no formato yyyy-mm-dd
     * @returns {string} Data no formato dd/mm/yyyy
     */
    isoToBrazilian(isoDate) {
        if (!isoDate) return '';
        
        const parts = isoDate.split('-');
        if (parts.length === 3) {
            const [year, month, day] = parts;
            return `${day}/${month}/${year}`;
        }
        
        return isoDate;
    },
    
    /**
     * Obtém o nome do mês em português
     * @param {number} month - Número do mês (1-12)
     * @returns {string} Nome do mês
     */
    getMonthName(month) {
        if (month >= 1 && month <= 12) {
            return DATE_CONFIG.monthNames[month - 1];
        }
        return '';
    },
    
    /**
     * Obtém o nome abreviado do mês em português
     * @param {number} month - Número do mês (1-12)
     * @returns {string} Nome abreviado do mês
     */
    getMonthNameShort(month) {
        if (month >= 1 && month <= 12) {
            return DATE_CONFIG.monthNamesShort[month - 1];
        }
        return '';
    },
    
    /**
     * Configura os inputs de data para formato brasileiro
     */
    setupDateInputs() {
        // Configura todos os inputs de data
        const dateInputs = document.querySelectorAll('input[type="date"]');
        
        dateInputs.forEach(input => {
            // Adiciona atributos para melhor UX
            input.setAttribute('data-date-format', 'dd/mm/yyyy');
            input.setAttribute('data-locale', 'pt-BR');
            
            // Adiciona tooltip explicativo
            input.title = 'Use o formato dd/mm/aaaa ou clique no calendário';
            
            // Adiciona classe CSS para estilização
            input.classList.add('date-input-br');
        });
        
        // Configura inputs de datetime-local
        const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
        
        datetimeInputs.forEach(input => {
            input.setAttribute('data-datetime-format', 'dd/mm/aaaa HH:mm');
            input.setAttribute('data-locale', 'pt-BR');
            input.title = 'Use o formato dd/mm/aaaa HH:mm';
            input.classList.add('datetime-input-br');
        });
    },
    
    /**
     * Formata valores de data em tabelas e listas
     */
    formatTableDates() {
        // Procura por elementos que contenham datas ISO
        const dateElements = document.querySelectorAll('[data-date-iso], .date-iso');
        
        dateElements.forEach(element => {
            const isoDate = element.getAttribute('data-date-iso') || element.textContent;
            if (isoDate && this.isValidISODate(isoDate)) {
                element.textContent = this.isoToBrazilian(isoDate);
                element.classList.add('date-formatted');
            }
        });
    },
    
    /**
     * Valida se uma string é uma data ISO válida
     * @param {string} isoDate - Data a ser validada
     * @returns {boolean} True se for válida
     */
    isValidISODate(isoDate) {
        const date = new Date(isoDate);
        return date instanceof Date && !isNaN(date);
    }
};

// Inicialização automática quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    DateUtils.setupDateInputs();
    DateUtils.formatTableDates();
});

// Exporta para uso global
window.DateUtils = DateUtils;
window.DATE_CONFIG = DATE_CONFIG;
