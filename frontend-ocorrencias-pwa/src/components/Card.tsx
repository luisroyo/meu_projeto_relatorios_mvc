import React, { ReactNode } from 'react';
import { colors } from '../theme/colors';

interface CardProps {
    children: ReactNode;
    style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({ children, style }) => {
    return (
        <div style={{
            backgroundColor: colors.surface,
            borderRadius: '12px',
            padding: '16px',
            margin: '8px 0',
            boxShadow: '0px 2px 4px rgba(0,0,0,0.1)',
            ...style
        }}>
            {children}
        </div>
    );
}; 