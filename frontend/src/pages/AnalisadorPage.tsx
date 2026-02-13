import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Send as SendIcon,
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
  Clear as ClearIcon,
  Psychology as RobotIcon,
  Keyboard as KeyboardIcon,
  AutoFixHigh as AutoFixIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import LoadingSpinner from '../components/LoadingSpinner';
import { analisadorService } from '../services/api';
import { ocorrenciaService } from '../services/api';

const AnalisadorPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Estados
  const [relatorioBruto, setRelatorioBruto] = useState('');
  const [classificacao, setClassificacao] = useState('');
  const [relatorioProcessado, setRelatorioProcessado] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [ocorrenciasPendentes, setOcorrenciasPendentes] = useState(0);

  // Carregar ocorrências pendentes
  const loadOcorrenciasPendentes = async () => {
    try {
      const response = await ocorrenciaService.list({ status: 'Pendente', per_page: 1 });
      setOcorrenciasPendentes(response.pagination?.total || 0);
    } catch (error) {
      console.error('Erro ao carregar ocorrências pendentes:', error);
    }
  };

  useEffect(() => {
    loadOcorrenciasPendentes();
  }, []);

  const handleProcessarRelatorio = async () => {
    if (!relatorioBruto.trim()) {
      toast.error('Por favor, insira um relatório para processar');
      return;
    }

    setLoading(true);
    try {
      const response = await analisadorService.analisarRelatorio(relatorioBruto);
      setClassificacao(response.classificacao);
      setRelatorioProcessado(response.relatorio_processado);
      toast.success('Relatório processado com sucesso!');
    } catch (error: any) {
      console.error('Erro ao processar relatório:', error);
      toast.error(error.message || 'Erro ao processar relatório');
    } finally {
      setLoading(false);
    }
  };

  const handleCopiarResultado = async () => {
    const textoParaCopiar = relatorioProcessado || relatorioBruto;
    if (!textoParaCopiar) {
      toast.error('Nenhum texto para copiar');
      return;
    }

    try {
      await navigator.clipboard.writeText(textoParaCopiar);
      setCopied(true);
      toast.success('Texto copiado para a área de transferência!');
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Erro ao copiar:', error);
      toast.error('Erro ao copiar texto');
    }
  };

  const handleExportarOcorrencia = () => {
    if (!relatorioProcessado) {
      toast.error('Processe um relatório primeiro');
      return;
    }

    try {
      console.log('Exportando dados para ocorrência:', {
        relatorioProcessado,
        classificacao,
        relatorioBruto
      });

      // Salvar relatório processado (padrão esperado pela página de ocorrência)
      localStorage.setItem('novoRelatorioProcessado', relatorioProcessado);

      // Salvar dados extraídos pela IA (se houver)
      if (classificacao) {
        const dadosExtraidos = {
          classificacao: classificacao,
          relatorio_original: relatorioBruto,
          data_processamento: new Date().toISOString(),
          origem: 'analisador'
        };
        localStorage.setItem('dadosExtraidosIA', JSON.stringify(dadosExtraidos));
        console.log('Dados extraídos salvos:', dadosExtraidos);
      }

      // Navegar para a página de criação de ocorrência
      navigate('/ocorrencias/nova');

      toast.success('Dados exportados! Preencha os campos restantes na página de ocorrência.');
    } catch (error) {
      console.error('Erro ao exportar ocorrência:', error);
      toast.error('Erro ao exportar dados para ocorrência');
    }
  };

  const handleLimparCampos = () => {
    setRelatorioBruto('');
    setClassificacao('');
    setRelatorioProcessado('');
    setCopied(false);
  };

  const handleCharCount = (text: string) => {
    return text.length;
  };

  return (
    <Box sx={{ p: 3, maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h3" component="h1" sx={{
          fontWeight: 700,
          background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          mb: 1
        }}>
          Analisador de Relatórios
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Processe relatórios brutos e extraia informações estruturadas
        </Typography>
      </Box>

      {/* Estatísticas */}
      <Box sx={{ mb: 4 }}>
        <Card sx={{ p: 2, background: theme.palette.info.light }}>
          <Typography variant="body2" color="text.secondary">
            📊 <strong>{ocorrenciasPendentes}</strong> ocorrências pendentes de análise
          </Typography>
        </Card>
      </Box>

      {/* Layout Principal */}
      <Box sx={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', gap: 3 }}>
        {/* Coluna Esquerda - Input */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Card sx={{ borderRadius: 3, height: 'fit-content' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <RobotIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  1. Relatório Bruto
                </Typography>
              </Box>

              <TextField
                multiline
                rows={12}
                fullWidth
                variant="outlined"
                placeholder="Cole aqui o relatório bruto que deseja processar..."
                value={relatorioBruto}
                onChange={(e) => setRelatorioBruto(e.target.value)}
                sx={{ mb: 2 }}
                helperText={`${handleCharCount(relatorioBruto)} caracteres`}
              />

              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  startIcon={<SendIcon />}
                  onClick={handleProcessarRelatorio}
                  disabled={loading || !relatorioBruto.trim()}
                  sx={{ flex: 1, minWidth: 200 }}
                >
                  {loading ? 'Processando...' : 'Processar Relatório'}
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<ClearIcon />}
                  onClick={handleLimparCampos}
                  disabled={loading}
                >
                  Limpar
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Box>

        {/* Coluna Direita - Resultados */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Card sx={{ borderRadius: 3, height: 'fit-content' }}>
            <CardContent sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <AutoFixIcon color="secondary" sx={{ mr: 1 }} />
                <Typography variant="h6" fontWeight={600}>
                  2. Relatório Corrigido
                </Typography>
              </Box>

              {loading ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <LoadingSpinner message="Processando relatório..." size="medium" />
                </Box>
              ) : relatorioProcessado ? (
                <Box>
                  {/* Resultado da Análise */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="subtitle1" color="text.secondary" gutterBottom sx={{ fontWeight: 600 }}>
                      Resultado da Análise:
                    </Typography>
                    <TextField
                      multiline
                      rows={12}
                      fullWidth
                      variant="outlined"
                      value={relatorioProcessado}
                      InputProps={{ readOnly: true }}
                      sx={{
                        '& .MuiInputBase-root': {
                          backgroundColor: theme.palette.background.default,
                          opacity: 0.7
                        }
                      }}
                    />
                  </Box>

                  {/* Ações */}
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <Button
                      variant="outlined"
                      startIcon={copied ? <CheckIcon /> : <CopyIcon />}
                      onClick={handleCopiarResultado}
                      sx={{ flex: 1, minWidth: 150 }}
                    >
                      {copied ? 'Copiado!' : 'Copiar'}
                    </Button>

                    <Button
                      variant="contained"
                      startIcon={<DownloadIcon />}
                      onClick={handleExportarOcorrencia}
                      color="secondary"
                      sx={{ flex: 1, minWidth: 150 }}
                    >
                      Exportar Ocorrência
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <KeyboardIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                  <Typography variant="body1" color="text.secondary">
                    Insira um relatório e clique em "Processar" para ver os resultados
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

export default AnalisadorPage; 
