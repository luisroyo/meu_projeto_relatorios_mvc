export async function iniciarRonda(token: string, dados: {
    condominio_id: number;
    data_plantao: string;
    escala_plantao?: string;
    user_id?: number;
}): Promise<{ sucesso: boolean; message: string; ronda_id?: number }> {
    try {
        console.log('Iniciando ronda:', dados);
        const response = await apiFetch('/api/rondas/iniciar', {
            method: 'POST',
            body: JSON.stringify(dados)
        }, token);
        console.log('Resposta do início de ronda:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao iniciar ronda:', error);
        return { sucesso: false, message: error.message };
    }
}

export async function finalizarRonda(token: string, rondaId: number, dados: {
    log_bruto?: string;
    observacoes?: string;
}): Promise<{ sucesso: boolean; message: string }> {
    try {
        console.log('Finalizando ronda:', { rondaId, dados });
        const response = await apiFetch(`/api/rondas/finalizar/${rondaId}`, {
            method: 'PUT',
            body: JSON.stringify(dados)
        }, token);
        console.log('Resposta da finalização de ronda:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao finalizar ronda:', error);
        return { sucesso: false, message: error.message };
    }
}

export async function atualizarRonda(token: string, rondaId: number, dados: {
    log_bruto?: string;
    observacoes?: string;
}): Promise<{ sucesso: boolean; message: string }> {
    try {
        console.log('Atualizando ronda:', { rondaId, dados });
        const response = await apiFetch(`/api/rondas/atualizar/${rondaId}`, {
            method: 'PUT',
            body: JSON.stringify(dados)
        }, token);
        console.log('Resposta da atualização de ronda:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao atualizar ronda:', error);
        return { sucesso: false, message: error.message };
    }
}

export async function gerarRelatorioRonda(token: string, condominioId: number, data: string): Promise<{ sucesso: boolean; message: string; relatorio?: string }> {
    try {
        console.log('Gerando relatório de ronda:', { condominioId, data });
        const response = await apiFetch(`/api/rondas/gerar-relatorio/${condominioId}/${data}`, {
            method: 'POST'
        }, token);
        console.log('Resposta da geração de relatório:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao gerar relatório de ronda:', error);
        return { sucesso: false, message: error.message };
    }
}

export async function enviarRondaWhatsApp(token: string, condominioId: number, data: string): Promise<{ sucesso: boolean; message: string }> {
    try {
        console.log('Enviando ronda via WhatsApp:', { condominioId, data });
        const response = await apiFetch(`/api/rondas/enviar-whatsapp/${condominioId}/${data}`, {
            method: 'POST'
        }, token);
        console.log('Resposta do envio via WhatsApp:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao enviar ronda via WhatsApp:', error);
        return { sucesso: false, message: error.message };
    }
}
import { apiFetch } from '../api';

export async function verificarRondaEmAndamento(token: string, condominioId: number): Promise<RondaEmAndamento> {
    try {
        console.log('Verificando ronda em andamento:', { condominioId });
        const response = await apiFetch(`/api/rondas/em-andamento/${condominioId}`, {}, token);
        console.log('Resposta da verificação de ronda:', response);

        // Verificar se a resposta tem a estrutura esperada
        if (response && typeof response.em_andamento === 'boolean') {
            return response;
        } else {
            console.warn('Resposta inesperada da API:', response);
            return { em_andamento: false };
        }
    } catch (error: any) {
        console.error('Erro ao verificar ronda em andamento:', error);
        // Retornar estado padrão em caso de erro
        return { em_andamento: false };
    }
}
// Interfaces para Rondas Regulares
export interface Ronda {
    id: number;
    condominio_id: number;
    condominio_nome?: string;
    data_plantao: string;
    escala_plantao: string;
    log_bruto?: string;
    total_rondas?: number;
    duracao_total_minutos?: number;
    primeiro_evento_utc?: string;
    ultimo_evento_utc?: string;
    user_id?: number;
    user_nome?: string;
    status: string;
    data_criacao?: string;
    data_modificacao?: string;
}

export interface RondaEmAndamento {
    em_andamento: boolean;
    ronda?: {
        id: number;
        inicio?: string;
        data_plantao?: string;
        hora_entrada?: string;
        escala_plantao?: string;
        turno?: string;
        observacoes?: string;
        user_id?: number;
        user_nome?: string;
    };
}



export async function listarRondasDoDia(token: string, condominioId: number, data: string): Promise<{ rondas: Ronda[], error?: string }> {
    try {
        console.log('Buscando rondas do dia:', { condominioId, data });
        const response = await apiFetch(`/api/rondas/do-dia/${condominioId}/${data}`, {}, token);
        console.log('Resposta da busca de rondas:', response);
        return { rondas: response.rondas || [] };
    } catch (error: any) {
        console.error('Erro ao buscar rondas do dia:', error);
        return { rondas: [], error: error.message };
    }
}
// ...demais funções de rondas regulares...
