import React from 'react';
import { Button } from '../Button';
import { colors } from '../../theme/colors';

interface Ronda {
    id?: number;
    residencial: string;
    inicio: string;
    termino?: string;
    duracao?: number;
    status: 'iniciada' | 'finalizada';
}

interface RondaListaProps {
    rondas: Ronda[];
    onRemoverRonda: (index: number) => void;
}

export const RondaLista: React.FC<RondaListaProps> = ({
    rondas,
    onRemoverRonda
}) => {
    if (rondas.length === 0) return null;

    return (
        <div style={{
            backgroundColor: colors.surface,
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
            <h3 style={{ margin: '0 0 20px 0', color: colors.headingText }}>
                📋 Rondas Registradas ({rondas.length})
            </h3>

            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {rondas.map((ronda, index) => (
                    <div key={index} style={{
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
                            <strong>{ronda.residencial}</strong>
                            <br />
                            <span style={{ color: '#666' }}>
                                {ronda.inicio} - {ronda.termino} ({ronda.duracao} min)
                            </span>
                        </div>
                        <Button
                            title="❌"
                            onClick={() => onRemoverRonda(index)}
                            style={{ backgroundColor: colors.danger, padding: '5px 10px' }}
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}; 