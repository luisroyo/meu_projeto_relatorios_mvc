import React, { useState } from 'react';
import { colors } from '../theme/colors';

interface AnimatedInputProps {
    label: string;
    value?: string;
    style?: React.CSSProperties;
    disabled?: boolean;
    placeholder?: string;
    onChange?: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    onFocus?: (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    onBlur?: (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
    multiline?: boolean;
    rows?: number;
    name?: string;
    id?: string;
    required?: boolean;
    autoComplete?: string;
    maxLength?: number;
    minLength?: number;
    pattern?: string;
    title?: string;
}

export const AnimatedInput: React.FC<AnimatedInputProps> = ({ 
    label, 
    value, 
    style, 
    disabled = false, 
    placeholder,
    onChange,
    onFocus,
    onBlur,
    multiline = false,
    rows = 4,
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
    const [isFocused, setIsFocused] = useState(false);
    const hasValue = value && value.length > 0;

    const handleFocus = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setIsFocused(true);
        onFocus && onFocus(e);
    };

    const handleBlur = (e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setIsFocused(false);
        onBlur && onBlur(e);
    };

    const labelStyle: React.CSSProperties = {
        position: 'absolute',
        left: '14px',
        top: isFocused || hasValue ? '-10px' : '18px',
        fontSize: isFocused || hasValue ? '13px' : '17px',
        color: isFocused ? colors.primaryBg : colors.mutedText,
        backgroundColor: 'transparent',
        padding: '0 4px',
        zIndex: 2,
        fontWeight: '500',
        letterSpacing: '0.2px',
        transition: 'all 0.18s ease',
        pointerEvents: 'none'
    };

    const inputStyle: React.CSSProperties = {
        backgroundColor: disabled ? '#E9ECEF' : (isFocused ? '#F0F6FA' : '#F5F7FA'),
        color: disabled ? colors.mutedText : colors.headingText,
        borderRadius: '12px',
        padding: '12px 16px',
        fontSize: '17px',
        border: `1px solid ${disabled ? '#D1D5DB' : (isFocused ? colors.primaryBg : colors.secondaryBg)}`,
        width: '100%',
        boxSizing: 'border-box',
        outline: 'none',
        minHeight: '44px',
        marginTop: '0',
        fontWeight: '400',
        boxShadow: isFocused ? `0 0 0 4px ${colors.primaryBg}07` : 'none',
        transition: 'all 0.18s ease',
        ...style
    };

    if (multiline) {
        inputStyle.minHeight = '100px';
        inputStyle.resize = 'vertical';
    }

    return (
        <div style={{
            margin: '6px 0',
            paddingTop: '8px',
            position: 'relative'
        }}>
            <label style={labelStyle}>{label}</label>
            {multiline ? (
                <textarea
                    value={value}
                    disabled={disabled}
                    style={inputStyle}
                    placeholder={isFocused ? '' : placeholder}
                    onChange={onChange}
                    onFocus={handleFocus}
                    onBlur={handleBlur}
                    rows={rows}
                    name={name}
                    id={id}
                    required={required}
                    maxLength={maxLength}
                    minLength={minLength}
                    title={title}
                    {...props}
                />
            ) : (
                <input
                    value={value}
                    disabled={disabled}
                    style={inputStyle}
                    placeholder={isFocused ? '' : placeholder}
                    onChange={onChange}
                    onFocus={handleFocus}
                    onBlur={handleBlur}
                    type="text"
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
            )}
        </div>
    );
}; 