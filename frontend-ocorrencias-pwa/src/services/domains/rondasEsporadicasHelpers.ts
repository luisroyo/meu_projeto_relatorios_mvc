// Funções específicas de rondas esporádicas, movidas de rondas.ts
import { apiFetch } from '../api';

export async function iniciarRondaEsporadica(token: string, dados: {
    condominio_id: number;
    user_id: number;
    data_plantao: string;
    hora_entrada: string;
    escala_plantao: string;
    turno: string;
    observacoes?: string;
}): Promise<{ sucesso: boolean; message: string; ronda_id?: number }> {
    try {
        console.log('Iniciando ronda esporádica:', dados);
        const response = await apiFetch('/api/rondas-esporadicas/iniciar', {
            method: 'POST',
            body: JSON.stringify(dados)
        }, token);
        console.log('Resposta do início de ronda esporádica:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao iniciar ronda esporádica:', error);
        return { sucesso: false, message: error.message };
    }
}

export async function finalizarRondaEsporadica(token: string, rondaId: number, dados: {
    hora_saida: string;
    observacoes?: string;
}): Promise<{ sucesso: boolean; message: string }> {
    try {
        console.log('Finalizando ronda esporádica:', { rondaId, dados });
        const response = await apiFetch(`/api/rondas-esporadicas/finalizar/${rondaId}`, {
            method: 'PUT',
            body: JSON.stringify(dados)
        }, token);
        console.log('Resposta da finalização de ronda esporádica:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao finalizar ronda esporádica:', error);
        return { sucesso: false, message: error.message };
    }
}
