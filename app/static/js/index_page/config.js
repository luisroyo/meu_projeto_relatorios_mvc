// app/static/js/index_page/config.js
// (Conteúdo como fornecido na resposta anterior, já está correto)
// Exemplo relevante:
// initialProcessButtonHTML: '<i class="bi bi-gear-fill me-1"></i>Processar Relatório',
// initialCopyButtonHTML: '<i class="bi bi-clipboard-data me-1"></i>Copiar Padrão',
// ... etc.
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
        copied: '<i class="bi bi-clipboard-check-fill me-1"></i>Copiado!',
        copyFailure: 'Falha ao copiar. Por favor, copie manualmente.',
        emptyReport: 'O relatório bruto não pode estar vazio.',
        reportTooLongFrontend: (max, current) => `Relatório muito longo. Máximo: ${max}, Atual: ${current}.`,
        communicationFailure: 'Falha de comunicação com o servidor.',
        errorPrefix: 'Erro: ',
        unexpectedResponse: 'Resposta inesperada do servidor.'
    },
    initialProcessButtonHTML: '<i class="bi bi-gear-fill me-1"></i>Processar Relatório',
    initialCopyButtonHTML: '<i class="bi bi-clipboard-data me-1"></i>Copiar Padrão',
    initialCopyEmailButtonHTML: '<i class="bi bi-envelope-check me-1"></i>Copiar E-mail',
    initialClearButtonHTML: '<i class="bi bi-eraser-fill me-1"></i>Limpar Tudo'
};

export const DOMElements = {};
for (const key in CONFIG.selectors) {
    DOMElements[key] = document.querySelector(CONFIG.selectors[key]);
}