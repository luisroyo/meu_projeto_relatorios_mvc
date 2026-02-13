import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { colors } from '../theme/colors';
import { useAdminCheck } from '../hooks/useAdminCheck';

interface LayoutProps {
  onLogout?: () => void;
  token?: string | null;
}

const Layout: React.FC<LayoutProps> = ({ onLogout, token }) => {
  const location = useLocation();
  const { isAdmin, loading } = useAdminCheck(token || null);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: colors.primaryBg }}>
      {/* Header */}
      <div style={{
        backgroundColor: colors.secondaryBg,
        padding: '16px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <img
            src="/assets/logo_master.png"
            alt="Logo Master"
            style={{ width: '40px', height: '40px', marginRight: '12px' }}
          />
          <h1 style={{
            color: colors.mainText,
            margin: 0,
            fontSize: '20px',
            fontWeight: 'bold'
          }}>
            Ocorrências Master
          </h1>
        </div>

        {onLogout && (
          <button
            onClick={onLogout}
            style={{
              backgroundColor: 'transparent',
              border: `1px solid ${colors.mainText}`,
              color: colors.mainText,
              padding: '8px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = colors.mainText;
              e.currentTarget.style.color = colors.primaryBg;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = colors.mainText;
            }}
          >
            Sair
          </button>
        )}
      </div>

      {/* Navigation */}
      <nav style={{
        backgroundColor: colors.surface,
        padding: '0 20px',
        borderBottom: `1px solid #e0e0e0`
      }}>
        <div style={{
          display: 'flex',
          gap: '0'
        }}>
          <Link
            to="/relatorio"
            style={{
              padding: '16px 24px',
              textDecoration: 'none',
              color: location.pathname === '/' || location.pathname === '/relatorio' ? colors.danger : colors.headingText,
              borderBottom: location.pathname === '/' || location.pathname === '/relatorio' ? `3px solid ${colors.danger}` : '3px solid transparent',
              fontWeight: location.pathname === '/' || location.pathname === '/relatorio' ? 'bold' : 'normal',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            📄 Relatório
          </Link>

          {/* Link de Ronda - apenas para administradores */}
          {!loading && isAdmin && (
            <Link
              to="/ronda"
              style={{
                padding: '16px 24px',
                textDecoration: 'none',
                color: location.pathname === '/ronda' ? colors.danger : colors.headingText,
                borderBottom: location.pathname === '/ronda' ? `3px solid ${colors.danger}` : '3px solid transparent',
                fontWeight: location.pathname === '/ronda' ? 'bold' : 'normal',
                transition: 'all 0.2s ease',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              🚀 Ronda
            </Link>
          )}

          <Link
            to="/ocorrencias"
            style={{
              padding: '16px 24px',
              textDecoration: 'none',
              color: location.pathname === '/ocorrencias' ? colors.danger : colors.headingText,
              borderBottom: location.pathname === '/ocorrencias' ? `3px solid ${colors.danger}` : '3px solid transparent',
              fontWeight: location.pathname === '/ocorrencias' ? 'bold' : 'normal',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            📋 Ocorrências
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <div style={{ flex: 1 }}>
        <Outlet />
      </div>
    </div>
  );
};

export default Layout; 