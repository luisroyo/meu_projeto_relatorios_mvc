import { salvarRondaCompleta } from '../services/domains/rondasEsporadicas';

// Interfaces baseadas na estrutura domains/
interface Ronda {
    id?: number;
    residencial: string;
    inicio: string;
    termino?: string;
    duracao?: number;
    status: 'iniciada' | 'finalizada';
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

export const useRondaActions = (token: string) => {
    // Funções utilitárias
    const formatarTempo = (segundos: number): string => {
        const minutos = Math.floor(segundos / 60);
        const segs = segundos % 60;
        return `${minutos.toString().padStart(2, '0')}:${segs.toString().padStart(2, '0')}`;
    };

    const calcularDuracao = (inicio: string, termino: string): number => {
        const [horaInicio, minInicio] = inicio.split(':').map(Number);
        const [horaTermino, minTermino] = termino.split(':').map(Number);

        let minutosInicio = horaInicio * 60 + minInicio;
        let minutosTermino = horaTermino * 60 + minTermino;

        // Se o término for menor que o início, significa que passou da meia-noite
        if (minutosTermino < minutosInicio) {
            minutosTermino += 24 * 60; // Adiciona 24 horas
        }

        return minutosTermino - minutosInicio;
    };

    // Função inteligente para enviar WhatsApp
    const enviarWhatsAppInteligente = async (rondasParaEnviar: Ronda[], dataPlantao: string, escalaPlantao: string) => {
        if (rondasParaEnviar.length === 0) {
            alert('Nenhuma ronda para enviar!');
            return;
        }

        // Calcular período do plantão
        const dataPlantaoObj = new Date(dataPlantao + 'T00:00:00');
        let inicio, fim;

        if (escalaPlantao === '18 às 06') {
            inicio = new Date(dataPlantaoObj);
            inicio.setHours(18, 0, 0, 0);

            fim = new Date(dataPlantaoObj);
            fim.setDate(fim.getDate() + 1);
            fim.setHours(6, 0, 0, 0);
        } else {
            inicio = new Date(dataPlantaoObj);
            inicio.setHours(6, 0, 0, 0);

            fim = new Date(dataPlantaoObj);
            fim.setHours(18, 0, 0, 0);
        }

        let mensagem = `Plantão ${dataPlantao} (${escalaPlantao})\n`;
        mensagem += `Período: ${inicio.toLocaleString('pt-BR')} - ${fim.toLocaleString('pt-BR')}\n\n`;

        rondasParaEnviar.forEach((ronda, index) => {
            mensagem += `${index + 1}. ${ronda.residencial}\n`;
            mensagem += `   Início: ${ronda.inicio} - Fim: ${ronda.termino || 'Em andamento'}\n`;
            if (ronda.duracao) {
                mensagem += `   Duração: ${ronda.duracao} minutos\n`;
            }
            mensagem += '\n';
        });

        mensagem += `✅ Total: ${rondasParaEnviar.length} rondas no plantão`;

        // Tentar enviar para WhatsApp Mobile primeiro
        try {
            if (navigator.share) {
                await navigator.share({
                    title: 'Relatório de Rondas',
                    text: mensagem
                });
                alert('Relatório enviado via WhatsApp Mobile!');
            } else {
                // Fallback para WhatsApp Web
                const url = `https://wa.me/?text=${encodeURIComponent(mensagem)}`;
                window.open(url, '_blank');
                alert('Relatório aberto no WhatsApp Web!');
            }
        } catch (error) {
            console.error('Erro ao enviar WhatsApp:', error);
            alert('Erro ao enviar WhatsApp!');
        }
    };

    // Ações de ronda
    const iniciarRonda = (
        residencial: string,
        inicioRonda: string,
        setRondaAtual: (ronda: Ronda | null) => void,
        setInicioRonda: (valor: string) => void,
        setContador: (valor: number) => void,
        setContadorAtivo: (valor: boolean) => void
    ) => {
        if (!residencial || !inicioRonda) {
            alert('Preencha o residencial e horário de início!');
            return false;
        }

        const novaRonda: Ronda = {
            residencial,
            inicio: inicioRonda,
            status: 'iniciada'
        };

        setRondaAtual(novaRonda);
        setInicioRonda('');
        setContador(1200); // Reset do contador
        setContadorAtivo(true);

        alert('Ronda iniciada! Agora você pode finalizar quando terminar.');
        return true;
    };

    const finalizarRonda = (
        rondaAtual: Ronda | null,
        terminoRonda: string,
        setRondas: React.Dispatch<React.SetStateAction<Ronda[]>>,
        setRondaAtual: (ronda: Ronda | null) => void,
        setTerminoRonda: (valor: string) => void,
        setContadorAtivo: (valor: boolean) => void
    ) => {
        if (!rondaAtual || !terminoRonda) {
            alert('Preencha o horário de término!');
            return false;
        }

        const duracao = calcularDuracao(rondaAtual.inicio, terminoRonda);

        if (duracao <= 0) {
            alert('O horário de término deve ser posterior ao início!');
            return false;
        }

        const rondaFinalizada: Ronda = {
            ...rondaAtual,
            termino: terminoRonda,
            duracao,
            status: 'finalizada'
        };

        setRondas(prev => [...prev, rondaFinalizada]);
        setRondaAtual(null);
        setTerminoRonda('');
        setContadorAtivo(false);

        alert('Ronda finalizada e adicionada à lista!');
        return true;
    };

    const removerRonda = (
        index: number,
        setRondas: React.Dispatch<React.SetStateAction<Ronda[]>>
    ) => {
        setRondas(prev => prev.filter((_, i) => i !== index));
    };

    // Ações do contador
    const iniciarContador = (
        setContadorAtivo: (valor: boolean) => void,
        setContador: (valor: number) => void
    ) => {
        setContadorAtivo(true);
        setContador(1200); // 20 minutos
    };

    const pararContador = (setContadorAtivo: (valor: boolean) => void) => {
        setContadorAtivo(false);
    };

    // Salvar rondas
    const salvarRondas = async (
        rondas: Ronda[],
        condominioId: number,
        dataPlantao: string,
        escalaPlantao: string,
        setLoading: (valor: boolean) => void,
        setRondasSalvas: React.Dispatch<React.SetStateAction<Ronda[]>>,
        setRondas: React.Dispatch<React.SetStateAction<Ronda[]>>,
        verificarCondominiosPendentes: () => string[],
        buscarRondasDoCondominio: (id: number) => Promise<void>
    ) => {
        if (rondas.length === 0) {
            alert('Adicione pelo menos uma ronda!');
            return false;
        }

        setLoading(true);
        try {
            console.log('💾 DEBUG - Salvando rondas:', {
                totalRondas: rondas.length,
                condominioId,
                dataPlantao,
                escalaPlantao,
                rondas: rondas
            });

            // Salvar cada ronda como esporádica completa
            for (const ronda of rondas) {
                if (ronda.termino && ronda.duracao) {
                    const dadosRonda = {
                        condominio_id: condominioId,
                        user_id: 1,
                        data_plantao: dataPlantao,
                        hora_entrada: ronda.inicio,
                        hora_saida: ronda.termino,
                        escala_plantao: escalaPlantao,
                        turno: escalaPlantao === "18 às 06" ? "Noite" : "Dia",
                        observacoes: `Ronda no residencial ${ronda.residencial}`
                    };

                    console.log('💾 DEBUG - Salvando ronda:', dadosRonda);

                    const resultado = await salvarRondaCompleta(token, dadosRonda);
                    console.log('✅ DEBUG - Ronda salva:', resultado);
                }
            }

            // Adicionar às rondas salvas
            setRondasSalvas(prev => [...prev, ...rondas]);

            alert('Rondas salvas com sucesso!');
            setRondas([]);

            // Verificar condomínios pendentes
            verificarCondominiosPendentes();

            // Buscar rondas executadas novamente para atualizar a lista
            if (condominioId > 1) {
                console.log('🔄 DEBUG - Buscando rondas executadas após salvar...');
                await buscarRondasDoCondominio(condominioId);
            }

            return true;
        } catch (error) {
            console.error('🚨 DEBUG - Erro ao salvar rondas:', error);
            alert('Erro ao salvar rondas!');
            return false;
        } finally {
            setLoading(false);
        }
    };

    // Enviar WhatsApp
    const enviarWhatsApp = async (
        rondasExecutadas: RondaExecutada[],
        rondas: Ronda[],
        dataPlantao: string,
        escalaPlantao: string,
        verificarCondominiosPendentes: () => string[]
    ) => {
        // Enviar rondas esporádicas já salvas primeiro
        if (rondasExecutadas.length > 0) {
            await enviarWhatsAppInteligente(rondasExecutadas.map(r => ({
                id: r.id,
                residencial: r.observacoes || 'Condomínio',
                inicio: r.hora_entrada,
                termino: r.hora_saida,
                duracao: r.duracao_minutos,
                status: 'finalizada' as const
            })), dataPlantao, escalaPlantao);
        }

        // Depois enviar rondas atuais se houver
        if (rondas.length > 0) {
            await enviarWhatsAppInteligente(rondas, dataPlantao, escalaPlantao);
        }

        // Verificar condomínios pendentes
        verificarCondominiosPendentes();
    };

    return {
        // Funções utilitárias
        formatarTempo,
        calcularDuracao,
        enviarWhatsAppInteligente,

        // Ações de ronda
        iniciarRonda,
        finalizarRonda,
        removerRonda,

        // Ações do contador
        iniciarContador,
        pararContador,

        // Ações de persistência
        salvarRondas,
        enviarWhatsApp
    };
}; 