import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BaseScreen } from '../components/BaseScreen';
import { Button } from '../components/Button';
import { colors } from '../theme/colors';
import { buscarDetalhesOcorrencia, Ocorrencia } from '../services/ocorrencias';

interface OcorrenciaDetailScreenProps {
    token?: string;
}

export const OcorrenciaDetailScreen: React.FC<OcorrenciaDetailScreenProps> = ({ token }) => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [ocorrencia, setOcorrencia] = useState<Ocorrencia | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const carregarOcorrencia = async () => {
            if (!id) {
                setError('ID da ocorrência não fornecido');
                setLoading(false);
                return;
            }

            try {
                const ocorrenciaId = parseInt(id);
                const detalhes = await buscarDetalhesOcorrencia(token!, ocorrenciaId);

                if (detalhes) {
                    setOcorrencia(detalhes);
                } else {
                    setError('Ocorrência não encontrada');
                }
            } catch (error) {
                console.error('Erro ao carregar ocorrência:', error);
                setError('Erro ao carregar detalhes da ocorrência');
            } finally {
                setLoading(false);
            }
        };

        carregarOcorrencia();
    }, [id, token]);

    const formatarData = (dataString?: string) => {
        if (!dataString) return 'N/A';
        try {
            const data = new Date(dataString);
            return data.toLocaleDateString('pt-BR') + ' ' + data.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
        } catch {
            return dataString;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'pendente':
                return colors.warning;
            case 'aprovado':
                return colors.success;
            case 'rejeitado':
                return colors.danger;
            default:
                return colors.mutedText;
        }
    };

    const handleVoltar = () => {
        navigate('/ocorrencias');
    };

    const handleCopiar = () => {
        const relatorio = ocorrencia?.relatorio_final || ocorrencia?.descricao;
        if (relatorio) {
            navigator.clipboard.writeText(relatorio);
            alert('Relatório copiado para a área de transferência!');
        }
    };

    const handleEnviarWhatsApp = () => {
        const relatorio = ocorrencia?.relatorio_final || ocorrencia?.descricao;
        if (relatorio) {
            const whatsappUrl = `https://wa.me/?text=${encodeURIComponent(relatorio)}`;
            window.open(whatsappUrl, '_blank');
        }
    };

    if (loading) {
        return (
            <BaseScreen title="Carregando..." subtitle="Aguarde um momento">
                <div style={{ padding: '20px', textAlign: 'center' }}>
                    <span>⏳ Carregando detalhes da ocorrência...</span>
                </div>
            </BaseScreen>
        );
    }

    if (error) {
        return (
            <BaseScreen title="Erro" subtitle="Não foi possível carregar a ocorrência">
                <div style={{ padding: '20px', textAlign: 'center' }}>
                    <p style={{ color: colors.danger, marginBottom: '20px' }}>{error}</p>
                    <Button
                        title="Voltar"
                        onClick={handleVoltar}
                        variant="secondary"
                        style={{ minWidth: '120px' }}
                    />
                </div>
            </BaseScreen>
        );
    }

    if (!ocorrencia) {
        return (
            <BaseScreen title="Ocorrência não encontrada" subtitle="Verifique o ID fornecido">
                <div style={{ padding: '20px', textAlign: 'center' }}>
                    <p style={{ color: colors.mutedText, marginBottom: '20px' }}>
                        A ocorrência solicitada não foi encontrada.
                    </p>
                    <Button
                        title="Voltar"
                        onClick={handleVoltar}
                        variant="secondary"
                        style={{ minWidth: '120px' }}
                    />
                </div>
            </BaseScreen>
        );
    }

    return (
        <BaseScreen title={`Ocorrência #${ocorrencia.id}`} subtitle="Detalhes completos da ocorrência">
            <div style={{ padding: '20px' }}>
                {/* Header com status */}
                <div style={{
                    backgroundColor: '#fff',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '20px',
                    border: '1px solid #e9ecef',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                        <div>
                            <h2 style={{ margin: '0 0 8px 0', color: colors.headingText }}>
                                Ocorrência #{ocorrencia.id}
                            </h2>
                            <p style={{ margin: '0', color: colors.mutedText, fontSize: '14px' }}>
                                {formatarData(ocorrencia.data_hora_ocorrencia)}
                            </p>
                        </div>
                        <span style={{
                            backgroundColor: getStatusColor(ocorrencia.status),
                            color: '#fff',
                            padding: '8px 16px',
                            borderRadius: '20px',
                            fontSize: '14px',
                            fontWeight: 'bold'
                        }}>
                            {ocorrencia.status}
                        </span>
                    </div>

                    {/* Informações básicas */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
                        <div>
                            <p style={{ margin: '0 0 4px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                📍 Local:
                            </p>
                            <p style={{ margin: '0', color: colors.mutedText }}>
                                {ocorrencia.endereco_especifico || ocorrencia.endereco || 'N/A'}
                            </p>
                        </div>

                        <div>
                            <p style={{ margin: '0 0 4px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                🏢 Condomínio:
                            </p>
                            <p style={{ margin: '0', color: colors.mutedText }}>
                                {ocorrencia.condominio?.nome || 'N/A'}
                            </p>
                        </div>

                        <div>
                            <p style={{ margin: '0 0 4px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                📋 Tipo:
                            </p>
                            <p style={{ margin: '0', color: colors.mutedText }}>
                                {ocorrencia.tipo?.nome || 'N/A'}
                            </p>
                        </div>

                        <div>
                            <p style={{ margin: '0 0 4px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                🕐 Turno:
                            </p>
                            <p style={{ margin: '0', color: colors.mutedText }}>
                                {ocorrencia.turno || 'N/A'}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Colaboradores e Órgãos */}
                {((ocorrencia.colaboradores && ocorrencia.colaboradores.length > 0) || (ocorrencia.orgaos_acionados && ocorrencia.orgaos_acionados.length > 0)) && (
                    <div style={{
                        backgroundColor: '#fff',
                        borderRadius: '12px',
                        padding: '20px',
                        marginBottom: '20px',
                        border: '1px solid #e9ecef',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                    }}>
                        <h3 style={{ marginBottom: '16px', color: colors.headingText }}>
                            👥 Envolvidos
                        </h3>

                        {ocorrencia.colaboradores && ocorrencia.colaboradores.length > 0 && (
                            <div style={{ marginBottom: '16px' }}>
                                <p style={{ margin: '0 0 8px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                    Colaboradores:
                                </p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                    {ocorrencia.colaboradores.map((colaborador, index) => (
                                        <span key={index} style={{
                                            backgroundColor: colors.secondaryBg,
                                            color: colors.mainText,
                                            padding: '4px 12px',
                                            borderRadius: '16px',
                                            fontSize: '12px'
                                        }}>
                                            {colaborador.nome}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {ocorrencia.orgaos_acionados && ocorrencia.orgaos_acionados.length > 0 && (
                            <div>
                                <p style={{ margin: '0 0 8px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                    Órgãos Acionados:
                                </p>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                                    {ocorrencia.orgaos_acionados.map((orgao, index) => (
                                        <span key={index} style={{
                                            backgroundColor: colors.danger,
                                            color: '#fff',
                                            padding: '4px 12px',
                                            borderRadius: '16px',
                                            fontSize: '12px'
                                        }}>
                                            {orgao.nome}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Relatório */}
                <div style={{
                    backgroundColor: '#fff',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '20px',
                    border: '1px solid #e9ecef',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                    <h3 style={{ marginBottom: '16px', color: colors.headingText }}>
                        📄 Relatório Completo
                    </h3>
                    <pre style={{
                        color: '#333',
                        fontSize: '14px',
                        lineHeight: '20px',
                        fontFamily: 'inherit',
                        whiteSpace: 'pre-line',
                        margin: 0,
                        backgroundColor: '#f8f9fa',
                        padding: '16px',
                        borderRadius: '8px',
                        border: '1px solid #dee2e6',
                        maxHeight: '400px',
                        overflowY: 'auto'
                    }}>
                        {ocorrencia.relatorio_final || ocorrencia.descricao || 'Nenhum relatório disponível'}
                    </pre>
                </div>

                {/* Metadados */}
                <div style={{
                    backgroundColor: '#fff',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '20px',
                    border: '1px solid #e9ecef',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}>
                    <h3 style={{ marginBottom: '16px', color: colors.headingText }}>
                        📊 Metadados
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                        <div>
                            <p style={{ margin: '0 0 4px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                Data de Criação:
                            </p>
                            <p style={{ margin: '0', color: colors.mutedText, fontSize: '14px' }}>
                                {formatarData(ocorrencia.data_criacao)}
                            </p>
                        </div>
                        <div>
                            <p style={{ margin: '0 0 4px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                Última Modificação:
                            </p>
                            <p style={{ margin: '0', color: colors.mutedText, fontSize: '14px' }}>
                                {formatarData(ocorrencia.data_modificacao)}
                            </p>
                        </div>
                        {ocorrencia.supervisor && (
                            <div>
                                <p style={{ margin: '0 0 4px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                    Supervisor:
                                </p>
                                <p style={{ margin: '0', color: colors.mutedText, fontSize: '14px' }}>
                                    {ocorrencia.supervisor?.username || 'N/A'}
                                </p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Ações */}
                <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                    <Button
                        title="⬅️ Voltar"
                        onClick={handleVoltar}
                        variant="secondary"
                        style={{ minWidth: '120px' }}
                    />
                    <Button
                        title="📋 Copiar Relatório"
                        onClick={handleCopiar}
                        variant="success"
                        style={{ minWidth: '150px' }}
                    />
                    <Button
                        title="📱 Enviar WhatsApp"
                        onClick={handleEnviarWhatsApp}
                        variant="success"
                        style={{ minWidth: '150px' }}
                    />
                </div>
            </div>
        </BaseScreen>
    );
}; 