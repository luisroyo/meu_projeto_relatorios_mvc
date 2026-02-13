import { apiFetch } from '../api';

export async function consolidarTurnoRondasEsporadicas(token: string, condominioId: number, data: string): Promise<ConsolidacaoResultado> {
    try {
        console.log('Consolidando turno de rondas esporádicas:', { condominioId, data });
        const response = await apiFetch(`/api/rondas-esporadicas/consolidar-turno/${condominioId}/${data}`, {
            method: 'POST'
        }, token);
        console.log('Resposta da consolidação de turno:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao consolidar turno de rondas esporádicas:', error);
        return { sucesso: false, message: error.message };
    }
}

export async function processoCompletoConsolidacao(token: string, condominioId: number, data: string): Promise<ConsolidacaoResultado> {
    try {
        console.log('Executando processo completo de consolidação:', { condominioId, data });
        const response = await apiFetch(`/api/rondas-esporadicas/processo-completo/${condominioId}/${data}`, {
            method: 'POST'
        }, token);
        console.log('Resposta do processo completo:', response);
        return response;
    } catch (error: any) {
        console.error('Erro no processo completo de consolidação:', error);
        return { sucesso: false, message: error.message };
    }
}

export async function marcarRondasProcessadas(token: string, condominioId: number, data: string): Promise<{ sucesso: boolean; message: string }> {
    try {
        console.log('Marcando rondas como processadas:', { condominioId, data });
        const response = await apiFetch(`/api/rondas-esporadicas/marcar-processadas/${condominioId}/${data}`, {
            method: 'PUT'
        }, token);
        console.log('Resposta da marcação como processadas:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao marcar rondas como processadas:', error);
        return { sucesso: false, message: error.message };
    }
}

export async function statusConsolidacao(token: string, condominioId: number, data: string): Promise<StatusConsolidacao> {
    try {
        console.log('Verificando status de consolidação:', { condominioId, data });
        const response = await apiFetch(`/api/rondas-esporadicas/status-consolidacao/${condominioId}/${data}`, {}, token);
        console.log('Resposta do status de consolidação:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao verificar status de consolidação:', error);
        return {
            sucesso: false,
            data: data,
            condominio_id: condominioId,
            status: {
                total_rondas_esporadicas: 0,
                rondas_finalizadas: 0,
                rondas_processadas: 0,
                duracao_total_minutos: 0,
                ronda_principal_criada: false,
                pode_consolidar: false,
                ja_consolidado: false
            },
            rondas: []
        };
    }
}
// Interfaces de consolidação e funções relacionadas
export interface ConsolidacaoResultado {
    sucesso: boolean;
    message: string;
    relatorio_consolidado?: string;
    total_rondas?: number;
    periodo?: string;
    duracao_total_minutos?: number;
    whatsapp_enviado?: boolean;
    ronda_principal_id?: number;
}

export interface StatusConsolidacao {
    sucesso: boolean;
    data: string;
    condominio_id: number;
    status: {
        total_rondas_esporadicas: number;
        rondas_finalizadas: number;
        rondas_processadas: number;
        duracao_total_minutos: number;
        ronda_principal_criada: boolean;
        ronda_principal_id?: number;
        pode_consolidar: boolean;
        ja_consolidado: boolean;
    };
    rondas: any[];
}


// ...demais funções de consolidação...
