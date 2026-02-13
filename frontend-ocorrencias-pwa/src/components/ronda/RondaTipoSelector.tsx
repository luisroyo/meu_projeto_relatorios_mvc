import React from 'react';
import { Button } from '../Button';
import { colors } from '../../theme/colors';

interface RondaTipoSelectorProps {
    tipoRonda: 'regular' | 'esporadica';
    onTipoChange: (tipo: 'regular' | 'esporadica') => void;
}

export const RondaTipoSelector: React.FC<RondaTipoSelectorProps> = ({ tipoRonda, onTipoChange }) => {
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
                🎯 Tipo de Ronda
            </h3>
            <div style={{ display: 'flex', gap: '12px' }}>
                <Button
                    title="🔄 Ronda Regular"
                    onClick={() => onTipoChange('regular')}
                    variant={tipoRonda === 'regular' ? 'primary' : 'secondary'}
                    style={{ flex: 1 }}
                />
                <Button
                    title="⏰ Ronda Esporádica"
                    onClick={() => onTipoChange('esporadica')}
                    variant={tipoRonda === 'esporadica' ? 'primary' : 'secondary'}
                    style={{ flex: 1 }}
                />
            </div>
        </div>
    );
}; 