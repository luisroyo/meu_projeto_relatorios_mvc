/**
 * Tooltips informativos para o Dashboard Comparativo
 * Este arquivo contém as definições dos tooltips que aparecem ao passar o mouse sobre os ícones de interrogação
 */

const DASHBOARD_TOOLTIPS = {
    // Métricas principais
    "total_rondas": {
        title: "Total de Rondas",
        content: "Soma total de todas as rondas individuais realizadas no período selecionado. Cada registro de plantão pode conter múltiplas rondas. A média por dia real trabalhado é calculada baseada nos dias efetivamente registrados na tabela de rondas."
    },
    "total_ocorrencias": {
        title: "Total de Ocorrências", 
        content: "Número total de ocorrências registradas no período selecionado."
    },
    "media_rondas_mensal": {
        title: "Média de Rondas por Mês",
        content: "Média aritmética do número de rondas realizadas por mês no período analisado."
    },
    "media_rondas_dia_trabalhado": {
        title: "Média de Rondas por Dia Real Trabalhado",
        content: "Média de rondas realizadas por dia efetivamente trabalhado, baseada nos registros reais da tabela de rondas. Esta métrica é muito mais precisa pois considera apenas os dias em que houve atividade real."
    },
    "media_ocorrencias_mensal": {
        title: "Média de Ocorrências por Mês",
        content: "Média aritmética do número de ocorrências registradas por mês no período analisado."
    },
    "mes_mais_rondas": {
        title: "Mês com Mais Rondas",
        content: "Mês que apresentou o maior volume de rondas realizadas."
    },
    "mes_mais_ocorrencias": {
        title: "Mês com Mais Ocorrências",
        content: "Mês que apresentou o maior número de ocorrências registradas."
    },
    "tendencia_rondas": {
        title: "Tendência das Rondas",
        content: "Análise de tendência comparando os últimos 3 meses com os primeiros 3 meses do período. Pode indicar Crescimento, Queda ou Estabilidade."
    },
    "tendencia_ocorrencias": {
        title: "Tendência das Ocorrências",
        content: "Análise de tendência comparando os últimos 3 meses com os primeiros 3 meses do período. Pode indicar Crescimento, Queda ou Estabilidade."
    },

    // Filtros
    "filtro_condominio": {
        title: "Filtro por Condomínio",
        content: "Selecione um condomínio específico para analisar apenas os dados relacionados a ele."
    },
    "filtro_supervisor": {
        title: "Filtro por Supervisor",
        content: "Selecione um supervisor específico para analisar apenas os dados sob sua responsabilidade."
    },
    "filtro_tipo_ocorrencia": {
        title: "Filtro por Tipo de Ocorrência",
        content: "Selecione um tipo específico de ocorrência para focar a análise (ex: Roubo, Vandalismo, etc.)."
    },
    "filtro_status": {
        title: "Filtro por Status",
        content: "Selecione um status específico de ocorrência (Registrada, Em Andamento, Concluída)."
    },
    "filtro_turno": {
        title: "Filtro por Turno",
        content: "Selecione um turno específico (Diurno, Noturno, Diurno Par, Diurno Impar, etc.)."
    },
    "filtro_data_inicio": {
        title: "Data de Início",
        content: "Selecione a data inicial do período que deseja analisar."
    },
    "filtro_data_fim": {
        title: "Data de Fim",
        content: "Selecione a data final do período que deseja analisar."
    },

    // Gráficos
    "grafico_combinado": {
        title: "Gráfico Combinado",
        content: "Visualização que combina barras (rondas) e linha (ocorrências) para facilitar a comparação entre as duas métricas ao longo do tempo."
    },
    "grafico_rondas": {
        title: "Gráfico de Rondas",
        content: "Gráfico de barras mostrando a evolução mensal do número de rondas realizadas."
    },
    "grafico_ocorrencias": {
        title: "Gráfico de Ocorrências",
        content: "Gráfico de linha mostrando a evolução mensal do número de ocorrências registradas."
    },

    // Breakdowns
    "breakdown_condominio": {
        title: "Ranking por Condomínio",
        content: "Lista dos condomínios ordenados por volume de atividade (rondas ou ocorrências)."
    },
    "breakdown_supervisor": {
        title: "Ranking por Supervisor",
        content: "Lista dos supervisores ordenados por volume de atividade sob sua responsabilidade."
    },
    "breakdown_turno": {
        title: "Distribuição por Turno",
        content: "Distribuição das rondas realizadas por turno de trabalho."
    },
    "breakdown_tipo": {
        title: "Distribuição por Tipo",
        content: "Distribuição das ocorrências por tipo/categoria."
    },
    "breakdown_status": {
        title: "Distribuição por Status",
        content: "Distribuição das ocorrências por status atual (Registrada, Em Andamento, Concluída)."
    },

    // Análises
    "analise_tendencia": {
        title: "Análise de Tendência",
        content: "Comparação entre os primeiros e últimos 3 meses do período para identificar padrões de crescimento ou queda."
    },
    "resumo_mensal": {
        title: "Resumo Mensal",
        content: "Tabela detalhada com os valores mensais de rondas e ocorrências para análise comparativa."
    }
};

/**
 * Função para inicializar os tooltips
 */
function initializeTooltips() {
    // Adiciona tooltips aos elementos com data-tooltip
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        const tooltipKey = element.getAttribute('data-tooltip');
        const tooltipData = DASHBOARD_TOOLTIPS[tooltipKey];
        
        if (tooltipData) {
            element.setAttribute('title', `${tooltipData.title}: ${tooltipData.content}`);
            element.style.cursor = 'help';
        }
    });
}

/**
 * Função para criar um ícone de interrogação com tooltip
 */
function createTooltipIcon(tooltipKey, size = '16px') {
    const tooltipData = DASHBOARD_TOOLTIPS[tooltipKey];
    if (!tooltipData) {
        console.warn(`Tooltip não encontrado para a chave: ${tooltipKey}`);
        return '';
    }
    
    return `
        <i class="fas fa-question-circle text-muted" 
           data-tooltip="${tooltipKey}"
           title="${tooltipData.title}: ${tooltipData.content}"
           style="cursor: help; font-size: ${size}; margin-left: 5px;"></i>
    `;
}

// Inicializa tooltips quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', initializeTooltips); 