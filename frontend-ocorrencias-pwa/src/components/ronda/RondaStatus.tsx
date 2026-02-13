import React from 'react';
import { colors } from '../../theme/colors';

interface RondaStatusProps {
    rondaAtiva: any;
}

export const RondaStatus: React.FC<RondaStatusProps> = ({ rondaAtiva }) => {
    return (
        <div style={{
            backgroundColor: '#e7f3ff',
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
                {rondaAtiva.em_andamento ? '🟢 Ronda em Andamento' : '🔴 Nenhuma Ronda Ativa'}
            </h3>

            {rondaAtiva.em_andamento && rondaAtiva.ronda && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                    <div>
                        <p style={{ margin: '0', fontWeight: 'bold' }}>ID da Ronda:</p>
                        <p style={{ margin: '0', color: '#666' }}>{rondaAtiva.ronda.id}</p>
                    </div>

                    {rondaAtiva.ronda.inicio && (
                        <div>
                            <p style={{ margin: '0', fontWeight: 'bold' }}>Início:</p>
                            <p style={{ margin: '0', color: '#666' }}>{rondaAtiva.ronda.inicio}</p>
                        </div>
                    )}

                    {rondaAtiva.ronda.hora_entrada && (
                        <div>
                            <p style={{ margin: '0', fontWeight: 'bold' }}>Hora de Entrada:</p>
                            <p style={{ margin: '0', color: '#666' }}>{rondaAtiva.ronda.hora_entrada}</p>
                        </div>
                    )}

                    {rondaAtiva.ronda.escala_plantao && (
                        <div>
                            <p style={{ margin: '0', fontWeight: 'bold' }}>Escala:</p>
                            <p style={{ margin: '0', color: '#666' }}>{rondaAtiva.ronda.escala_plantao}</p>
                        </div>
                    )}

                    {rondaAtiva.ronda.turno && (
                        <div>
                            <p style={{ margin: '0', fontWeight: 'bold' }}>Turno:</p>
                            <p style={{ margin: '0', color: '#666' }}>{rondaAtiva.ronda.turno}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}; 