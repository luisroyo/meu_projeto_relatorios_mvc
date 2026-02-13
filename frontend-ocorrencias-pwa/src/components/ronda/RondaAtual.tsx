import React from 'react';
import { Button } from '../Button';
import { Input } from '../Input';
import { colors } from '../../theme/colors';

interface Ronda {
    id?: number;
    residencial: string;
    inicio: string;
    termino?: string;
    duracao?: number;
    status: 'iniciada' | 'finalizada';
}

interface RondaAtualProps {
    rondaAtual: Ronda | null;
    terminoRonda: string;
    setTerminoRonda: (termino: string) => void;
    loading: boolean;
    onFinalizarRonda: () => void;
}

export const RondaAtual: React.FC<RondaAtualProps> = ({
    rondaAtual,
    terminoRonda,
    setTerminoRonda,
    loading,
    onFinalizarRonda
}) => {
    if (!rondaAtual) return null;

    return (
        <div style={{
            backgroundColor: colors.success,
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            color: 'white'
        }}>
            <h3 style={{ margin: '0 0 15px 0' }}>
                🔄 Ronda em Andamento
            </h3>

            <div style={{ marginBottom: '15px' }}>
                <strong>Residencial:</strong> {rondaAtual.residencial}<br />
                <strong>Início:</strong> {rondaAtual.inicio}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <div>
                    <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
                        Horário de Término
                    </label>
                    <Input
                        type="time"
                        value={terminoRonda}
                        onChange={(e) => setTerminoRonda(e.target.value)}
                    />
                </div>

                <Button
                    title="⏹️ Finalizar Ronda"
                    onClick={onFinalizarRonda}
                    disabled={loading || !terminoRonda}
                    style={{ backgroundColor: colors.danger }}
                />
            </div>
        </div>
    );
}; 