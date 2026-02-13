import React from 'react';
import { colors } from '../theme/colors';

interface InputProps {
    highlighted?: boolean;
    style?: React.CSSProperties;
    placeholder?: string;
    value?: string;
    onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void;
    onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
    onFocus?: (e: React.FocusEvent<HTMLInputElement>) => void;
    disabled?: boolean;
    type?: string;
    name?: string;
    id?: string;
    required?: boolean;
    autoComplete?: string;
    maxLength?: number;
    minLength?: number;
    pattern?: string;
    title?: string;
}

export const Input: React.FC<InputProps> = ({ 
    highlighted, 
    style, 
    placeholder,
    value,
    onChange,
    onBlur,
    onFocus,
    disabled = false,
    type = 'text',
    name,
    id,
    required = false,
    autoComplete,
    maxLength,
    minLength,
    pattern,
    title,
    ...props 
}) => {
    return (
        <input
            style={{
                backgroundColor: colors.surface,
                color: colors.headingText,
                borderRadius: '8px',
                padding: '12px 16px',
                fontSize: '16px',
                margin: '8px 0',
                border: highlighted ? `2px solid ${colors.danger}` : `1px solid ${colors.secondaryBg}`,
                width: '100%',
                boxSizing: 'border-box',
                outline: 'none',
                ...style
            }}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            onBlur={onBlur}
            onFocus={onFocus}
            disabled={disabled}
            type={type}
            name={name}
            id={id}
            required={required}
            autoComplete={autoComplete}
            maxLength={maxLength}
            minLength={minLength}
            pattern={pattern}
            title={title}
            {...props}
        />
    );
}; 