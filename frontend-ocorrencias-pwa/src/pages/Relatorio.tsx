import React, { useState, useEffect, useRef } from 'react';
import { Input } from '../components/Input';
import { Button } from '../components/Button';
import { AnimatedInput } from '../components/AnimatedInput';
import { BaseScreen } from '../components/BaseScreen';
import { AutoComplete } from '../components/AutoComplete';
import { colors } from '../theme/colors';
import { analisarRelatorio } from '../services/relatorios';
import { listarColaboradores, buscarColaboradores } from '../services/domains/colaboradores';
import { buscarEnderecos } from '../services/enderecos';

interface RelatorioScreenProps {
    token?: string;
    onRelatorioCorrigido?: (relatorio: string) => void;
}

export const RelatorioScreen: React.FC<RelatorioScreenProps> = ({ token, onRelatorioCorrigido }) => {
    const [data, setData] = useState<string>('');
    const [hora, setHora] = useState<string>('');
    const [endereco, setEndereco] = useState('');
    const [colaborador, setColaborador] = useState('');
    const [relatorioBruto, setRelatorioBruto] = useState('');
    const [relatorioLimpo, setRelatorioLimpo] = useState('');
    const [loading, setLoading] = useState(false);
    const [vtr, setVtr] = useState('');
    const [selectedColaborador, setSelectedColaborador] = useState<any>(null);
    const [selectedEndereco, setSelectedEndereco] = useState<any>(null);

    // Funções de busca para autocompletar
    const buscarColaboradoresAutocomplete = async (query: string): Promise<any[]> => {
        try {
            const response = await buscarColaboradores(query, token);
            return response.colaboradores || [];
        } catch (error) {
            console.error('Erro ao buscar colaboradores:', error);
            return [];
        }
    };

    const buscarEnderecosAutocomplete = async (query: string): Promise<any[]> => {
        try {
            const response = await buscarEnderecos(query, token);
            return response.enderecos || [];
        } catch (error) {
            console.error('Erro ao buscar endereços:', error);
            return [];
        }
    };

    const vtrOptions = [
        '',
        'VTR 03',
        'VTR 04',
        'VTR 05',
        'VTR 06',
        'VTR 07',
        'VTR 08',
        'VTR 09',
        'VTR 10',
        'VTR 11',
    ];

    const FORM_KEY = 'relatorio_form_state_v1';

    // Carregar estado salvo ao montar
    useEffect(() => {
        try {
            const saved = localStorage.getItem(FORM_KEY);
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed.data) setData(parsed.data);
                if (parsed.hora) setHora(parsed.hora);
                if (parsed.endereco) setEndereco(parsed.endereco);
                if (parsed.colaborador) setColaborador(parsed.colaborador);
                if (parsed.relatorioBruto) setRelatorioBruto(parsed.relatorioBruto);
                if (parsed.vtr) setVtr(parsed.vtr);
            }
        } catch (error) {
            console.error('Erro ao carregar dados salvos:', error);
        }
    }, []);

    // Salvar estado sempre que algum campo mudar
    useEffect(() => {
        const timeout = setTimeout(() => {
            localStorage.setItem(
                FORM_KEY,
                JSON.stringify({
                    data,
                    hora,
                    endereco,
                    colaborador,
                    relatorioBruto,
                    vtr,
                })
            );
        }, 400);
        return () => clearTimeout(timeout);
    }, [data, hora, endereco, colaborador, relatorioBruto, vtr]);

    // Função para limpar formulário
    const handleLimparFormulario = () => {
        setData('');
        setHora('');
        setEndereco('');
        setColaborador('');
        setRelatorioBruto('');
        setRelatorioLimpo('');
        setVtr('');
        localStorage.removeItem(FORM_KEY);
        alert('Formulário limpo com sucesso!');
    };

    // Função para aplicar o template ao relatório processado
    const aplicarTemplate = (relatorioProcessado: string) => {
        // Se o relatório já está no formato do template, retorna como está
        if (relatorioProcessado.includes('Data:') && relatorioProcessado.includes('Hora:')) {
            return relatorioProcessado;
        }

        // Caso contrário, aplica o template básico
        const dataAtual = data || '[Preencher data]';
        const horaAtual = hora || '[Preencher hora]';
        const enderecoAtual = endereco || '[Preencher endereço]';

        return `Data: ${dataAtual}
Hora: ${horaAtual}
Local: ${enderecoAtual}

Ocorrência: [Resumo da ocorrência]

Relato:
${relatorioProcessado}

Ações Realizadas:
- [Listar ações realizadas]

Acionamentos:
( ) Central ( ) Apoio 90 ( ) Polícia Militar ( ) Supervisor ( ) Coordenador

Envolvidos/Testemunhas:
[Informações dos envolvidos]

Veículo (envolvido na ocorrência):
[Descrição do veículo]

Responsável pelo registro: [Nome do agente]`;
    };

    const handleAnalisar = async () => {
        if (!relatorioBruto.trim()) {
            alert('Cole ou digite o relatório bruto.');
            return;
        }

        // Verificar se o usuário colou o prompt de instruções por engano
        if (relatorioBruto.includes('PROMPT PARA CORRIGIR RELATÓRIOS DE OCORRÊNCIA:')) {
            alert('Você colou o prompt de instruções. Por favor, cole apenas o relatório bruto original.');
            return;
        }

        // Monta o texto com os campos preenchidos acima do relatório bruto
        const textoMontado = `
Data: ${data || '[Preencher data]'}
Hora: ${hora || '[Preencher hora]'}
Colaborador: ${colaborador || '[Preencher colaborador]'}
Endereço: ${endereco || '[Preencher endereço]'}
Viatura/VTR: ${vtr || '[Preencher viatura]'}
\n${relatorioBruto}`;

        setLoading(true);
        try {
            console.log('Token sendo usado:', token ? 'Presente' : 'Ausente');
            console.log('Texto sendo enviado:', textoMontado.substring(0, 200) + '...');
            const response = await analisarRelatorio(token!, textoMontado);
            if (response?.sucesso && response.dados) {
                const relatorioCorrigido = response.dados.relatorio_corrigido || response.dados.relatorio || response.relatorio_corrigido || response.relatorio;
                if (relatorioCorrigido) {
                    // Aplicar template ao relatório processado
                    const relatorioComTemplate = aplicarTemplate(relatorioCorrigido);
                    setRelatorioLimpo(relatorioComTemplate);
                    if (onRelatorioCorrigido) {
                        onRelatorioCorrigido(relatorioComTemplate);
                    }
                } else {
                    setRelatorioLimpo(JSON.stringify(response.dados, null, 2));
                }

                const { data_hora_ocorrencia, endereco_especifico, colaboradores_envolvidos } = response.dados;
                if (data_hora_ocorrencia) {
                    const [d, h] = data_hora_ocorrencia.split('T');
                    const [ano, mes, dia] = d.split('-');
                    const [horaStr, minStr] = h.split(':');
                    setData(`${dia}/${mes}/${ano}`);
                    setHora(`${horaStr}:${minStr}`);
                }
                if (endereco_especifico) setEndereco(endereco_especifico);
                if (colaboradores_envolvidos?.length > 0) setColaborador(colaboradores_envolvidos[0]);
            } else {
                alert(response.message || 'Não foi possível analisar o relatório.');
            }
        } catch (e: any) {
            alert(e.message || 'Erro ao analisar relatório.');
        } finally {
            setLoading(false);
        }
    };

    // Limpar estado salvo ao enviar via WhatsApp
    const handleEnviarWhatsApp = () => {
        if (!relatorioLimpo) {
            alert('Gere o relatório limpo antes de enviar.');
            return;
        }

        // Tenta primeiro o esquema nativo do WhatsApp
        const whatsappNativeUrl = `whatsapp://send?text=${encodeURIComponent(relatorioLimpo)}`;
        const whatsappWebUrl = `https://wa.me/?text=${encodeURIComponent(relatorioLimpo)}`;

        // Verifica se o esquema nativo está disponível
        const link = document.createElement('a');
        link.href = whatsappNativeUrl;

        // Tenta abrir o esquema nativo
        try {
            window.location.href = whatsappNativeUrl;
        } catch (error) {
            // Se falhar, abre o link web
            window.open(whatsappWebUrl, '_blank');
        }
    };

    const handleCopiar = () => {
        navigator.clipboard.writeText(relatorioLimpo);
        alert('Relatório limpo copiado para a área de transferência.');
    };

    return (
        <BaseScreen title="Relatório de Ocorrência" subtitle="Preencha os dados abaixo">
            <div style={{ padding: '20px' }}>
                <div style={{ marginBottom: '20px' }}>
                    {/* Data */}
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: colors.headingText }}>
                            📅 Data
                        </label>
                        <input
                            type="date"
                            value={data}
                            onChange={(e) => setData(e.target.value)}
                            style={{
                                backgroundColor: '#F9F9F9',
                                color: '#333',
                                fontSize: '16px',
                                borderRadius: '10px',
                                padding: '12px 15px',
                                border: '1px solid #E0E0E0',
                                width: '100%',
                                boxSizing: 'border-box',
                                height: '48px'
                            }}
                        />
                    </div>

                    {/* Hora */}
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: colors.headingText }}>
                            🕐 Hora
                        </label>
                        <input
                            type="time"
                            value={hora}
                            onChange={(e) => setHora(e.target.value)}
                            style={{
                                backgroundColor: '#F9F9F9',
                                color: '#333',
                                fontSize: '16px',
                                borderRadius: '10px',
                                padding: '12px 15px',
                                border: '1px solid #E0E0E0',
                                width: '100%',
                                boxSizing: 'border-box',
                                height: '48px'
                            }}
                        />
                    </div>

                    {/* Endereço */}
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: colors.headingText }}>
                            📍 Endereço
                        </label>
                        <AutoComplete
                            placeholder="Digite para buscar endereços..."
                            value={endereco}
                            onChange={setEndereco}
                            onSelect={(item) => {
                                setSelectedEndereco(item);
                                setEndereco(item.nome || '');
                            }}
                            searchFunction={buscarEnderecosAutocomplete}
                            displayField="nome"
                            token={token}
                            style={{
                                backgroundColor: '#F9F9F9',
                                color: '#333',
                                fontSize: '16px',
                                borderRadius: '10px',
                                padding: '12px 15px',
                                border: '1px solid #E0E0E0',
                                width: '100%',
                                boxSizing: 'border-box'
                            }}
                        />
                    </div>

                    {/* Colaborador */}
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: colors.headingText }}>
                            👤 Colaborador/Responsável
                        </label>
                        <AutoComplete
                            placeholder="Digite para buscar colaboradores..."
                            value={colaborador}
                            onChange={setColaborador}
                            onSelect={(item) => {
                                setSelectedColaborador(item);
                                setColaborador(item.nome_completo || '');
                            }}
                            searchFunction={buscarColaboradoresAutocomplete}
                            displayField="nome_completo"
                            token={token}
                            style={{
                                backgroundColor: '#F9F9F9',
                                color: '#333',
                                fontSize: '16px',
                                borderRadius: '10px',
                                padding: '12px 15px',
                                border: '1px solid #E0E0E0',
                                width: '100%',
                                boxSizing: 'border-box'
                            }}
                        />
                    </div>

                    {/* VTR */}
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: colors.headingText }}>
                            🚗 Viatura/VTR
                        </label>
                        <select
                            value={vtr}
                            onChange={(e) => setVtr(e.target.value)}
                            style={{
                                backgroundColor: '#F9F9F9',
                                color: '#333',
                                fontSize: '16px',
                                borderRadius: '10px',
                                padding: '12px 15px',
                                border: '1px solid #E0E0E0',
                                width: '100%',
                                boxSizing: 'border-box',
                                height: '48px'
                            }}
                        >
                            {vtrOptions.map(opt => (
                                <option key={opt} value={opt}>
                                    {opt || 'Selecione'}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Relatório Bruto */}
                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: colors.headingText }}>
                            📄 Relatório Bruto
                        </label>
                        <textarea
                            placeholder="Cole aqui APENAS o relatório bruto original (não cole o prompt de instruções)..."
                            value={relatorioBruto}
                            onChange={(e) => setRelatorioBruto(e.target.value)}
                            style={{
                                backgroundColor: '#F9F9F9',
                                color: '#333',
                                fontSize: '16px',
                                borderRadius: '10px',
                                padding: '12px 15px',
                                border: '1px solid #E0E0E0',
                                width: '100%',
                                boxSizing: 'border-box',
                                minHeight: '120px',
                                resize: 'vertical',
                                fontFamily: 'inherit'
                            }}
                        />
                    </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                        <Button
                            title={loading ? 'Analisando...' : 'Analisar Relatório'}
                            onClick={handleAnalisar}
                            disabled={loading}
                            style={{
                                backgroundColor: colors.danger,
                                flex: 1,
                                minWidth: '200px'
                            }}
                        />
                        <Button
                            title="Limpar Formulário"
                            onClick={handleLimparFormulario}
                            variant="secondary"
                            style={{
                                flex: 1,
                                minWidth: '200px'
                            }}
                        />
                    </div>
                    {loading && (
                        <div style={{ textAlign: 'center', marginTop: '10px' }}>
                            <span>⏳ Analisando...</span>
                        </div>
                    )}
                </div>

                {relatorioLimpo && (
                    <div style={{
                        backgroundColor: '#f8f9fa',
                        borderRadius: '12px',
                        padding: '20px',
                        border: '1px solid #e9ecef'
                    }}>
                        <h3 style={{ marginBottom: '16px', color: colors.headingText }}>
                            📋 Relatório Limpo
                        </h3>
                        <pre style={{
                            color: '#333',
                            fontSize: '16px',
                            lineHeight: '22px',
                            fontFamily: 'inherit',
                            whiteSpace: 'pre-line',
                            margin: 0,
                            backgroundColor: '#fff',
                            padding: '16px',
                            borderRadius: '8px',
                            border: '1px solid #dee2e6'
                        }}>
                            {relatorioLimpo}
                        </pre>
                        <div style={{ display: 'flex', gap: '10px', marginTop: '16px', flexWrap: 'wrap' }}>
                            <Button
                                title="📋 Copiar Relatório"
                                onClick={handleCopiar}
                                variant="success"
                                style={{ flex: 1, minWidth: '150px' }}
                            />
                            <Button
                                title="📱 Enviar via WhatsApp"
                                onClick={handleEnviarWhatsApp}
                                variant="success"
                                style={{ flex: 1, minWidth: '150px' }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </BaseScreen>
    );
}; 