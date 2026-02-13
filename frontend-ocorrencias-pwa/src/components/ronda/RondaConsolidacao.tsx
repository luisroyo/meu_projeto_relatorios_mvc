import React from 'react';
import { Button } from '../Button';
import { Input } from '../Input';
import { colors } from '../../theme/colors';

interface RondaConsolidacaoProps {
    dataInicioConsolidacao: string;
    setDataInicioConsolidacao: (data: string) => void;
    dataFimConsolidacao: string;
    setDataFimConsolidacao: (data: string) => void;
    resultadoConsolidacao: any;
    onConsolidarTurno: () => void;
    onProcessoCompleto: () => void;
    onMarcarProcessadas: () => void;
    loading: boolean;
}

export const RondaConsolidacao: React.FC<RondaConsolidacaoProps> = ({
    dataInicioConsolidacao,
    setDataInicioConsolidacao,
    dataFimConsolidacao,
    setDataFimConsolidacao,
    resultadoConsolidacao,
    onConsolidarTurno,
    onProcessoCompleto,
    onMarcarProcessadas,
    loading
}) => {
    return (
        <div style={{
            backgroundColor: '#f8f9fa',
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px'
        }}>
            <h3 style={{
                color: colors.primaryBg,
                marginBottom: '16px',
                fontSize: '18px',
                fontWeight: 'bold'
            }}>
                📊 Consolidação de Rondas Esporádicas
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                        Data Início
                    </label>
                    <Input
                        type="date"
                        value={dataInicioConsolidacao}
                        onChange={(e) => setDataInicioConsolidacao(e.target.value)}
                    />
                </div>
                <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                        Data Fim
                    </label>
                    <Input
                        type="date"
                        value={dataFimConsolidacao}
                        onChange={(e) => setDataFimConsolidacao(e.target.value)}
                    />
                </div>
            </div>

            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <Button
                    title="📋 Consolidar Turno"
                    onClick={onConsolidarTurno}
                    disabled={loading}
                    variant="secondary"
                    style={{ minWidth: '140px' }}
                />
                <Button
                    title="🔄 Processo Completo"
                    onClick={onProcessoCompleto}
                    disabled={loading}
                    variant="primary"
                    style={{ minWidth: '140px' }}
                />
                <Button
                    title="✅ Marcar Processadas"
                    onClick={onMarcarProcessadas}
                    disabled={loading}
                    variant="success"
                    style={{ minWidth: '140px' }}
                />
            </div>

            {resultadoConsolidacao && (
                <div style={{
                    backgroundColor: '#d4edda',
                    padding: '16px',
                    borderRadius: '6px',
                    marginTop: '16px',
                    border: '1px solid #c3e6cb'
                }}>
                    <h4 style={{
                        color: '#155724',
                        marginBottom: '8px',
                        fontSize: '16px',
                        fontWeight: 'bold'
                    }}>
                        Resultado da Consolidação
                    </h4>
                    <p style={{
                        color: '#155724',
                        margin: '0',
                        fontSize: '14px'
                    }}>
                        {resultadoConsolidacao.message}
                    </p>
                    {resultadoConsolidacao.relatorio_consolidado && (
                        <details style={{ marginTop: '12px' }}>
                            <summary style={{
                                color: '#155724',
                                cursor: 'pointer',
                                fontWeight: 'bold'
                            }}>
                                Ver Relatório Consolidado
                            </summary>
                            <pre style={{
                                backgroundColor: '#fff',
                                padding: '12px',
                                borderRadius: '4px',
                                marginTop: '8px',
                                fontSize: '12px',
                                whiteSpace: 'pre-wrap',
                                overflow: 'auto',
                                maxHeight: '200px'
                            }}>
                                {resultadoConsolidacao.relatorio_consolidado}
                            </pre>
                        </details>
                    )}
                </div>
            )}
        </div>
    );
}; 