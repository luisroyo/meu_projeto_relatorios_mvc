// Interfaces para Colaboradores
export interface Colaborador {
    id: number;
    nome: string;
    nome_completo: string;
    email?: string;
    cargo?: string;
}

export interface ListaColaboradores {
    sucesso: boolean;
    colaboradores: Colaborador[];
    total: number;
}

import { apiFetch } from '../api';

export async function listarColaboradores(token: string): Promise<ListaColaboradores> {
    try {
        console.log('Buscando colaboradores');
        const response = await apiFetch('/api/colaboradores', {}, token);
        console.log('Resposta da busca de colaboradores:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao buscar colaboradores:', error);
        return { sucesso: false, colaboradores: [], total: 0 };
    }
}

export async function buscarColaboradores(nome: string, token?: string): Promise<{ colaboradores: Colaborador[], error?: string }> {
    try {
        console.log('🔍 DEBUG - Buscando colaboradores:', { nome });
        const params = new URLSearchParams();
        if (nome) {
            params.append('nome', nome);
        }
        const url = `/api/colaboradores?${params.toString()}`;
        console.log('🌐 DEBUG - URL da requisição:', url);
        const response = await apiFetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        }, token);
        console.log('📊 DEBUG - Resposta da busca de colaboradores:', response);
        if (response && response.colaboradores) {
            console.log('✅ DEBUG - Colaboradores encontrados:', response.colaboradores.length);
            return { colaboradores: response.colaboradores };
        } else {
            console.warn('⚠️ DEBUG - Resposta inesperada da API de colaboradores:', response);
            return { colaboradores: [] };
        }
    } catch (error: any) {
        console.error('🚨 DEBUG - Erro ao buscar colaboradores:', error);
        return { colaboradores: [], error: error.message };
    }
}
