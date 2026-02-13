import React from 'react';
import { Button } from '../Button';
import { colors } from '../../theme/colors';

interface RondaAcoesProps {
    rondas: any[];
    loading: boolean;
    onSalvarRondas: () => void;
    onEnviarWhatsApp: () => void;
}

export const RondaAcoes: React.FC<RondaAcoesProps> = ({
    rondas,
    loading,
    onSalvarRondas,
    onEnviarWhatsApp
}) => {
    if (rondas.length === 0) return null;

    return (
        <div style={{
            display: 'flex',
            gap: '15px',
            justifyContent: 'center',
            padding: '20px',
            backgroundColor: colors.surface,
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
            <Button
                title="💾 Salvar Rondas"
                onClick={onSalvarRondas}
                disabled={loading}
                style={{ backgroundColor: colors.primaryBg }}
            />

            <Button
                title="📱 Enviar WhatsApp"
                onClick={onEnviarWhatsApp}
                disabled={loading}
                style={{ backgroundColor: colors.success }}
            />
        </div>
    );
}; 