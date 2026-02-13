import { useState, useEffect } from 'react';
import { buscarRondasExecutadas } from '../services/domains/rondasEsporadicas';
import { buscarCondominios } from '../services/domains/condominios';

// Interfaces baseadas na estrutura domains/
interface Ronda {
    id?: number;
    residencial: string;
    inicio: string;
    termino?: string;
    duracao?: number;
    status: 'iniciada' | 'finalizada';
}

interface Condominio {
    id: number;
    nome: string;
}

interface RondaExecutada {
    id: number;
    data_plantao: string;
    hora_entrada: string;
    hora_saida?: string;
    duracao_minutos?: number;
    escala_plantao: string;
    turno: string;
    observacoes?: string;
}

interface PeriodoPlantao {
    inicio: string;
    fim: string;
    inicioFormatado: string;
    fimFormatado: string;
}

export const useRondaState = (token: string) => {
    // Estados principais
    const [rondas, setRondas] = useState<Ronda[]>([]);
    const [residencial, setResidencial] = useState<string>('');
    const [inicioRonda, setInicioRonda] = useState<string>('');
    const [terminoRonda, setTerminoRonda] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(false);
    const [rondaAtual, setRondaAtual] = useState<Ronda | null>(null);

    // Estados de configuração
    const [dataPlantao, setDataPlantao] = useState<string>(new Date().toISOString().split('T')[0]);
    const [escalaPlantao, setEscalaPlantao] = useState<string>('18 às 06');
    const [condominioId, setCondominioId] = useState<number>(1);
    const [condominioNome, setCondominioNome] = useState<string>('');

    // Estados de rondas executadas
    const [rondasExecutadas, setRondasExecutadas] = useState<RondaExecutada[]>([]);
    const [loadingRondasExecutadas, setLoadingRondasExecutadas] = useState<boolean>(false);

    // Estados de controle inteligente
    const [periodoInicio, setPeriodoInicio] = useState<string>('');
    const [periodoFim, setPeriodoFim] = useState<string>('');
    const [condominiosPendentes, setCondominiosPendentes] = useState<string[]>([]);
    const [rondasSalvas, setRondasSalvas] = useState<Ronda[]>([]);

    // Estados do contador
    const [contador, setContador] = useState<number>(1200); // 20 minutos
    const [contadorAtivo, setContadorAtivo] = useState<boolean>(false);

    // Função para calcular período do plantão
    const calcularPeriodoPlantao = (data: string, escala: string): PeriodoPlantao => {
        const dataPlantao = new Date(data + 'T00:00:00');

        if (escala === '18 às 06') {
            const inicio = new Date(dataPlantao);
            inicio.setHours(18, 0, 0, 0);

            const fim = new Date(dataPlantao);
            fim.setDate(fim.getDate() + 1);
            fim.setHours(6, 0, 0, 0);

            return {
                inicio: inicio.toISOString(),
                fim: fim.toISOString(),
                inicioFormatado: inicio.toLocaleString('pt-BR'),
                fimFormatado: fim.toLocaleString('pt-BR')
            };
        } else {
            const inicio = new Date(dataPlantao);
            inicio.setHours(6, 0, 0, 0);

            const fim = new Date(dataPlantao);
            fim.setHours(18, 0, 0, 0);

            return {
                inicio: inicio.toISOString(),
                fim: fim.toISOString(),
                inicioFormatado: inicio.toLocaleString('pt-BR'),
                fimFormatado: fim.toLocaleString('pt-BR')
            };
        }
    };

    // Buscar rondas executadas
    const buscarRondasDoCondominio = async (condominioId: number) => {
        if (!condominioId) return;

        setLoadingRondasExecutadas(true);
        try {
            const periodo = calcularPeriodoPlantao(dataPlantao, escalaPlantao);
            const dataInicio = new Date(periodo.inicio).toISOString().split('T')[0];
            const dataFim = new Date(periodo.fim).toISOString().split('T')[0];

            console.log('🔍 DEBUG - Buscando rondas executadas:', {
                condominioId, dataInicio, dataFim, dataPlantao, escalaPlantao
            });

            const resultado = await buscarRondasExecutadas(token, condominioId, dataInicio, dataFim);

            if (resultado.rondas) {
                setRondasExecutadas(resultado.rondas);
            } else {
                setRondasExecutadas([]);
            }
        } catch (error) {
            console.error('🚨 DEBUG - Erro ao buscar rondas executadas:', error);
            setRondasExecutadas([]);
        } finally {
            setLoadingRondasExecutadas(false);
        }
    };

    // Verificar condomínios pendentes
    const verificarCondominiosPendentes = () => {
        const condominiosComRondas = Array.from(new Set(rondasSalvas.map(r => r.residencial)));
        const condominiosExecutados = Array.from(new Set(rondasExecutadas.map(r => r.observacoes || '')));

        const pendentes = condominiosComRondas.filter(cond =>
            !condominiosExecutados.includes(cond)
        );

        setCondominiosPendentes(pendentes);
        return pendentes;
    };

    // Recalcular período quando data ou escala mudar
    useEffect(() => {
        if (dataPlantao && escalaPlantao) {
            const periodo = calcularPeriodoPlantao(dataPlantao, escalaPlantao);
            setPeriodoInicio(periodo.inicio);
            setPeriodoFim(periodo.fim);

            if (condominioId > 1) {
                buscarRondasDoCondominio(condominioId);
            }
        }
    }, [dataPlantao, escalaPlantao]);

    // Contador regressivo
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (contadorAtivo && contador > 0) {
            interval = setInterval(() => {
                setContador(prev => prev - 1);
            }, 1000);
        } else if (contador === 0) {
            setContadorAtivo(false);
        }
        return () => clearInterval(interval);
    }, [contadorAtivo, contador]);

    return {
        // Estados
        rondas, setRondas,
        residencial, setResidencial,
        inicioRonda, setInicioRonda,
        terminoRonda, setTerminoRonda,
        loading, setLoading,
        rondaAtual, setRondaAtual,
        dataPlantao, setDataPlantao,
        escalaPlantao, setEscalaPlantao,
        condominioId, setCondominioId,
        condominioNome, setCondominioNome,
        rondasExecutadas, setRondasExecutadas,
        loadingRondasExecutadas,
        periodoInicio, periodoFim,
        condominiosPendentes, setCondominiosPendentes,
        rondasSalvas, setRondasSalvas,
        contador, setContador,
        contadorAtivo, setContadorAtivo,

        // Funções
        calcularPeriodoPlantao,
        buscarRondasDoCondominio,
        verificarCondominiosPendentes
    };
}; 