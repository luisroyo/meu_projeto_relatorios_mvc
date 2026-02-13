import React from 'react';
import { colors } from '../theme/colors';

interface BaseScreenProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  showCredit?: boolean;
  disableScroll?: boolean;
  backgroundColor?: string;
}

export const BaseScreen: React.FC<BaseScreenProps> = ({ 
  title, 
  subtitle, 
  children, 
  showCredit = true, 
  disableScroll = false, 
  backgroundColor 
}) => (
  <div style={{ 
    minHeight: '100vh',
    backgroundColor: backgroundColor || '#003c3c',
    padding: '20px',
    display: 'flex',
    flexDirection: 'column'
  }}>
    {title && (
      <div style={{
        backgroundColor: 'transparent',
        alignItems: 'center',
        marginBottom: 0,
        textAlign: 'center'
      }}>
        <h1 style={{
          color: '#fff',
          fontSize: '24px',
          fontWeight: 'bold',
          marginBottom: '8px',
          textAlign: 'center',
          margin: 0
        }}>
          {title}
        </h1>
      </div>
    )}
    
    {subtitle && (
      <p style={{
        fontSize: '16px',
        color: '#ddd',
        textAlign: 'center',
        marginBottom: '20px',
        margin: '0 0 20px 0'
      }}>
        {subtitle}
      </p>
    )}
    
    <div style={{
      backgroundColor: '#fff',
      borderRadius: '16px',
      padding: '20px',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
      flex: 1,
      marginBottom: showCredit ? '20px' : '0'
    }}>
      {children}
    </div>
    
    {showCredit && (
      <div style={{
        alignItems: 'center',
        marginTop: '20px',
        marginBottom: '10px',
        textAlign: 'center'
      }}>
        <p style={{
          color: '#ccc',
          fontSize: '13px',
          fontStyle: 'italic',
          textAlign: 'center',
          marginTop: '10px',
          margin: 0
        }}>
          Desenvolvido por Luis Eduardo Rodrigues Royo
        </p>
      </div>
    )}
  </div>
); 