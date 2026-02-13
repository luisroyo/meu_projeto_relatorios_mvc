import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BaseScreen } from '../components/BaseScreen';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { colors } from '../theme/colors';
import { buscarHistoricoOcorrencias, Ocorrencia, FiltrosOcorrencia } from '../services/ocorrencias';

interface OcorrenciasListScreenProps {
    token?: string;
}

export const OcorrenciasListScreen: React.FC<OcorrenciasListScreenProps> = ({ token }) => {
    const navigate = useNavigate();
    const [ocorrencias, setOcorrencias] = useState<Ocorrencia[]>([]);
    const [loading, setLoading] = useState(false);
    const [filtros, setFiltros] = useState<FiltrosOcorrencia>({});
    const [dataInicio, setDataInicio] = useState('');
    const [dataFim, setDataFim] = useState('');

    const carregarOcorrencias = async () => {
        if (!token) {
            console.error('Token não fornecido');
            return;
        }

        setLoading(true);
        try {
            console.log('Token sendo usado:', token ? 'Presente' : 'Ausente');

            const filtrosCompletos = {
                ...filtros,
                data_inicio: dataInicio || undefined,
                data_fim: dataFim || undefined,
            };

            const response = await buscarHistoricoOcorrencias(token, filtrosCompletos);
            if (response.historico) {
                setOcorrencias(response.historico);
            } else {
                console.error('Erro ao carregar ocorrências:', response.error);
            }
        } catch (error) {
            console.error('Erro ao carregar ocorrências:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        carregarOcorrencias();
    }, []);

    const handleFiltrar = () => {
        carregarOcorrencias();
    };

    const handleLimparFiltros = () => {
        setFiltros({});
        setDataInicio('');
        setDataFim('');
        carregarOcorrencias();
    };

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

    return (
        <BaseScreen title="Histórico de Ocorrências" subtitle="Visualize todas as ocorrências registradas">
            <div style={{ padding: '20px' }}>
                {/* Filtros */}
                <div style={{
                    backgroundColor: '#f8f9fa',
                    borderRadius: '12px',
                    padding: '20px',
                    marginBottom: '20px',
                    border: '1px solid #e9ecef'
                }}>
                    <h3 style={{ marginBottom: '16px', color: colors.headingText }}>
                        🔍 Filtros
                    </h3>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                        <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: colors.headingText }}>
                                Status
                            </label>
                            <select
                                value={filtros.status || ''}
                                onChange={(e) => setFiltros({ ...filtros, status: e.target.value || undefined })}
                                style={{
                                    backgroundColor: '#fff',
                                    color: colors.headingText,
                                    fontSize: '16px',
                                    borderRadius: '8px',
                                    padding: '8px 12px',
                                    border: '1px solid #dee2e6',
                                    width: '100%'
                                }}
                            >
                                <option value="">Todos</option>
                                <option value="Pendente">Pendente</option>
                                <option value="Aprovado">Aprovado</option>
                                <option value="Rejeitado">Rejeitado</option>
                            </select>
                        </div>

                        <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: colors.headingText }}>
                                Data Início
                            </label>
                            <Input
                                type="date"
                                value={dataInicio}
                                onChange={(e) => setDataInicio(e.target.value)}
                                style={{
                                    backgroundColor: '#fff',
                                    color: colors.headingText,
                                    fontSize: '16px',
                                    borderRadius: '8px',
                                    padding: '8px 12px',
                                    border: '1px solid #dee2e6',
                                    width: '100%'
                                }}
                            />
                        </div>

                        <div>
                            <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold', color: colors.headingText }}>
                                Data Fim
                            </label>
                            <Input
                                type="date"
                                value={dataFim}
                                onChange={(e) => setDataFim(e.target.value)}
                                style={{
                                    backgroundColor: '#fff',
                                    color: colors.headingText,
                                    fontSize: '16px',
                                    borderRadius: '8px',
                                    padding: '8px 12px',
                                    border: '1px solid #dee2e6',
                                    width: '100%'
                                }}
                            />
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                        <Button
                            title="🔍 Filtrar"
                            onClick={handleFiltrar}
                            disabled={loading}
                            style={{
                                backgroundColor: colors.danger,
                                minWidth: '120px'
                            }}
                        />
                        <Button
                            title="🧹 Limpar"
                            onClick={handleLimparFiltros}
                            variant="secondary"
                            style={{
                                minWidth: '120px'
                            }}
                        />
                    </div>
                </div>

                {/* Lista de Ocorrências */}
                <div>
                    <h3 style={{ marginBottom: '16px', color: colors.headingText }}>
                        📋 Ocorrências ({ocorrencias.length})
                    </h3>

                    {loading && (
                        <div style={{ textAlign: 'center', padding: '40px' }}>
                            <span>⏳ Carregando ocorrências...</span>
                        </div>
                    )}

                    {!loading && ocorrencias.length === 0 && (
                        <div style={{ textAlign: 'center', padding: '40px', color: colors.mutedText }}>
                            <span>Nenhuma ocorrência encontrada</span>
                        </div>
                    )}

                    {!loading && ocorrencias.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                            {ocorrencias.map((ocorrencia) => (
                                <div
                                    key={ocorrencia.id}
                                    style={{
                                        backgroundColor: '#fff',
                                        borderRadius: '12px',
                                        padding: '20px',
                                        border: '1px solid #e9ecef',
                                        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                    }}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                                        <div>
                                            <h4 style={{ margin: '0 0 8px 0', color: colors.headingText }}>
                                                Ocorrência #{ocorrencia.id}
                                            </h4>
                                            <p style={{ margin: '0', color: colors.mutedText, fontSize: '14px' }}>
                                                {formatarData(ocorrencia.data_hora_ocorrencia)}
                                            </p>
                                        </div>
                                        <span style={{
                                            backgroundColor: getStatusColor(ocorrencia.status),
                                            color: '#fff',
                                            padding: '4px 12px',
                                            borderRadius: '20px',
                                            fontSize: '12px',
                                            fontWeight: 'bold'
                                        }}>
                                            {ocorrencia.status}
                                        </span>
                                    </div>

                                    <div style={{ marginBottom: '12px' }}>
                                        <p style={{ margin: '0 0 8px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                            📍 Local:
                                        </p>
                                        <p style={{ margin: '0', color: colors.mutedText }}>
                                            {ocorrencia.endereco_especifico || ocorrencia.endereco || 'N/A'}
                                        </p>
                                    </div>

                                    <div style={{ marginBottom: '12px' }}>
                                        <p style={{ margin: '0 0 8px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                            🏢 Condomínio:
                                        </p>
                                        <p style={{ margin: '0', color: colors.mutedText }}>
                                            {ocorrencia.condominio?.nome || 'N/A'}
                                        </p>
                                    </div>

                                    <div style={{ marginBottom: '12px' }}>
                                        <p style={{ margin: '0 0 8px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                            📄 Relatório:
                                        </p>
                                        <p style={{
                                            margin: '0',
                                            color: colors.mutedText,
                                            maxHeight: '100px',
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            display: '-webkit-box',
                                            WebkitLineClamp: 3,
                                            WebkitBoxOrient: 'vertical'
                                        }}>
                                            {ocorrencia.relatorio_final || ocorrencia.descricao || 'N/A'}
                                        </p>
                                    </div>

                                    {ocorrencia.colaboradores && ocorrencia.colaboradores.length > 0 && (
                                        <div style={{ marginBottom: '12px' }}>
                                            <p style={{ margin: '0 0 8px 0', color: colors.headingText, fontWeight: 'bold' }}>
                                                👥 Colaboradores:
                                            </p>
                                            <p style={{ margin: '0', color: colors.mutedText }}>
                                                {ocorrencia.colaboradores.join(', ')}
                                            </p>
                                        </div>
                                    )}

                                    <div style={{ display: 'flex', gap: '8px', marginTop: '16px' }}>
                                        <Button
                                            title="👁️ Ver Detalhes"
                                            onClick={() => {
                                                navigate(`/ocorrencias/${ocorrencia.id}`);
                                            }}
                                            variant="secondary"
                                            style={{ fontSize: '12px', padding: '8px 12px' }}
                                        />
                                        <Button
                                            title="📋 Copiar"
                                            onClick={() => {
                                                navigator.clipboard.writeText(ocorrencia.relatorio_final || ocorrencia.descricao || '');
                                                alert('Relatório copiado!');
                                            }}
                                            variant="success"
                                            style={{ fontSize: '12px', padding: '8px 12px' }}
                                        />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </BaseScreen>
    );
}; 