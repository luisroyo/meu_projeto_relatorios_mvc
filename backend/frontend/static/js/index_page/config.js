// app/static/js/index_page/config.js
export const CONFIG = {
    maxInputLengthFrontend: 10000,
    maxInputLengthServerDisplay: 12000, // Conforme definido em seu app.config em conftest.py
    copySuccessMessageDuration: 2000,
    apiEndpoint: '/api/ocorrencias/analyze-report', // Endpoint da API

    // Configurações de data e localização
    dateFormat: 'dd/mm/yyyy',
    locale: 'pt-BR',
    timezone: 'America/Sao_Paulo',
    selectors: {
        btnProcessar: '#submit',
        relatorioBruto: '#relatorio_bruto',
        resultadoProcessamento: '#resultadoProcessamento',
        resultadoEmail: '#resultadoEmail',
        colunaRelatorioEmail: '#colunaRelatorioEmail',
        statusProcessamento: '#statusProcessamento',
        statusProcessamentoEmail: '#statusProcessamentoEmail',
        btnCopiar: '#copiarResultado',
        btnCopiarEmail: '#copiarResultadoEmail',
        btnEnviarWhatsAppResultado: '#enviarWhatsAppResultado',
        btnEnviarWhatsAppEmail: '#enviarWhatsAppEmail',
        btnLimpar: '#limpar-campos',
        charCount: '#charCount',
        formatarParaEmailCheckbox: '#formatarParaEmail',
    },
    cssClasses: {
        textDanger: 'text-danger',
        alert: 'alert',
        alertInfo: 'alert-info',
        alertSuccess: 'alert-success',
        alertWarning: 'alert-warning',
        alertDanger: 'alert-danger'
    },
    messages: {
        processing: 'Processando, por favor aguarde...',
        success: 'Relatório processado com sucesso!',
        copied: '<i class="bi bi-clipboard-check-fill me-1"></i>Copiado!', // Exemplo com ícone
        copyFailure: 'Falha ao copiar. Por favor, copie manualmente.',
        emptyReport: 'O relatório bruto não pode estar vazio.',
        reportTooLongFrontend: (max, current) => `Relatório muito longo. Máximo: ${max}, Atual: ${current}.`,
        communicationFailure: 'Falha de comunicação com o servidor.',
        errorPrefix: 'Erro: ',
        unexpectedResponse: 'Resposta inesperada do servidor.'
    },
    initialProcessButtonHTML: '<i class="bi bi-gear-fill me-1"></i>Processar Relatório',
    // Função utilitária para detectar dispositivos mobile
    isMobile: () => {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    // Configurações de WhatsApp
    whatsapp: {
        mobileUrl: 'whatsapp://send?text=',
        desktopUrl: 'https://wa.me/?text=',
        // Função para detectar se o WhatsApp app está instalado
        isAppInstalled: () => {
            // Para mobile, tentamos detectar se o app está instalado
            if (CONFIG.isMobile()) {
                // No iOS, podemos tentar detectar se o app está instalado
                if (/iPhone|iPad|iPod/i.test(navigator.userAgent)) {
                    // iOS: sempre tentar app primeiro
                    return true;
                } else if (/Android/i.test(navigator.userAgent)) {
                    // Android: tentar app primeiro
                    return true;
                }
            }
            // Para desktop, sempre usar web
            return false;
        }
    }
};

// DOMElements será inicializado dinamicamente quando o DOM estiver pronto
export const DOMElements = {};

// Função para inicializar os elementos DOM
export function initializeDOMElements() {
    for (const key in CONFIG.selectors) {
        DOMElements[key] = document.querySelector(CONFIG.selectors[key]);

        // Log detalhado para debug
        if (DOMElements[key]) {
            console.log(`config.js: Elemento encontrado: ${key} = ${CONFIG.selectors[key]}`, DOMElements[key]);
        } else {
            console.warn(`config.js: Elemento NÃO encontrado: ${key} = ${CONFIG.selectors[key]}`);

            // Tentar encontrar elementos similares
            const similarElements = document.querySelectorAll(`[id*="${key}"]`);
            if (similarElements.length > 0) {
                console.log(`config.js: Elementos similares encontrados para ${key}:`, similarElements);
            }
        }
    }

    // Log para debug
    console.log('config.js: DOMElements inicializados:', Object.keys(DOMElements));

    // Verificar elementos essenciais (apenas os que realmente existem no HTML)
    const essentialElements = ['relatorioBruto', 'btnProcessar', 'resultadoProcessamento'];
    const missingElements = essentialElements.filter(key => !DOMElements[key]);

    if (missingElements.length > 0) {
        console.warn('config.js: Elementos não encontrados:', missingElements);
        console.warn('config.js: Selectors correspondentes:',
            missingElements.map(key => CONFIG.selectors[key]));
    }

    // Verificar especificamente o botão de copiar
    if (DOMElements.btnCopiar) {
        console.log('config.js: Botão copiar encontrado:', DOMElements.btnCopiar);
        console.log('config.js: Botão copiar display:', DOMElements.btnCopiar.style.display);
        console.log('config.js: Botão copiar visível:', DOMElements.btnCopiar.offsetParent !== null);
    } else {
        console.error('config.js: Botão copiar NÃO encontrado!');
        console.error('config.js: Seletor usado:', CONFIG.selectors.btnCopiar);
        console.error('config.js: Elementos com ID similar:', document.querySelectorAll('[id*="copiar"]'));
    }

    return DOMElements;
}