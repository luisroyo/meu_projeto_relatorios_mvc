import React, { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Box, Typography, Button, Alert } from '@mui/material';
import { Refresh as RefreshIcon } from '@mui/icons-material';

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
    errorInfo?: ErrorInfo;
}

class ErrorBoundary extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Erro capturado pelo ErrorBoundary:', error, errorInfo);
        this.setState({ error, errorInfo });
    }

    handleRefresh = () => {
        window.location.reload();
    };

    render() {
        if (this.state.hasError) {
            return (
                <Box sx={{
                    p: 4,
                    textAlign: 'center',
                    minHeight: '100vh',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center'
                }}>
                    <Alert severity="error" sx={{ mb: 3, maxWidth: 600 }}>
                        <Typography variant="h6" gutterBottom>
                            Ops! Algo deu errado
                        </Typography>
                        <Typography variant="body2" sx={{ mb: 2 }}>
                            Ocorreu um erro inesperado na aplicação. Isso pode ser causado por:
                        </Typography>
                        <ul style={{ textAlign: 'left', margin: '0 0 16px 0' }}>
                            <li>Problemas de conexão com o servidor</li>
                            <li>Dados corrompidos no cache</li>
                            <li>Erro de renderização de componentes</li>
                        </ul>
                        <Typography variant="body2" sx={{ mb: 2 }}>
                            <strong>Erro:</strong> {this.state.error?.message || 'Erro desconhecido'}
                        </Typography>
                    </Alert>

                    <Button
                        variant="contained"
                        startIcon={<RefreshIcon />}
                        onClick={this.handleRefresh}
                        sx={{ mb: 2 }}
                    >
                        Recarregar Página
                    </Button>

                    <Button
                        variant="outlined"
                        onClick={() => window.location.href = '/login'}
                    >
                        Voltar ao Login
                    </Button>
                </Box>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary; 