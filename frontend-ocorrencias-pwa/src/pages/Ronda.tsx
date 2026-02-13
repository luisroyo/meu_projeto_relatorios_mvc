import React from 'react';
import { BaseScreen } from '../components/BaseScreen';
import { colors } from '../theme/colors';
import { useRondaState } from '../hooks/useRondaState';
import { useRondaActions } from '../hooks/useRondaActions';
import { RondaConfiguracoes } from '../components/ronda/RondaConfiguracoes';
import { RondaContador } from '../components/ronda/RondaContador';
import { RondaExecutadas } from '../components/ronda/RondaExecutadas';
import { RondaForm } from '../components/ronda/RondaForm';
import { RondaAtual } from '../components/ronda/RondaAtual';
import { RondaLista } from '../components/ronda/RondaLista';
import { RondaAcoes } from '../components/ronda/RondaAcoes';

interface RondaScreenProps {
    token: string;
}

interface Ronda {
    id?: number;
    residencial: string;
    inicio: string;
    termino?: string; // Made optional
    duracao?: number; // Made optional
    status: 'iniciada' | 'finalizada'; // Added status
}

interface Condominio {
    id: number;
    nome: string;
}

interface RondaExecutada {
    id: number;
    data_plantao: string;
    hora_entrada: string;
    hora_saida?: string; // Made optional to match RondaEsporadica
    duracao_minutos?: number; // Made optional
    escala_plantao: string;
    turno: string;
    observacoes?: string;
}

export const RondaScreen: React.FC<RondaScreenProps> = ({ token }) => {
    // Usar hooks customizados para estado e ações
    const {
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
    } = useRondaState(token);

    const {
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
    } = useRondaActions(token);

    // Handlers para ações
    const handleIniciarRonda = () => {
        iniciarRonda(
            residencial,
            inicioRonda,
            setRondaAtual,
            setInicioRonda,
            setContador,
            setContadorAtivo
        );
    };

    const handleFinalizarRonda = () => {
        finalizarRonda(
            rondaAtual,
            terminoRonda,
            setRondas,
            setRondaAtual,
            setTerminoRonda,
            setContadorAtivo
        );
    };

    const handleRemoverRonda = (index: number) => {
        removerRonda(index, setRondas);
    };

    const handleIniciarContador = () => {
        iniciarContador(setContadorAtivo, setContador);
    };

    const handlePararContador = () => {
        pararContador(setContadorAtivo);
    };

    const handleSalvarRondas = async () => {
        await salvarRondas(
            rondas,
            condominioId,
            dataPlantao,
            escalaPlantao,
            setLoading,
            setRondasSalvas,
            setRondas,
            verificarCondominiosPendentes,
            buscarRondasDoCondominio
        );
    };

    const handleEnviarWhatsApp = async () => {
        await enviarWhatsApp(
            rondasExecutadas,
            rondas,
            dataPlantao,
            escalaPlantao,
            verificarCondominiosPendentes
        );
    };

    return (
        <BaseScreen title="Controle de Rondas" subtitle="Registro de rondas esporádicas">
            <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>

                {/* Configurações do Plantão */}
                <RondaConfiguracoes
                    dataPlantao={dataPlantao}
                    setDataPlantao={setDataPlantao}
                    escalaPlantao={escalaPlantao}
                    setEscalaPlantao={setEscalaPlantao}
                    condominioNome={condominioNome}
                    setCondominioNome={setCondominioNome}
                    setCondominioId={setCondominioId}
                    setResidencial={setResidencial}
                    buscarRondasDoCondominio={buscarRondasDoCondominio}
                    periodoInicio={periodoInicio}
                    periodoFim={periodoFim}
                    condominiosPendentes={condominiosPendentes}
                    token={token}
                />

                {/* Rondas Executadas */}
                <RondaExecutadas
                    condominioId={condominioId}
                    condominioNome={condominioNome}
                    rondasExecutadas={rondasExecutadas}
                    loadingRondasExecutadas={loadingRondasExecutadas}
                />

                {/* Formulário de Nova Ronda */}
                <RondaForm
                    condominioNome={condominioNome}
                    setCondominioNome={setCondominioNome}
                    setCondominioId={setCondominioId}
                    setResidencial={setResidencial}
                    buscarRondasDoCondominio={buscarRondasDoCondominio}
                    inicioRonda={inicioRonda}
                    setInicioRonda={setInicioRonda}
                    residencial={residencial}
                    loading={loading}
                    onIniciarRonda={handleIniciarRonda}
                    token={token}
                />

                {/* Ronda Atual */}
                <RondaAtual
                    rondaAtual={rondaAtual}
                    terminoRonda={terminoRonda}
                    setTerminoRonda={setTerminoRonda}
                    loading={loading}
                    onFinalizarRonda={handleFinalizarRonda}
                />

                {/* Contador Regressivo */}
                <RondaContador
                    contador={contador}
                    contadorAtivo={contadorAtivo}
                    onIniciar={handleIniciarContador}
                    onParar={handlePararContador}
                    formatarTempo={formatarTempo}
                />

                {/* Lista de Rondas */}
                <RondaLista
                    rondas={rondas}
                    onRemoverRonda={handleRemoverRonda}
                />

                {/* Botões de Ação */}
                <RondaAcoes
                    rondas={rondas}
                    loading={loading}
                    onSalvarRondas={handleSalvarRondas}
                    onEnviarWhatsApp={handleEnviarWhatsApp}
                />
            </div>
        </BaseScreen>
    );
}; 