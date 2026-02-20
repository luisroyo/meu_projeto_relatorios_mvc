import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button, 
  CircularProgress,
  Alert,
  Paper
} from '@mui/material';
import { 
  QrCodeScanner as QrCodeIcon, 
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  PhoneIphone as PhoneIcon,
  Group as GroupIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import axios from 'axios';

// Usaremos a URL base do Node.js e da API Python
const WHATSAPP_API_URL = process.env.REACT_APP_WHATSAPP_API_URL || 'http://localhost:3001/api/whatsapp';
const PYTHON_API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

interface WhatsAppGroup {
  id: string;
  subject: string;
  participantsCount: number;
}

interface Condominio {
  id: number;
  nome: string;
  whatsapp_group_id: string | null;
}

export const WhatsAppConfigPage: React.FC = () => {
  const [status, setStatus] = useState<string>('initializing');
  const [qrCodeData, setQrCodeData] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Estados para Mapeamento
  const [groups, setGroups] = useState<WhatsAppGroup[]>([]);
  const [condominios, setCondominios] = useState<Condominio[]>([]);
  const [loadingMapping, setLoadingMapping] = useState<boolean>(false);
  const [mappingMessage, setMappingMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${WHATSAPP_API_URL}/status`);
      setStatus(response.data.status);
      setQrCodeData(response.data.qr);
    } catch (err: any) {
      console.error('Erro ao buscar status do WhatsApp:', err);
      // Se falhar silenciosamente, pode ser que o Node.js esteja offline
      setError('Não foi possível conectar ao serviço do WhatsApp. Certifique-se de que o servidor Node.js está rodando na porta correta.');
      setStatus('disconnected');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Configura um polling para verificar o status a cada 5 segundos
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // Busca dados de mapeamento quando o WhatsApp conecta
  useEffect(() => {
    if (status === 'connected') {
      fetchMappingData();
    }
  }, [status]);

  const fetchMappingData = async () => {
    setLoadingMapping(true);
    try {
      // Busca Grupos do Node
      const groupsRes = await axios.get(`${WHATSAPP_API_URL}/groups`);
      setGroups(groupsRes.data);

      // Busca Condomínios e Mapeamentos Atuais do Python
      // Usando query params ou axios defaults se precisar mandar Token JWT aqui
      const condRes = await axios.get(`${PYTHON_API_URL}/whatsapp/condominios-mapping`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      });
      setCondominios(condRes.data);
    } catch (err) {
      console.error('Erro ao buscar dados de mapeamento:', err);
    } finally {
      setLoadingMapping(false);
    }
  };

  const handleSaveMapping = async (condominioId: number, groupId: string) => {
    setMappingMessage(null);
    try {
      await axios.post(`${PYTHON_API_URL}/whatsapp/condominio/${condominioId}/map-group`, {
        whatsapp_group_id: groupId || null
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`
        }
      });
      
      setMappingMessage({type: 'success', text: 'Mapeamento salvo com sucesso!'});
      setTimeout(() => setMappingMessage(null), 3000);
      
      // Atualiza a UI local
      setCondominios(prev => prev.map(c => 
        c.id === condominioId ? { ...c, whatsapp_group_id: groupId || null } : c
      ));

    } catch (err) {
      console.error('Erro ao salvar mapeamento:', err);
      setMappingMessage({type: 'error', text: 'Erro ao salvar o mapeamento.'});
    }
  };

  const handleLogout = async () => {
    setLoading(true);
    try {
      await axios.post(`${WHATSAPP_API_URL}/logout`);
      await fetchStatus();
    } catch (err: any) {
      setError('Erro ao desconectar.');
      setLoading(false);
    }
  };

  const renderStatusIcon = () => {
    if (loading && status === 'initializing') return <CircularProgress size={60} />;
    if (status === 'connected') return <CheckCircleIcon color="success" sx={{ fontSize: 60 }} />;
    if (status === 'qr_ready') return <QrCodeIcon color="primary" sx={{ fontSize: 60 }} />;
    return <PhoneIcon color="disabled" sx={{ fontSize: 60 }} />;
  };

  return (
    <Box sx={{ p: 4, maxWidth: 800, margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <PhoneIcon fontSize="large" color="primary" />
        Conexão WhatsApp (Rondas)
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Conecte o número de telefone que participará dos grupos dos residenciais. 
        Este aparelho será responsável por monitorar as mensagens de rondas enviadas pelos supervisores.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} action={
          <Button color="inherit" size="small" onClick={fetchStatus}>
            TENTAR NOVAMENTE
          </Button>
        }>
          {error}
        </Alert>
      )}

      <Card elevation={3} sx={{ mt: 2, borderRadius: 2 }}>
        <CardContent sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', p: 4 }}>
          
          <Box sx={{ mb: 3 }}>
            {renderStatusIcon()}
          </Box>

          <Typography variant="h6" fontWeight="bold" gutterBottom>
            {status === 'connected' && 'Aparelho Conectado com Sucesso!'}
            {status === 'qr_ready' && 'Escaneie o QR Code'}
            {status === 'initializing' && 'Iniciando o serviço...'}
            {status === 'disconnected' && 'Serviço Desconectado'}
          </Typography>

          {status === 'connected' && (
            <>
              <Typography variant="body2" color="text.secondary" align="center" paragraph>
                O sistema já está monitorando ativamente os grupos e salvando as informações no banco de dados. 
                Você já pode utilizar a Correção Mágica de Rondas.
              </Typography>
              <Button 
                variant="outlined" 
                color="error" 
                onClick={handleLogout}
                disabled={loading}
                sx={{ mt: 2 }}
              >
                Desconectar Aparelho
              </Button>
            </>
          )}

          {status === 'qr_ready' && qrCodeData && (
            <Paper elevation={2} sx={{ p: 2, bgcolor: 'white', borderRadius: 4, mb: 3 }}>
              <img src={qrCodeData} alt="WhatsApp QR Code" style={{ width: 260, height: 260 }} />
            </Paper>
          )}

          {status === 'qr_ready' && (
             <Box sx={{ textAlign: 'left', bgcolor: '#f5f5f5', p: 3, borderRadius: 2, maxWidth: 500 }}>
               <Typography variant="subtitle2" fontWeight="bold" gutterBottom>Instruções:</Typography>
               <ol style={{ paddingLeft: '20px', margin: 0 }}>
                 <li>Abra o WhatsApp no seu celular</li>
                 <li>Toque em Mais opções (três pontos) ou Configurações</li>
                 <li>Toque em <b>Aparelhos conectados</b></li>
                 <li>Toque em <b>Conectar um aparelho</b></li>
                 <li>Aponte a tela do seu celular para esta tela para capturar o código</li>
               </ol>
             </Box>
          )}

          <Button 
            startIcon={<RefreshIcon />} 
            onClick={fetchStatus} 
            disabled={loading}
            sx={{ mt: 3 }}
          >
            Atualizar Status
          </Button>

        </CardContent>
      </Card>

      {/* Seção de Mapeamento de Grupos (Aparece apenas quando conectado) */}
      {status === 'connected' && (
        <Card elevation={3} sx={{ mt: 4, borderRadius: 2 }}>
          <Box sx={{ bgcolor: 'primary.main', color: 'primary.contrastText', p: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <GroupIcon />
              Mapeamento de Grupos (Residenciais)
            </Typography>
          </Box>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="body1" color="text.secondary" paragraph>
              Selecione qual Grupo do WhatsApp corresponde a cada condomínio cadastrado no sistema.
            </Typography>

            {mappingMessage && (
              <Alert severity={mappingMessage.type} sx={{ mb: 2 }}>
                {mappingMessage.text}
              </Alert>
            )}

            {loadingMapping ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : condominios.length === 0 ? (
              <Alert severity="warning">Nenhum condomínio cadastrado no sistema.</Alert>
            ) : (
              <Box>
                {condominios.map((condominio) => (
                  <Box key={condominio.id} sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between',
                    p: 2, 
                    borderBottom: '1px solid #eee',
                    flexWrap: 'wrap',
                    gap: 2
                  }}>
                    <Typography variant="subtitle1" fontWeight="bold" sx={{ width: { xs: '100%', sm: '30%' } }}>
                      {condominio.nome}
                    </Typography>
                    
                    <Box sx={{ flexGrow: 1, minWidth: 200 }}>
                      <select 
                        className="form-select"
                        style={{ 
                          width: '100%', 
                          padding: '8px', 
                          borderRadius: '4px',
                          border: '1px solid #ccc'
                        }}
                        value={condominio.whatsapp_group_id || ''}
                        onChange={(e) => {
                          const val = e.target.value;
                          setCondominios(prev => prev.map(c => 
                            c.id === condominio.id ? {...c, whatsapp_group_id: val} : c
                          ));
                        }}
                      >
                        <option value="">-- Não Monitorar este Condomínio --</option>
                        {groups.map(g => (
                          <option key={g.id} value={g.id}>
                            {g.subject} ({g.participantsCount} membros)
                          </option>
                        ))}
                      </select>
                    </Box>

                    <Button 
                      variant="contained" 
                      color="primary"
                      size="small"
                      startIcon={<SaveIcon />}
                      onClick={() => handleSaveMapping(condominio.id, condominio.whatsapp_group_id || '')}
                    >
                      Salvar
                    </Button>
                  </Box>
                ))}
              </Box>
            )}

            <Button 
              startIcon={<RefreshIcon />} 
              onClick={fetchMappingData} 
              disabled={loadingMapping}
              sx={{ mt: 3 }}
            >
              Recarregar Condomínios e Grupos
            </Button>
          </CardContent>
        </Card>
      )}

    </Box>
  );
};

export default WhatsAppConfigPage;
