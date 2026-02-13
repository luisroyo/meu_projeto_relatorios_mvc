import React from 'react';
import { colors } from '../theme/colors';

interface ButtonProps {
    title: string;
    variant?: 'primary' | 'danger' | 'success' | 'secondary';
    textStyle?: React.CSSProperties;
    style?: React.CSSProperties;
    onClick?: () => void;
    disabled?: boolean;
    type?: 'button' | 'submit' | 'reset';
}

export const Button: React.FC<ButtonProps> = ({
    title,
    variant = 'primary',
    style,
    textStyle,
    onClick,
    disabled = false,
    type = 'button',
    ...props
}) => {
    const getVariantStyle = () => {
        switch (variant) {
            case 'primary':
                return { backgroundColor: colors.danger };
            case 'danger':
                return { backgroundColor: colors.dangerHover };
            case 'success':
                return { backgroundColor: colors.success };
            case 'secondary':
                return { backgroundColor: colors.secondaryBg };
            default:
                return { backgroundColor: colors.danger };
        }
    };

    return (
        <button
            style={{
                padding: '14px 24px',
                borderRadius: '8px',
                alignItems: 'center',
                marginTop: '8px',
                marginBottom: '8px',
                border: 'none',
                cursor: disabled ? 'not-allowed' : 'pointer',
                opacity: disabled ? 0.6 : 1,
                ...getVariantStyle(),
                ...style
            }}
            onClick={onClick}
            disabled={disabled}
            type={type}
            {...props}
        >
            <span style={{
                color: colors.mainText,
                fontWeight: 'bold',
                fontSize: '16px',
                ...textStyle
            }}>
                {title}
            </span>
        </button>
    );
}; 