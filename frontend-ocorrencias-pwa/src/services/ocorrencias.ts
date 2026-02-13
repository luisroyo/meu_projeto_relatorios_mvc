import { apiFetch } from './api';

export interface Ocorrencia {
    id: number;
    relatorio_final?: string; // Campo opcional, pode vir como 'descricao' do backend
    descricao?: string; // Campo que o backend retorna
    data_hora_ocorrencia?: string;
    turno?: string;
    status: string;
    endereco_especifico?: string; // Campo opcional, pode vir como 'endereco' do backend
    endereco?: string; // Campo que o backend retorna
    condominio?: { id: number, nome: string };
    tipo?: { id: number, nome: string };
    supervisor?: { id: number, username: string };
    supervisor_id?: number; // ID do supervisor
    registrado_por?: { id: number, username: string };
    registrado_por_user_id?: number; // ID do usuário que registrou
    data_criacao?: string;
    data_modificacao?: string;
    colaboradores?: Array<{ id: number, nome: string }>;
    orgaos_acionados?: Array<{ id: number, nome: string }>;
}

export interface FiltrosOcorrencia {
    status?: string;
    condominio_id?: number;
    tipo_id?: number;
    data_inicio?: string;
    data_fim?: string;
    supervisor_id?: number;
}

// Analisar relatório (já existe, mas vou melhorar)
export async function analisarRelatorio(token: string, texto_relatorio: string) {
    try {
        if (!token) {
            console.error('Token não fornecido para análise de relatório');
            return { sucesso: false, message: 'Token de autenticação não fornecido' };
        }

        if (!texto_relatorio || texto_relatorio.trim() === '') {
            console.error('Texto do relatório vazio');
            return { sucesso: false, message: 'Texto do relatório é obrigatório' };
        }

        console.log('Analisando relatório:', {
            token: token ? 'Presente' : 'Ausente',
            texto_relatorio: texto_relatorio.substring(0, 100) + '...'
        });

        // Verificar se a rota existe antes de tentar acessá-la
        try {
            const requestBody = { relatorio_bruto: texto_relatorio };
            console.log('Enviando para API:', JSON.stringify(requestBody, null, 2));

            const response = await apiFetch('/api/analisador/processar-relatorio', {
                method: 'POST',
                body: JSON.stringify(requestBody),
            }, token);

            console.log('Resposta da análise:', response);

            // Verificar se a resposta tem a estrutura esperada
            if (response.classificacao && response.relatorio_processado) {
                return {
                    sucesso: true,
                    dados: {
                        classificacao: response.classificacao,
                        relatorio_corrigido: response.relatorio_processado,
                        // Outros campos que podem vir do backend
                        ...response
                    }
                };
            }

            return response;
        } catch (apiError: any) {
            console.log('🔍 DEBUG - Capturou erro da API:', {
                message: apiError.message,
                status: apiError.status,
                statusText: apiError.statusText,
                originalError: apiError.originalError
            });

            // Se a rota não existir (erro 405), usar fallback
            if (apiError.status === 405 || apiError.message?.includes('405') || apiError.message?.includes('Method Not Allowed')) {
                console.warn('🚨 Rota de análise não disponível (405), usando processamento local...');
                console.log('🔄 Ativando fallback...');
                return processarRelatorioLocal(texto_relatorio);
            }

            console.log('❌ Erro não é 405, re-lançando:', apiError);
            throw apiError;
        }
    } catch (error) {
        console.error('Erro ao analisar relatório:', error);
        return { sucesso: false, message: 'Erro ao analisar relatório', error };
    }
}

// Função de fallback para processamento local quando a API não estiver disponível
function processarRelatorioLocal(texto_relatorio: string) {
    console.log('🚀 PROCESSAMENTO LOCAL ATIVADO!');
    console.log('📝 Texto original recebido:', texto_relatorio.substring(0, 100) + '...');

    // Processamento básico local
    const linhas = texto_relatorio.split('\n').filter(linha => linha.trim());
    console.log('📊 Linhas após filtro:', linhas.length);

    const relatorioProcessado = linhas.map(linha => {
        // Limpar formatação básica
        return linha.trim().replace(/\s+/g, ' ');
    }).join('\n');

    console.log('✨ Relatório processado:', relatorioProcessado.substring(0, 100) + '...');

    const resultado = {
        sucesso: true,
        dados: {
            classificacao: 'processado_localmente',
            relatorio_corrigido: relatorioProcessado,
            message: 'Relatório processado localmente (API não disponível)',
            relatorio_original: texto_relatorio
        }
    };

    console.log('🎯 Resultado final do fallback:', resultado);
    return resultado;
}

// Buscar histórico de ocorrências
export async function buscarHistoricoOcorrencias(token: string, filtros?: FiltrosOcorrencia): Promise<{ historico: Ocorrencia[], error?: string }> {
    try {
        console.log('Buscando histórico de ocorrências:', filtros);

        const params = new URLSearchParams();
        if (filtros?.status) params.append('status', filtros.status);
        if (filtros?.condominio_id) params.append('condominio_id', filtros.condominio_id.toString());
        if (filtros?.tipo_id) params.append('tipo_id', filtros.tipo_id.toString());
        if (filtros?.data_inicio) params.append('data_inicio', filtros.data_inicio);
        if (filtros?.data_fim) params.append('data_fim', filtros.data_fim);
        if (filtros?.supervisor_id) params.append('supervisor_id', filtros.supervisor_id.toString());

        const response = await apiFetch(`/api/ocorrencias?${params.toString()}`, {
            method: 'GET',
        }, token);

        console.log('Resposta do histórico:', response);
        return { historico: response.data?.ocorrencias || [] };
    } catch (error: any) {
        console.error('Erro ao buscar histórico:', error);
        return { historico: [], error: error.message };
    }
}

// Buscar detalhes de uma ocorrência específica
export async function buscarDetalhesOcorrencia(token: string, ocorrenciaId: number): Promise<Ocorrencia | null> {
    try {
        console.log('Buscando detalhes da ocorrência:', { ocorrenciaId });

        const response = await apiFetch(`/api/ocorrencias/${ocorrenciaId}`, {
            method: 'GET',
        }, token);

        console.log('Detalhes da ocorrência:', response);
        return response.data?.ocorrencia || response;
    } catch (error: any) {
        console.error('Erro ao buscar detalhes da ocorrência:', error);
        return null;
    }
}

// Salvar nova ocorrência
export async function salvarOcorrencia(token: string, dados: {
    relatorio_final: string;
    turno?: string;
    endereco_especifico?: string;
    condominio_id?: number;
    ocorrencia_tipo_id?: number;
    registrado_por_user_id?: number;
    supervisor_id?: number;
}): Promise<{ sucesso: boolean, message?: string, ocorrencia_id?: number, error?: string }> {
    try {
        console.log('Salvando ocorrência:', dados);

        const response = await apiFetch('/api/ocorrencias', {
            method: 'POST',
            body: JSON.stringify(dados),
        }, token);

        console.log('Resposta do salvamento:', response);
        return response.data || response;
    } catch (error: any) {
        console.error('Erro ao salvar ocorrência:', error);
        return { sucesso: false, error: error.message };
    }
} 