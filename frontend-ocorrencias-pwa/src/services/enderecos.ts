import { apiFetch } from './api';

export interface Endereco {
    id: number;
    logradouro: string;
    bairro: string;
    cidade: string;
    estado: string;
    cep: string;
    numero?: string;
    complemento?: string;
}

// Buscar endereços com autocompletar
export async function buscarEnderecos(nome: string, token?: string): Promise<{ enderecos: Endereco[], error?: string }> {
    try {
        console.log('Buscando endereços:', { nome });

        const params = new URLSearchParams();
        if (nome) {
            params.append('nome', nome);
        }

        const response = await apiFetch(`/api/logradouros_view?${params.toString()}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        }, token);

        console.log('Resposta da busca de endereços:', response);
        
        if (response && response.logradouros) {
            return { enderecos: response.logradouros };
        } else {
            console.warn('Resposta inesperada da API de endereços:', response);
            return { enderecos: [] };
        }
    } catch (error: any) {
        console.error('Erro ao buscar endereços:', error);
        // Retornar array vazio em caso de erro para não quebrar a interface
        return { enderecos: [], error: error.message };
    }
}

// Formatar endereço completo
export function formatarEndereco(endereco: Endereco): string {
    const partes = [
        endereco.logradouro,
        endereco.numero,
        endereco.complemento,
        endereco.bairro,
        endereco.cidade,
        endereco.estado,
        endereco.cep
    ].filter(Boolean);

    return partes.join(', ');
} 