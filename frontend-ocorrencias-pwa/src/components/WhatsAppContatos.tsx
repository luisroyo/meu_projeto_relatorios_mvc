import React from 'react';
import { colors } from '../theme/colors';

const contatos = [
    { label: 'Central', numero: '+5519997497922' },
    { label: 'Supervisão', numero: '+5519997304337' },
];

export const WhatsAppContatos = () => {
    const handleWhatsAppClick = (numero: string) => {
        window.open(`https://wa.me/${numero}`, '_blank');
    };

    return (
        <div style={{
            borderTop: `2px solid ${colors.warning}`,
            padding: '12px',
            backgroundColor: colors.primaryBg,
            alignItems: 'center',
            textAlign: 'center'
        }}>
            {contatos.map(({ label, numero }) => (
                <button
                    key={numero}
                    style={{
                        display: 'flex',
                        alignItems: 'center',
                        margin: '4px 0',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: '#fff',
                        fontSize: '16px',
                        padding: '8px',
                        borderRadius: '8px',
                        transition: 'background-color 0.2s ease'
                    }}
                    onClick={() => handleWhatsAppClick(numero)}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.1)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = 'transparent';
                    }}
                >
                    <span style={{
                        color: colors.success,
                        marginRight: '8px',
                        fontSize: '22px'
                    }}>
                        📱
                    </span>
                    <span>{label}: {numero.replace('+55', '+55 ')}</span>
                </button>
            ))}
        </div>
    );
}; 