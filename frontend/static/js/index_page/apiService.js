// app/static/js/index_page/apiService.js
import { CONFIG } from './config.js';
import { displayStatus } from './uiHandlers.js'; // Para erros de CSRF

export async function callProcessReportAPI(relatorioBrutoValue, formatarParaEmailChecked) {
    const csrfTokenElement = document.querySelector('meta[name="csrf-token"]');
    if (!csrfTokenElement) {
        displayStatus('Erro de configuração: CSRF token não encontrado.', 'danger', 'standard');
        // Lançar um erro aqui para ser pego pelo chamador (reportLogic.js)
        throw new Error('CSRF token não encontrado.');
    }
    const csrfToken = csrfTokenElement.getAttribute('content');

    const payload = {
        relatorio_bruto: relatorioBrutoValue,
        format_for_email: formatarParaEmailChecked
    };

    const response = await fetch(CONFIG.apiEndpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(payload),
    });

    const contentType = response.headers.get("content-type");
    if (contentType && contentType.indexOf("application/json") !== -1) {
        const data = await response.json();
        if (!response.ok) {
            // Encapsula o erro para o chamador decidir como apresentar
            const errorMessage = data.message || data.erro || `Erro do servidor: ${response.status}`;
            const error = new Error(errorMessage);
            error.data = data; // Anexa os dados do erro para uso posterior
            error.isApiError = true;
            throw error;
        }
        return data; // Retorna os dados em caso de sucesso
    } else {
        const errorText = await response.text();
        let userMessage = CONFIG.messages.communicationFailure || "Falha de comunicação com o servidor.";
        if (!response.ok && errorText.trim().toLowerCase().startsWith("<!doctype html")) {
            userMessage += " Possível erro de CSRF ou resposta HTML inesperada.";
        } else if (!response.ok) {
            userMessage += ` Erro ${response.status}.`;
        } else {
            userMessage += " Resposta inesperada do servidor (não JSON, mas status OK)."
        }
        const error = new Error(userMessage);
        error.isNetworkOrParseError = true; // Flag para tipo de erro
        throw error;
    }
}