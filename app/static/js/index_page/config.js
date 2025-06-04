// app/static/js/index_page/config.js

export const CONFIG = {
    maxInputLengthFrontend: 10000,
    maxInputLengthServerDisplay: 12000,
    copySuccessMessageDuration: 2000,
    apiEndpoint: '/processar_relatorio',
    selectors: {
        btnProcessar: '#processarRelatorio',
        relatorioBruto: '#relatorioBruto',
        resultadoProcessamento: '#resultadoProcessamento',
        resultadoEmail: '#resultadoEmail',
        colunaRelatorioEmail: '#colunaRelatorioEmail',
        statusProcessamento: '#statusProcessamento',
        statusProcessamentoEmail: '#statusProcessamentoEmail',
        spinnerElement: '#processarSpinner', // Renomeado para clareza, embora o spinner seja agora parte do botão
        btnCopiar: '#copiarResultado',
        btnCopiarEmail: '#copiarResultadoEmail',
        btnLimpar: '#limparCampos',
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
        copied: '<i class="bi bi-check-lg me-1"></i>Copiado!',
        copyFailure: 'Falha ao copiar. Por favor, copie manualmente.',
        emptyReport: 'O relatório bruto não pode estar vazio.',
        reportTooLongFrontend: (max, current) => `Relatório muito longo. Máximo: ${max}, Atual: ${current}.`,
        communicationFailure: 'Falha de comunicação com o servidor.',
        errorPrefix: 'Erro: ',
        unexpectedResponse: 'Resposta inesperada do servidor.'
    },
    initialCopyButtonText: '<i class="bi bi-clipboard me-1"></i>Copiar Padrão',
    initialCopyEmailButtonText: '<i class="bi bi-clipboard-check me-1"></i>Copiar E-mail'
    // Adicione o texto original do botão Processar aqui se ele tiver ícones
    // initialProcessButtonHTML: '<i class="bi bi-magic"></i> Processar Relatório', // Exemplo
};

export const DOMElements = {};
for (const key in CONFIG.selectors) {
    DOMElements[key] = document.querySelector(CONFIG.selectors[key]);
    if (!DOMElements[key] && key !== 'spinnerElement') { // spinnerElement pode não existir mais como um span separado
        // console.warn(`config.js: Elemento DOM para '${key}' (seletor: '${CONFIG.selectors[key]}') NÃO ENCONTRADO.`);
    }
}