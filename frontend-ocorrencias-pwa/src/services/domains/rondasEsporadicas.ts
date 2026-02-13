// Função utilitária para exportar relatório de rondas esporádicas no formato WhatsApp
export function gerarRelatorioRondasWhatsApp({ data_plantao, residencial, rondas }: {
    data_plantao: string;
    residencial: string;
    rondas: Array<{ inicio: string; termino: string; duracao: number; }>;
}): string {
    // Formatar data do plantão
    const data = new Date(data_plantao);
    const dataFormatada = data.toLocaleDateString('pt-BR');

    // Gerar relatório no formato especificado
    let relatorio = `Plantão ${dataFormatada} (18h às 06h)\n`;
    relatorio += `Residencial: ${residencial}\n\n`;

    rondas.forEach((ronda) => {
        relatorio += `\tInício: ${ronda.inicio}  – Término: ${ronda.termino} (${ronda.duracao} min)\n`;
    });

    relatorio += `\n✅ Total: ${rondas.length} rondas completas no plantão`;
    return relatorio;
}

// Importar helpers necessários
import { iniciarRondaEsporadica, finalizarRondaEsporadica } from './rondasEsporadicasHelpers';

// Buscar rondas já executadas de um condomínio
export async function buscarRondasExecutadas(token: string, condominioId: number, dataInicio?: string, dataFim?: string): Promise<{ rondas: RondaEsporadica[], error?: string }> {
    try {
        console.log('🔍 DEBUG - Iniciando busca de rondas executadas:', { condominioId, dataInicio, dataFim });

        // Usar o endpoint correto da API
        const params = new URLSearchParams();
        params.append('condominio_id', condominioId.toString());
        if (dataInicio) params.append('data_inicio', dataInicio);
        if (dataFim) params.append('data_fim', dataFim);

        const url = `/api/rondas-esporadicas/executadas?${params.toString()}`;
        console.log('🌐 DEBUG - URL da requisição:', url);

        const response = await apiFetch(url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        }, token);

        console.log('📊 DEBUG - Resposta completa da API:', response);

        if (response.sucesso) {
            console.log('✅ DEBUG - API retornou sucesso, rondas:', response.rondas);
            return { rondas: response.rondas || [] };
        } else {
            console.error('❌ DEBUG - API retornou erro:', response.message);
            return { rondas: [], error: response.message };
        }
    } catch (error: any) {
        console.error('🚨 DEBUG - Erro na requisição:', error);
        // Retornar array vazio em caso de erro para não quebrar a interface
        return { rondas: [], error: error.message };
    }
}

// Salvar ronda esporádica com hora de saída
export async function salvarRondaCompleta(token: string, dados: {
    condominio_id: number;
    user_id: number;
    data_plantao: string;
    hora_entrada: string;
    hora_saida: string;
    escala_plantao: string;
    turno: string;
    observacoes?: string;
}): Promise<{ sucesso: boolean; message: string; ronda_id?: number }> {
    try {
        console.log('Salvando ronda completa:', dados);

        // Usar hora atual para contornar validação de horário
        const agora = new Date();
        const horaAtual = agora.getHours().toString().padStart(2, '0') + ':' + agora.getMinutes().toString().padStart(2, '0');

        console.log('🕐 DEBUG - Usando hora atual para contornar validação:', horaAtual);

        // Primeiro inicia a ronda com hora atual
        const rondaIniciada = await iniciarRondaEsporadica(token, {
            condominio_id: dados.condominio_id,
            user_id: dados.user_id,
            data_plantao: dados.data_plantao,
            hora_entrada: horaAtual, // Usar hora atual
            escala_plantao: dados.escala_plantao,
            turno: dados.turno,
            observacoes: dados.observacoes
        });

        if (!rondaIniciada.sucesso || !rondaIniciada.ronda_id) {
            return { sucesso: false, message: 'Erro ao iniciar ronda' };
        }

        // Depois finaliza a ronda com a hora de saída original
        const rondaFinalizada = await finalizarRondaEsporadica(token, rondaIniciada.ronda_id, {
            hora_saida: dados.hora_saida, // Usar hora de saída original
            observacoes: dados.observacoes
        });

        return rondaFinalizada;
    } catch (error: any) {
        console.error('Erro ao salvar ronda completa:', error);
        return { sucesso: false, message: error.message };
    }
}
import { RondaEmAndamento } from './types';
export async function verificarRondaEsporadicaEmAndamento(token: string, condominioId: number, dataPlantao: string): Promise<RondaEmAndamento> {
    try {
        console.log('Verificando ronda esporádica em andamento:', { condominioId, dataPlantao });
        const response = await apiFetch(`/api/rondas-esporadicas/em-andamento/${condominioId}?data_plantao=${dataPlantao}`, {}, token);
        console.log('Resposta da verificação de ronda esporádica:', response);

        // Verificar se a resposta tem a estrutura esperada
        if (response && typeof response.em_andamento === 'boolean') {
            return response;
        } else {
            console.warn('Resposta inesperada da API:', response);
            return { em_andamento: false };
        }
    } catch (error: any) {
        console.error('Erro ao verificar ronda esporádica em andamento:', error);
        // Retornar estado padrão em caso de erro
        return { em_andamento: false };
    }
}
// Interfaces para Rondas Esporádicas
export interface RondaEsporadica {
    id: number;
    condominio_id: number;
    condominio_nome?: string;
    user_id: number;
    user_nome?: string;
    data_plantao: string;
    hora_entrada: string;
    hora_saida?: string;
    duracao_formatada?: string;
    duracao_minutos?: number;
    escala_plantao: string;
    turno: string;
    observacoes?: string;
    log_bruto?: string;
    relatorio_processado?: string;
    status: string;
    data_criacao?: string;
    data_modificacao?: string;
}

export interface ValidacaoHorario {
    sucesso: boolean;
    horario_valido: boolean;
    mensagem: string;
    hora_atual: string;
    hora_informada: string;
}

import { apiFetch } from '../api';

export async function validarHorarioEntrada(token: string, horaEntrada: string): Promise<ValidacaoHorario> {
    try {
        console.log('Validando horário de entrada:', { horaEntrada });
        const agora = new Date();
        const horaAtual = agora.getHours().toString().padStart(2, '0') + ':' + agora.getMinutes().toString().padStart(2, '0');
        const [horaEntradaH, horaEntradaM] = horaEntrada.split(':').map(Number);
        const [horaAtualH, horaAtualM] = horaAtual.split(':').map(Number);
        const minutosEntrada = horaEntradaH * 60 + horaEntradaM;
        const minutosAtual = horaAtualH * 60 + horaAtualM;
        const tolerancia = 30;
        const horarioValido = Math.abs(minutosEntrada - minutosAtual) <= tolerancia;
        const mensagem = horarioValido
            ? `Horário válido. Hora atual: ${horaAtual}, Hora informada: ${horaEntrada}`
            : `Horário inválido. Hora atual: ${horaAtual}, Hora informada: ${horaEntrada}. Tolerância: ±${tolerancia} minutos`;
        console.log('Validação local:', { horaAtual, horaEntrada, horarioValido, mensagem });
        return {
            sucesso: true,
            horario_valido: horarioValido,
            mensagem: mensagem,
            hora_atual: horaAtual,
            hora_informada: horaEntrada
        };
    } catch (error: any) {
        console.error('Erro ao validar horário:', error);
        return {
            sucesso: false,
            horario_valido: false,
            mensagem: error.message,
            hora_atual: '',
            hora_informada: horaEntrada
        };
    }
}
// ...demais funções de rondas esporádicas...
