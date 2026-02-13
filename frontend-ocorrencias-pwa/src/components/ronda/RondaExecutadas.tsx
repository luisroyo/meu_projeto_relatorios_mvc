import React from 'react';
import { colors } from '../../theme/colors';

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

interface RondaExecutadasProps {
    condominioId: number;
    condominioNome: string;
    rondasExecutadas: RondaExecutada[];
    loadingRondasExecutadas: boolean;
}

export const RondaExecutadas: React.FC<RondaExecutadasProps> = ({
    condominioId,
    condominioNome,
    rondasExecutadas,
    loadingRondasExecutadas
}) => {
    if (condominioId <= 1) return null;

    return (
        <div style={{
            backgroundColor: colors.surface,
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
            <h3 style={{ margin: '0 0 20px 0', color: colors.headingText }}>
                📋 Rondas Executadas em {condominioNome}
            </h3>

            {loadingRondasExecutadas ? (
                <div style={{ textAlign: 'center', padding: '20px', color: colors.mutedText }}>
                    🔄 Carregando rondas executadas...
                </div>
            ) : rondasExecutadas.length > 0 ? (
                <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                    {rondasExecutadas.map((ronda, index) => (
                        <div key={ronda.id || index} style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '10px',
                            border: '1px solid #e0e0e0',
                            borderRadius: '4px',
                            marginBottom: '10px',
                            backgroundColor: 'white'
                        }}>
                            <div>
                                <strong>Data: {new Date(ronda.data_plantao).toLocaleDateString('pt-BR')}</strong>
                                <br />
                                <span style={{ color: '#666' }}>
                                    {ronda.hora_entrada} - {ronda.hora_saida || 'Em andamento'}
                                    {ronda.duracao_minutos && ` (${ronda.duracao_minutos} min)`}
                                </span>
                                <br />
                                <span style={{ color: '#888', fontSize: '12px' }}>
                                    {ronda.escala_plantao} | {ronda.turno}
                                </span>
                            </div>
                            <div style={{ color: '#28a745', fontSize: '12px', fontWeight: 'bold' }}>
                                ✅ Executada
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div style={{ textAlign: 'center', padding: '20px', color: colors.mutedText }}>
                    <div style={{ marginBottom: '10px' }}>
                        📭 Nenhuma ronda executada encontrada
                    </div>
                    <div style={{ fontSize: '12px', color: '#888' }}>
                        <em>Nenhuma ronda foi encontrada para este período</em>
                    </div>
                </div>
            )}
        </div>
    );
}; 