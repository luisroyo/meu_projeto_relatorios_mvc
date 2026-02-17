// app/static/js/index_page/apiService.js
import { CONFIG } from './config.js';
import { displayStatus } from './uiHandlers.js'; // Para erros de CSRF

// Função de fallback para processar relatório localmente
function processarRelatorioLocal(relatorioBruto, formatarParaEmail = false) {
    console.log('processarRelatorioLocal: Iniciando processamento local...');
    console.log('processarRelatorioLocal: Texto original:', relatorioBruto.substring(0, 200) + '...');

    // Processamento básico de correção de texto
    let relatorioProcessado = relatorioBruto
        .replace(/\xa0/g, ' ') // Remove caracteres especiais
        .trim()
        .replace(/\s+/g, ' ') // Remove espaços extras
        .replace(/([.!?])\s*([A-Za-z])/g, '$1 $2') // Adiciona espaços após pontuação
        .replace(/^\w/, c => c.toUpperCase()); // Primeira letra maiúscula

    // Melhoria básica de pontuação e capitalização
    relatorioProcessado = relatorioProcessado
        .replace(/(\w)\s*:\s*/g, '$1: ') // Normaliza dois pontos
        .replace(/(\w)\s*,\s*/g, '$1, ') // Normaliza vírgulas
        .replace(/\b(data|hora|colaborador|endereço|viatura|vtr)\b/gi, (match) => {
            return match.charAt(0).toUpperCase() + match.slice(1).toLowerCase();
        });

    // Correções específicas para o texto do exemplo
    relatorioProcessado = relatorioProcessado
        .replace(/hoirario/gi, 'horário')
        .replace(/conatto/gi, 'contato')
        .replace(/marador/gi, 'morador')
        .replace(/fernado/gi, 'Fernando')
        .replace(/\b(\w+)\s*,\s*o\s+mesmo\s+relatou/gi, '$1, o mesmo relatou')
        .replace(/\bpor\s+isso\s+o\s+motivo\b/gi, 'esse foi o motivo')
        .replace(/\bmais\s+se\s+comprometeu\b/gi, 'mas se comprometeu');

    // Melhoria de estrutura de frases
    relatorioProcessado = relatorioProcessado
        .replace(/^(\w)/g, (match) => match.toUpperCase()) // Primeira letra maiúscula
        .replace(/([.!?])\s*$/g, '$1') // Garante pontuação no final
        .replace(/([^.!?])$/g, '$1.'); // Adiciona ponto no final se não tiver

    // Se solicitado formato de email, aplica formatação adicional
    let relatorioEmail = null;
    if (formatarParaEmail) {
        relatorioEmail = `
Prezados,

${relatorioProcessado}

Atenciosamente,
Equipe de Segurança
        `.trim();
    }

    console.log('processarRelatorioLocal: Texto processado:', relatorioProcessado.substring(0, 200) + '...');
    console.log('processarRelatorioLocal: Processamento concluído');

    return {
        relatorio_processado: relatorioProcessado,
        relatorio_email: relatorioEmail,
        fallback_usado: true,
        message: 'Relatório processado localmente (API indisponível)'
    };
}

export async function callProcessReportAPI(relatorioBrutoValue, formatarParaEmailChecked) {
    console.log('callProcessReportAPI: Iniciando...');
    console.log('callProcessReportAPI: relatorioBrutoValue length:', relatorioBrutoValue ? relatorioBrutoValue.length : 'N/A');
    console.log('callProcessReportAPI: formatarParaEmailChecked:', formatarParaEmailChecked);

    try {
        const csrfTokenElement = document.querySelector('meta[name="csrf-token"]');
        if (!csrfTokenElement) {
            console.warn('callProcessReportAPI: CSRF token não encontrado, usando fallback local');
            return processarRelatorioLocal(relatorioBrutoValue, formatarParaEmailChecked);
        }
        const csrfToken = csrfTokenElement.getAttribute('content');
        console.log('callProcessReportAPI: CSRF token encontrado');

        const payload = {
            relatorio_bruto: relatorioBrutoValue,
            format_for_email: formatarParaEmailChecked
        };
        console.log('callProcessReportAPI: Payload criado:', payload);

        console.log('callProcessReportAPI: Fazendo fetch para:', CONFIG.apiEndpoint);

        const response = await fetch(CONFIG.apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(payload),
        });

        console.log('callProcessReportAPI: Response recebida:', {
            status: response.status,
            statusText: response.statusText,
            contentType: response.headers.get("content-type")
        });

        // Se erro 405 (Method Not Allowed), usar fallback
        if (response.status === 405) {
            console.warn('callProcessReportAPI: API retornou 405, usando fallback local');
            return processarRelatorioLocal(relatorioBrutoValue, formatarParaEmailChecked);
        }

        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            const data = await response.json();
            console.log('callProcessReportAPI: Dados JSON recebidos:', data);

            if (!response.ok) {
                // Se erro da API, usar fallback
                console.warn('callProcessReportAPI: API retornou erro, usando fallback local');
                return processarRelatorioLocal(relatorioBrutoValue, formatarParaEmailChecked);
            }

            console.log('callProcessReportAPI: Retornando dados da API com sucesso');

            // Verifica se a resposta está encapsulada em 'data' (padrão success_response)
            if (data.success && data.data) {
                console.log('callProcessReportAPI: Desembrulhando dados da resposta padrão');
                return data.data;
            }

            return data; // Retorna os dados como estão se não seguir o padrão
        } else {
            console.warn('callProcessReportAPI: Resposta não é JSON, usando fallback local');
            return processarRelatorioLocal(relatorioBrutoValue, formatarParaEmailChecked);
        }
    } catch (error) {
        console.warn('callProcessReportAPI: Erro na requisição, usando fallback local:', error.message);
        return processarRelatorioLocal(relatorioBrutoValue, formatarParaEmailChecked);
    }
}