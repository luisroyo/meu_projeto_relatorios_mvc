import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  Paper,
  Stack,
  useTheme
} from '@mui/material';

interface TestResult {
  type: 'success' | 'error' | 'info';
  message: string;
  details?: any;
}

const TestJwtPage: React.FC = () => {
  const theme = useTheme();
  const [results, setResults] = useState<TestResult[]>([]);
  const [loading, setLoading] = useState(false);

  const addResult = (result: TestResult) => {
    setResults(prev => [...prev, result]);
  };

  const log = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    addResult({ type, message });
    console.log(`[${new Date().toLocaleTimeString()}] ${message}`);
  };

  const checkToken = () => {
    const token = localStorage.getItem('access_token');
    
    if (token) {
      addResult({
        type: 'success',
        message: `Token encontrado! Tamanho: ${token.length} caracteres`,
        details: token.substring(0, 50) + '...'
      });
      log('Token encontrado no localStorage', 'success');
    } else {
      addResult({
        type: 'error',
        message: 'Nenhum token encontrado no localStorage'
      });
      log('Nenhum token encontrado no localStorage', 'error');
    }
  };

  const clearStorage = () => {
    localStorage.clear();
    addResult({
      type: 'info',
      message: 'localStorage limpo'
    });
    log('localStorage limpo', 'info');
  };

  const testLogin = async () => {
    setLoading(true);
    addResult({
      type: 'info',
      message: 'Iniciando teste de login...'
    });
    log('Iniciando teste de login...', 'info');

    try {
      const response = await fetch('http://localhost:5000/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: 'luisroyo25@gmail.com',
          password: 'edu123cs'
        })
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        addResult({
          type: 'success',
          message: 'Login bem-sucedido!',
          details: `Token: ${data.access_token.substring(0, 50)}...`
        });
        log('Login teste: SUCESSO', 'success');
      } else {
        addResult({
          type: 'error',
          message: `Login falhou! Status: ${response.status}`,
          details: data.error || 'Erro desconhecido'
        });
        log(`Login teste: FALHA - ${response.status}`, 'error');
      }
    } catch (error) {
      addResult({
        type: 'error',
        message: 'Erro de conexão!',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      });
      log(`Erro de conexão: ${error instanceof Error ? error.message : 'Erro desconhecido'}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const testJWT = async () => {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      addResult({
        type: 'error',
        message: 'Nenhum token disponível para teste'
      });
      return;
    }

    setLoading(true);
    addResult({
      type: 'info',
      message: 'Iniciando teste JWT...'
    });
    log('Iniciando teste JWT...', 'info');

    try {
      const response = await fetch('http://localhost:5000/api/dashboard/test', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      
      if (response.ok) {
        addResult({
          type: 'success',
          message: 'JWT funcionando!',
          details: `Usuário: ${data.user.username}, ID: ${data.user.id}`
        });
        log('JWT teste: SUCESSO', 'success');
      } else {
        addResult({
          type: 'error',
          message: `JWT falhou! Status: ${response.status}`,
          details: data.error || 'Erro desconhecido'
        });
        log(`JWT teste: FALHA - ${response.status}`, 'error');
      }
    } catch (error) {
      addResult({
        type: 'error',
        message: 'Erro de conexão!',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      });
      log(`Erro de conexão: ${error instanceof Error ? error.message : 'Erro desconhecido'}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const testDashboard = async () => {
    const token = localStorage.getItem('access_token');
    
    if (!token) {
      addResult({
        type: 'error',
        message: 'Nenhum token disponível para teste'
      });
      return;
    }

    setLoading(true);
    addResult({
      type: 'info',
      message: 'Iniciando teste Dashboard...'
    });
    log('Iniciando teste Dashboard...', 'info');

    try {
      const response = await fetch('http://localhost:5000/api/dashboard/stats', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      const data = await response.json();
      
      if (response.ok) {
        addResult({
          type: 'success',
          message: 'Dashboard funcionando!',
          details: `Total Ocorrências: ${data.stats.total_ocorrencias}, Total Rondas: ${data.stats.total_rondas}`
        });
        log('Dashboard teste: SUCESSO', 'success');
      } else {
        addResult({
          type: 'error',
          message: `Dashboard falhou! Status: ${response.status}`,
          details: data.error || 'Erro desconhecido'
        });
        log(`Dashboard teste: FALHA - ${response.status}`, 'error');
      }
    } catch (error) {
      addResult({
        type: 'error',
        message: 'Erro de conexão!',
        details: error instanceof Error ? error.message : 'Erro desconhecido'
      });
      log(`Erro de conexão: ${error instanceof Error ? error.message : 'Erro desconhecido'}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h3" component="h1" sx={{ mb: 3, fontWeight: 700 }}>
        🔍 Teste JWT - Diagnóstico
      </Typography>

      <Stack spacing={3}>
        {/* Seção 1: Verificar Token */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              1. Verificar Token no localStorage
            </Typography>
            <Stack direction="row" spacing={2}>
              <Button 
                variant="contained" 
                onClick={checkToken}
                disabled={loading}
              >
                Verificar Token
              </Button>
              <Button 
                variant="outlined" 
                onClick={clearStorage}
                disabled={loading}
              >
                Limpar localStorage
              </Button>
            </Stack>
          </CardContent>
        </Card>

        {/* Seção 2: Teste de Login */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              2. Teste de Login
            </Typography>
            <Button 
              variant="contained" 
              onClick={testLogin}
              disabled={loading}
            >
              Testar Login
            </Button>
          </CardContent>
        </Card>

        {/* Seção 3: Teste JWT */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              3. Teste JWT no Backend
            </Typography>
            <Button 
              variant="contained" 
              onClick={testJWT}
              disabled={loading}
            >
              Testar JWT
            </Button>
          </CardContent>
        </Card>

        {/* Seção 4: Teste Dashboard */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              4. Teste Dashboard Stats
            </Typography>
            <Button 
              variant="contained" 
              onClick={testDashboard}
              disabled={loading}
            >
              Testar Dashboard
            </Button>
          </CardContent>
        </Card>

        {/* Seção 5: Logs */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              5. Logs do Console
            </Typography>
            <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto', bgcolor: 'grey.50' }}>
              {results.length === 0 ? (
                <Typography color="text.secondary">
                  Nenhum log ainda. Execute os testes acima.
                </Typography>
              ) : (
                <Stack spacing={1}>
                  {results.map((result, index) => (
                    <Alert 
                      key={index} 
                      severity={result.type} 
                      sx={{ '& .MuiAlert-message': { width: '100%' } }}
                    >
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {result.message}
                      </Typography>
                      {result.details && (
                        <Typography variant="body2" sx={{ mt: 1, fontFamily: 'monospace' }}>
                          {result.details}
                        </Typography>
                      )}
                    </Alert>
                  ))}
                </Stack>
              )}
            </Paper>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
};

export default TestJwtPage; 