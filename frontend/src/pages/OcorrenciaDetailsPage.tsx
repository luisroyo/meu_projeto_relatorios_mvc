import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  Chip,
  Grid,
  List,
  ListItem,
  ListItemText,
  Alert,
  Stack,
  useTheme,
  alpha,
  IconButton,
  Tooltip,
  Snackbar
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  ContentCopy as CopyIcon,
  Check as CheckIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import LoadingSpinner from '../components/LoadingSpinner';
import { ocorrenciaService } from '../services/api';
import type { Ocorrencia } from '../types';

const OcorrenciaDetailsPage: React.FC = () => {
  const theme = useTheme();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [ocorrencia, setOcorrencia] = useState<Ocorrencia | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (id) {
      loadOcorrencia(parseInt(id));
    }
  }, [id]);

  const loadOcorrencia = async (ocorrenciaId: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await ocorrenciaService.getById(ocorrenciaId);
      setOcorrencia(data);
    } catch (error) {
      console.error('Erro ao carregar ocorrência:', error);
      setError('Erro ao carregar detalhes da ocorrência. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyRelatorio = async () => {
    if (!ocorrencia?.descricao) return;

    try {
      await navigator.clipboard.writeText(ocorrencia.descricao);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Erro ao copiar:', error);
      // Fallback para navegadores mais antigos
      const textArea = document.createElement('textarea');
      textArea.value = ocorrencia.descricao;
      textArea.style.position = 'fixed';
      textArea.style.left = '-9999px';
      textArea.style.top = '-9999px';
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');

      // Verificar se o elemento ainda existe antes de remover
      if (document.body.contains(textArea)) {
        document.body.removeChild(textArea);
      }

      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleAprovarOcorrencia = async () => {
    if (!ocorrencia) return;

    if (window.confirm('Confirmar aprovação desta ocorrência?')) {
      try {
        await ocorrenciaService.update(ocorrencia.id, { status: 'Aprovada' });
        loadOcorrencia(ocorrencia.id);
      } catch (error) {
        console.error('Erro ao aprovar ocorrência:', error);
        setError('Erro ao aprovar ocorrência. Tente novamente.');
      }
    }
  };

  const handleRejeitarOcorrencia = async () => {
    if (!ocorrencia) return;

    if (window.confirm('Confirmar rejeição desta ocorrência?')) {
      try {
        await ocorrenciaService.update(ocorrencia.id, { status: 'Rejeitada' });
        loadOcorrencia(ocorrencia.id);
      } catch (error) {
        console.error('Erro ao rejeitar ocorrência:', error);
        setError('Erro ao rejeitar ocorrência. Tente novamente.');
      }
    }
  };

  const handleDeletarOcorrencia = async () => {
    if (!ocorrencia) return;

    if (window.confirm('Tem certeza que deseja excluir esta ocorrência? Esta ação não pode ser desfeita.')) {
      try {
        await ocorrenciaService.delete(ocorrencia.id);
        navigate('/ocorrencias');
      } catch (error) {
        console.error('Erro ao deletar ocorrência:', error);
        setError('Erro ao deletar ocorrência. Tente novamente.');
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'concluída': return 'success';
      case 'em andamento': return 'warning';
      case 'registrada': return 'info';
      case 'aprovada': return 'success';
      case 'rejeitada': return 'error';
      default: return 'default';
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'dd/MM/yyyy HH:mm', { locale: ptBR });
    } catch {
      return 'N/A';
    }
  };

  if (loading) {
    return <LoadingSpinner message="Carregando ocorrência..." size="large" />;
  }

  if (error || !ocorrencia) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error || 'Ocorrência não encontrada'}
        </Alert>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/ocorrencias')}
        >
          Voltar ao Histórico
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          mb: 1
        }}>
          📄 Detalhes da Ocorrência #{ocorrencia.id}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Detalhes completos da ocorrência oficial registrada.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Card Principal */}
      <Card sx={{ mb: 4, borderRadius: 3, boxShadow: theme.shadows[3] }}>
        <CardHeader
          title={
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6" fontWeight={600}>
                Resumo da Ocorrência
              </Typography>
              <Chip
                label={ocorrencia.status}
                color={getStatusColor(ocorrencia.status) as any}
                variant="filled"
                sx={{ fontWeight: 600 }}
              />
            </Box>
          }
          sx={{
            backgroundColor: alpha(theme.palette.background.default, 0.8),
            borderBottom: `1px solid ${theme.palette.divider}`
          }}
        />
        <CardContent>
          <Grid container spacing={4}>
            {/* Coluna Esquerda */}
            <Grid item xs={12} md={6}>
              <List sx={{ p: 0 }}>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="ID da Ocorrência"
                    secondary={ocorrencia.id}
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="Tipo"
                    secondary={ocorrencia.tipo || 'N/A'}
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="Data e Hora"
                    secondary={formatDate(ocorrencia.data_hora_ocorrencia)}
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="Registrada por"
                    secondary={ocorrencia.registrado_por || 'N/A'}
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="Supervisor"
                    secondary={ocorrencia.supervisor || 'N/A'}
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="Condomínio"
                    secondary={ocorrencia.condominio || 'N/A'}
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="Turno"
                    secondary={ocorrencia.turno || 'N/A'}
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
              </List>
            </Grid>

            {/* Coluna Direita */}
            <Grid item xs={12} md={6}>
              <List sx={{ p: 0 }}>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="Endereço Específico"
                    secondary={ocorrencia.endereco || 'Não informado'}
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="Órgãos Acionados"
                    secondary={
                      ocorrencia.orgaos_publicos && ocorrencia.orgaos_publicos.length > 0 ? (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                          {ocorrencia.orgaos_publicos.map((orgao, index) => (
                            <Chip
                              key={index}
                              label={orgao}
                              size="small"
                              color="info"
                              variant="outlined"
                            />
                          ))}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          Nenhum
                        </Typography>
                      )
                    }
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
                <ListItem sx={{ px: 0, py: 1 }}>
                  <ListItemText
                    primary="Colaboradores Envolvidos"
                    secondary={
                      ocorrencia.colaboradores && ocorrencia.colaboradores.length > 0 ? (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                          {ocorrencia.colaboradores.map((colaborador, index) => (
                            <Chip
                              key={index}
                              label={colaborador}
                              size="small"
                              variant="outlined"
                              sx={{ backgroundColor: alpha(theme.palette.background.default, 0.8) }}
                            />
                          ))}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          Nenhum
                        </Typography>
                      )
                    }
                    primaryTypographyProps={{ fontWeight: 600, color: 'text.primary' }}
                  />
                </ListItem>
              </List>
            </Grid>
          </Grid>

          <Box sx={{ mt: 3, pt: 3, borderTop: `1px solid ${theme.palette.divider}` }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" fontWeight={600}>
                Relatório Final Oficial
              </Typography>
              <Button
                variant="outlined"
                size="small"
                startIcon={copied ? <CheckIcon /> : <CopyIcon />}
                onClick={handleCopyRelatorio}
                sx={{ borderRadius: 2 }}
              >
                {copied ? 'Copiado!' : 'Copiar Relatório'}
              </Button>
            </Box>
            <Box
              component="pre"
              sx={{
                backgroundColor: alpha(theme.palette.background.default, 0.5),
                p: 2,
                borderRadius: 2,
                border: `1px solid ${theme.palette.divider}`,
                fontFamily: 'monospace',
                fontSize: '0.875rem',
                lineHeight: 1.5,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                maxHeight: 400,
                overflow: 'auto'
              }}
            >
              {ocorrencia.descricao || 'Nenhum relatório disponível'}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Botões de Ação */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
        <Button
          variant="outlined"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/ocorrencias')}
        >
          Voltar ao Histórico
        </Button>

        <Stack direction="row" spacing={2}>
          {ocorrencia.status === 'Registrada' ? (
            <>
              <Button
                variant="contained"
                color="success"
                startIcon={<CheckCircleIcon />}
                onClick={handleAprovarOcorrencia}
              >
                Aprovar Ocorrência
              </Button>
              <Button
                variant="contained"
                color="error"
                startIcon={<CancelIcon />}
                onClick={handleRejeitarOcorrencia}
              >
                Rejeitar Ocorrência
              </Button>
            </>
          ) : (
            <Button
              variant="contained"
              color="warning"
              startIcon={<EditIcon />}
              onClick={() => navigate(`/ocorrencias/${ocorrencia.id}/editar`)}
            >
              Editar Ocorrência
            </Button>
          )}

          {/* Botão de deletar apenas para admins */}
          <Button
            variant="contained"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={handleDeletarOcorrencia}
          >
            Excluir Ocorrência
          </Button>
        </Stack>
      </Box>

      {/* Snackbar para feedback de cópia */}
      <Snackbar
        open={copied}
        autoHideDuration={2000}
        onClose={() => setCopied(false)}
        message="Relatório copiado para a área de transferência!"
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      />
    </Box>
  );
};

export default OcorrenciaDetailsPage; 