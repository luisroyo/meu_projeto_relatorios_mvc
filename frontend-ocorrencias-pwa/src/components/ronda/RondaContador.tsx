import React from 'react';
import { Button } from '../Button';
import { colors } from '../../theme/colors';

interface RondaContadorProps {
    contador: number;
    contadorAtivo: boolean;
    onIniciar: () => void;
    onParar: () => void;
    formatarTempo: (segundos: number) => string;
}

export const RondaContador: React.FC<RondaContadorProps> = ({
    contador,
    contadorAtivo,
    onIniciar,
    onParar,
    formatarTempo
}) => {
    return (
        <div style={{
            backgroundColor: colors.surface,
            padding: '20px',
            borderRadius: '8px',
            marginBottom: '20px',
            textAlign: 'center',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
            <h3 style={{ margin: '0 0 15px 0', color: colors.headingText }}>
                ⏰ Contador Regressivo (20 min)
            </h3>

            <div style={{
                fontSize: '48px',
                fontWeight: 'bold',
                color: contador < 300 ? colors.danger : colors.headingText,
                marginBottom: '15px'
            }}>
                {formatarTempo(contador)}
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                <Button
                    title="▶️ Iniciar"
                    onClick={onIniciar}
                    disabled={contadorAtivo}
                    style={{ backgroundColor: colors.success }}
                />
                <Button
                    title="⏹️ Parar"
                    onClick={onParar}
                    disabled={!contadorAtivo}
                    style={{ backgroundColor: colors.danger }}
                />
            </div>
        </div>
    );
}; 