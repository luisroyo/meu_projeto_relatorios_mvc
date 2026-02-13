// Interfaces para Condomínios
export interface Condominio {
    id: number;
    nome: string;
}

export interface ListaCondominios {
    sucesso: boolean;
    condominios: Condominio[];
    total: number;
}

import { apiFetch } from '../api';

export async function listarCondominios(token: string): Promise<ListaCondominios> {
    try {
        console.log('Buscando condomínios');
        const response = await apiFetch('/api/condominios', {}, token);
        console.log('Resposta da busca de condomínios:', response);
        return response;
    } catch (error: any) {
        console.error('Erro ao buscar condomínios:', error);
        return { sucesso: false, condominios: [], total: 0 };
    }
}

export async function buscarCondominios(nome: string, token?: string): Promise<{ condominios: Condominio[], error?: string }> {
    try {
        console.log('🔍 DEBUG - Buscando condomínios:', { nome });
        const params = new URLSearchParams();
        if (nome) {
            params.append('nome', nome);
        }
        const url = `/api/condominios?${params.toString()}`;
        console.log('🌐 DEBUG - URL da requisição:', url);
        const response = await apiFetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        }, token);
        console.log('📊 DEBUG - Resposta da busca de condomínios:', response);
        if (response && response.condominios) {
            console.log('✅ DEBUG - Condomínios encontrados:', response.condominios.length);
            return { condominios: response.condominios };
        } else {
            console.warn('⚠️ DEBUG - Resposta inesperada da API de condomínios:', response);
            return { condominios: [] };
        }
    } catch (error: any) {
        console.error('🚨 DEBUG - Erro ao buscar condomínios:', error);
        return { condominios: [], error: error.message };
    }
}
