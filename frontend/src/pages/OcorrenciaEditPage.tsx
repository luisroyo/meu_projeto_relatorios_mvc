import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  useTheme,
  Chip,
  CircularProgress,
  Snackbar,
  alpha
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  CalendarToday as CalendarIcon,
  LocationOn as LocationIcon,
  Description as DescriptionIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Category as CategoryIcon,
  Assignment as AssignmentIcon,
  Article as ArticleIcon,
  AutoFixHigh as AutoFixIcon
} from '@mui/icons-material';
import LoadingSpinner from '../components/LoadingSpinner';
import { ocorrenciaService, userService, analisadorService } from '../services/api';

// Cores modernas inspiradas no logo da empresa
const MODERN_COLORS = {
  primary: '#2E7D32', // Verde escuro elegante
  secondary: '#4CAF50', // Verde médio
  accent: '#81C784', // Verde claro
  success: '#66BB6A', // Verde sucesso
  warning: '#FFA726', // Laranja moderno
  error: '#EF5350', // Vermelho moderno
  info: '#42A5F5', // Azul moderno
  dark: '#1B5E20', // Verde muito escuro
  light: '#E8F5E8', // Verde muito claro
  background: '#F8FBF8', // Fundo verde claro
  surface: '#FFFFFF', // Branco puro
  text: '#2C3E50', // Azul escuro para texto
  textSecondary: '#7F8C8D' // Cinza para texto secundário
};

const OcorrenciaEditPage: React.FC = () => {
  const theme = useTheme();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const isNewOcorrencia = !id;

  // Estados principais
  const [ocorrencia, setOcorrencia] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Dados do formulário
  const [users, setUsers] = useState<any[]>([]);
  const [tipos, setTipos] = useState<any[]>([]);
  const [condominios, setCondominios] = useState<any[]>([]);
  const [colaboradores, setColaboradores] = useState<any[]>([]);
  const [orgaosPublicos, setOrgaosPublicos] = useState<any[]>([]);
  const [statusList, setStatusList] = useState<string[]>([]);

  // Form data
  const [formData, setFormData] = useState({
    condominio_id: '',
    supervisor_id: '',
    data_hora_ocorrencia: '',
    turno: '',
    ocorrencia_tipo_id: '',
    status: 'Registrada',
    endereco_especifico: '',
    colaboradores_envolvidos: [] as string[],
    orgaos_acionados: [] as string[]
  });

  // Relatório final
  const [relatorioFinal, setRelatorioFinal] = useState('');
  const [processandoRelatorio, setProcessandoRelatorio] = useState(false);

  useEffect(() => {
    if (id) {
      loadOcorrencia(parseInt(id));
    } else {
      // Nova ocorrência - verificar dados do analisador
      const relatorioProcessado = localStorage.getItem('novoRelatorioProcessado');
      const dadosExtraidosIA = localStorage.getItem('dadosExtraidosIA');

      if (relatorioProcessado) {
        console.log('Relatório processado encontrado no localStorage:', relatorioProcessado);
        setRelatorioFinal(relatorioProcessado);
        localStorage.removeItem('novoRelatorioProcessado');
      }

      if (dadosExtraidosIA) {
        try {
          const dadosIA = JSON.parse(dadosExtraidosIA);
          console.log('Dados extraídos pela IA:', dadosIA);
          localStorage.removeItem('dadosExtraidosIA');
        } catch (error) {
          console.error('Erro ao processar dados extraídos pela IA:', error);
        }
      }

      setLoading(false);
    }

    loadFormData();
  }, [id, location.state]);

  const loadOcorrencia = async (ocorrenciaId: number) => {
    try {
      const response = await ocorrenciaService.getById(ocorrenciaId);
      setOcorrencia(response);

      // Função para formatar data para o input datetime-local
      const formatDateForInput = (dateString: string) => {
        if (!dateString) return '';
        try {
          const date = new Date(dateString);
          return date.toISOString().slice(0, 16); // Formato: YYYY-MM-DDTHH:mm
        } catch {
          return '';
        }
      };

      setFormData({
        condominio_id: response.condominio_id?.toString() || '',
        supervisor_id: response.supervisor_id?.toString() || '',
        data_hora_ocorrencia: formatDateForInput(response.data_hora_ocorrencia),
        turno: response.turno || '',
        ocorrencia_tipo_id: response.ocorrencia_tipo_id?.toString() || '',
        status: response.status || 'Registrada',
        endereco_especifico: response.endereco_especifico || '',
        colaboradores_envolvidos: response.colaboradores_envolvidos?.map((c: any) => c.id.toString()) || [],
        orgaos_acionados: response.orgaos_acionados?.map((o: any) => o.id.toString()) || []
      });

      setRelatorioFinal(response.descricao || '');
    } catch (error: any) {
      console.error('Erro ao carregar ocorrência:', error);
      setError(error.message || 'Erro ao carregar ocorrência');
    } finally {
      setLoading(false);
    }
  };

  const loadFormData = async () => {
    try {
      const [usersResponse, tiposResponse, condominiosResponse, colaboradoresResponse, orgaosResponse] = await Promise.all([
        userService.list(),
        ocorrenciaService.getTipos(),
        ocorrenciaService.getCondominios(),
        ocorrenciaService.getColaboradores(),
        ocorrenciaService.getOrgaosPublicos()
      ]);

      setUsers(usersResponse.users || []);
      setTipos(tiposResponse.tipos || []);
      setCondominios(condominiosResponse.condominios || []);
      setColaboradores(colaboradoresResponse.colaboradores || []);
      setOrgaosPublicos(orgaosResponse.orgaos_publicos || []);
      setStatusList(['Registrada', 'Em Andamento', 'Concluída', 'Cancelada']);
    } catch (error: any) {
      console.error('Erro ao carregar dados do formulário:', error);
      setError('Erro ao carregar dados do formulário');
    }
  };

  const handleInputChange = (field: string, value: string | string[]) => {
    // Garantir que os valores dos selects sejam strings vazias se não houver valor válido
    let processedValue = value;
    if (typeof value === 'string' && (value === 'undefined' || value === 'null')) {
      processedValue = '';
    }

    setFormData(prev => ({
      ...prev,
      [field]: processedValue
    }));
  };

  const handleRelatorioChange = (value: string) => {
    setRelatorioFinal(value);
  };

  const handleProcessarRelatorio = async () => {
    if (!relatorioFinal.trim()) {
      setError('Por favor, insira um relatório final para analisar.');
      return;
    }

    setProcessandoRelatorio(true);
    setError(null);

    try {
      // Enviar o relatório final para análise e extração de dados
      const response = await analisadorService.analisarRelatorio(relatorioFinal);

      // Extrair informações do relatório processado
      const relatorioTexto = response.relatorio_processado;

      // Função para extrair data e hora
      const extrairDataHora = (texto: string) => {
        const dataMatch = texto.match(/Data:\s*(\d{2}\/\d{2}\/\d{4})/);
        const horaMatch = texto.match(/Hora:\s*(\d{2}:\d{2})/);

        if (dataMatch && horaMatch) {
          const [dia, mes, ano] = dataMatch[1].split('/');
          const [hora, minuto] = horaMatch[1].split(':');
          return `${ano}-${mes.padStart(2, '0')}-${dia.padStart(2, '0')}T${hora}:${minuto}`;
        }
        return '';
      };

      // Função para extrair local/endereço
      const extrairLocal = (texto: string) => {
        const localMatch = texto.match(/Local:\s*(.+?)(?:\n|$)/);
        return localMatch ? localMatch[1].trim() : '';
      };

      // Função para extrair turno baseado no horário
      const extrairTurno = (texto: string) => {
        const horaMatch = texto.match(/Hora:\s*(\d{2}):\d{2}/);
        if (horaMatch) {
          const hora = parseInt(horaMatch[1]);
          return hora >= 6 && hora < 18 ? 'Diurno' : 'Noturno';
        }
        return '';
      };

      // Função para extrair tipo de ocorrência
      const extrairTipoOcorrencia = (texto: string) => {
        const ocorrenciaMatch = texto.match(/Ocorrência:\s*(.+?)(?:\n|$)/);
        if (ocorrenciaMatch && tipos.length > 0) {
          const ocorrenciaTexto = ocorrenciaMatch[1].toLowerCase();

          // Buscar por palavras-chave nos tipos disponíveis
          for (const tipo of tipos) {
            const tipoNome = tipo.nome.toLowerCase();
            if (ocorrenciaTexto.includes(tipoNome) || tipoNome.includes(ocorrenciaTexto)) {
              return tipo.id.toString();
            }
          }

          // Buscar por palavras-chave específicas
          if (ocorrenciaTexto.includes('acidente') || ocorrenciaTexto.includes('colisão')) {
            const tipoAcidente = tipos.find(t => t.nome.toLowerCase().includes('acidente'));
            if (tipoAcidente) return tipoAcidente.id.toString();
          }

          if (ocorrenciaTexto.includes('furto') || ocorrenciaTexto.includes('roubo')) {
            const tipoFurto = tipos.find(t => t.nome.toLowerCase().includes('furto') || t.nome.toLowerCase().includes('roubo'));
            if (tipoFurto) return tipoFurto.id.toString();
          }

          if (ocorrenciaTexto.includes('verificação') || ocorrenciaTexto.includes('averiguação')) {
            const tipoVerificacao = tipos.find(t => t.nome.toLowerCase().includes('verificação'));
            if (tipoVerificacao) return tipoVerificacao.id.toString();
          }
        }
        return '';
      };

      // Extrair informações
      const dataHora = extrairDataHora(relatorioTexto);
      const local = extrairLocal(relatorioTexto);
      const turno = extrairTurno(relatorioTexto);
      const tipoOcorrencia = extrairTipoOcorrencia(relatorioTexto);

      // Atualizar formulário com as informações extraídas
      setFormData(prev => ({
        ...prev,
        data_hora_ocorrencia: dataHora || prev.data_hora_ocorrencia,
        endereco_especifico: local || prev.endereco_especifico,
        turno: turno || prev.turno,
        ocorrencia_tipo_id: tipoOcorrencia || prev.ocorrencia_tipo_id,
      }));

      setSuccessMessage('Campos preenchidos automaticamente com base no relatório!');
    } catch (error: any) {
      console.error('Erro ao analisar relatório:', error);
      setError(error.message || 'Erro ao analisar relatório');
    } finally {
      setProcessandoRelatorio(false);
    }
  };

  const handleSave = async () => {
    if (!relatorioFinal.trim()) {
      setError('O relatório final é obrigatório.');
      return;
    }

    if (!formData.ocorrencia_tipo_id) {
      setError('O tipo de ocorrência é obrigatório.');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const ocorrenciaData = {
        relatorio_final: relatorioFinal,
        ocorrencia_tipo_id: parseInt(formData.ocorrencia_tipo_id),
        condominio_id: formData.condominio_id ? parseInt(formData.condominio_id) : undefined,
        supervisor_id: formData.supervisor_id ? parseInt(formData.supervisor_id) : undefined,
        turno: formData.turno,
        status: formData.status,
        endereco_especifico: formData.endereco_especifico,
        data_hora_ocorrencia: formData.data_hora_ocorrencia,
        colaboradores_envolvidos: formData.colaboradores_envolvidos.length > 0 ? formData.colaboradores_envolvidos.map(id => parseInt(id)) : [],
        orgaos_acionados: formData.orgaos_acionados.length > 0 ? formData.orgaos_acionados.map(id => parseInt(id)) : []
      };

      if (isNewOcorrencia) {
        await ocorrenciaService.create(ocorrenciaData);
        setSuccessMessage('Ocorrência registrada com sucesso!');
      } else {
        await ocorrenciaService.update(parseInt(id), ocorrenciaData);
        setSuccessMessage('Ocorrência atualizada com sucesso!');
      }

      setTimeout(() => {
        navigate('/ocorrencias');
      }, 2000);
    } catch (error: any) {
      console.error('Erro ao salvar ocorrência:', error);
      setError(error.message || 'Erro ao salvar ocorrência');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingSpinner message="Carregando ocorrência..." size="large" />;
  }

  if (error && !isNewOcorrencia && !ocorrencia) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          Ocorrência não encontrada
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
    <Box sx={{
      backgroundColor: MODERN_COLORS.background,
      minHeight: '100vh',
      py: 4
    }}>
      <Box sx={{ maxWidth: '1400px', mx: 'auto', px: 2 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" component="h1" sx={{
            fontWeight: 700,
            background: `linear-gradient(135deg, ${MODERN_COLORS.primary}, ${MODERN_COLORS.secondary})`,
            backgroundClip: 'text',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 1,
            display: 'flex',
            alignItems: 'center'
          }}>
            <DescriptionIcon sx={{ mr: 2, fontSize: 36, color: MODERN_COLORS.primary }} />
            {isNewOcorrencia ? 'Registrar Nova Ocorrência' : `Editar Ocorrência #${ocorrencia?.id}`}
          </Typography>
          <Typography variant="h6" sx={{ color: MODERN_COLORS.textSecondary }}>
            Preencha os campos abaixo para registrar a ocorrência no sistema.
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 4 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 4 }}>
          {/* Coluna Esquerda - Campos do Formulário */}
          <Box sx={{ flex: { xs: 1, lg: 7 } }}>
            {/* Contexto da Ocorrência */}
            <Card sx={{
              borderRadius: 4,
              boxShadow: '0 8px 32px rgba(46, 125, 50, 0.1)',
              mb: 3,
              overflow: 'visible',
              border: `1px solid ${alpha(MODERN_COLORS.primary, 0.1)}`
            }}>
              <Box sx={{
                background: `linear-gradient(135deg, ${MODERN_COLORS.primary}, ${MODERN_COLORS.secondary})`,
                p: 3,
                borderRadius: '16px 16px 0 0',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <Box sx={{
                  position: 'absolute',
                  top: 0,
                  right: 0,
                  width: '100px',
                  height: '100px',
                  background: `radial-gradient(circle, ${alpha(MODERN_COLORS.accent, 0.3)} 0%, transparent 70%)`,
                  transform: 'translate(30px, -30px)'
                }} />
                <Typography variant="h6" sx={{
                  fontWeight: 600,
                  color: MODERN_COLORS.surface,
                  display: 'flex',
                  alignItems: 'center',
                  position: 'relative',
                  zIndex: 1
                }}>
                  <LocationIcon sx={{ mr: 1.5, fontSize: 24 }} />
                  Contexto da Ocorrência
                </Typography>
              </Box>
              <CardContent sx={{ p: 4, backgroundColor: MODERN_COLORS.surface }}>
                <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
                  <FormControl fullWidth>
                    <InputLabel sx={{ color: MODERN_COLORS.textSecondary }}>CONDOMÍNIO</InputLabel>
                    <Select
                      value={formData.condominio_id}
                      onChange={(e) => handleInputChange('condominio_id', e.target.value)}
                      label="CONDOMÍNIO"
                      startAdornment={<BusinessIcon sx={{ mr: 1, color: MODERN_COLORS.primary }} />}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '&:hover fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                        },
                      }}
                    >
                      <MenuItem value="">
                        <em>-- Selecione um Condomínio --</em>
                      </MenuItem>
                      {condominios.map((condominio) => (
                        <MenuItem key={condominio.id} value={condominio.id}>
                          {condominio.nome}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel sx={{ color: MODERN_COLORS.textSecondary }}>SUPERVISOR</InputLabel>
                    <Select
                      value={formData.supervisor_id}
                      onChange={(e) => handleInputChange('supervisor_id', e.target.value)}
                      label="SUPERVISOR"
                      startAdornment={<PersonIcon sx={{ mr: 1, color: MODERN_COLORS.primary }} />}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '&:hover fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                        },
                      }}
                    >
                      <MenuItem value="">
                        <em>-- Selecione um Supervisor --</em>
                      </MenuItem>
                      {users.filter((user: any) => user.is_supervisor === true).map((user) => (
                        <MenuItem key={user.id} value={user.id}>
                          {user.username}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>

                <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3, mt: 3 }}>
                  <TextField
                    label="DATA E HORA DA OCORRÊNCIA"
                    type="datetime-local"
                    value={formData.data_hora_ocorrencia}
                    onChange={(e) => handleInputChange('data_hora_ocorrencia', e.target.value)}
                    fullWidth
                    InputProps={{
                      startAdornment: (
                        <CalendarIcon sx={{ mr: 1, color: MODERN_COLORS.primary }} />
                      ),
                    }}
                    InputLabelProps={{
                      shrink: true,
                      sx: { color: MODERN_COLORS.textSecondary }
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '&:hover fieldset': {
                          borderColor: MODERN_COLORS.primary,
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: MODERN_COLORS.primary,
                        },
                      },
                    }}
                  />

                  <FormControl fullWidth>
                    <InputLabel sx={{ color: MODERN_COLORS.textSecondary }}>TURNO</InputLabel>
                    <Select
                      value={formData.turno}
                      onChange={(e) => handleInputChange('turno', e.target.value)}
                      label="TURNO"
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '&:hover fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                        },
                      }}
                    >
                      <MenuItem value="Diurno">Diurno</MenuItem>
                      <MenuItem value="Noturno">Noturno</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
              </CardContent>
            </Card>

            {/* Detalhes do Registro */}
            <Card sx={{
              borderRadius: 4,
              boxShadow: '0 8px 32px rgba(76, 175, 80, 0.1)',
              mb: 3,
              overflow: 'visible',
              border: `1px solid ${alpha(MODERN_COLORS.secondary, 0.1)}`
            }}>
              <Box sx={{
                background: `linear-gradient(135deg, ${MODERN_COLORS.secondary}, ${MODERN_COLORS.accent})`,
                p: 3,
                borderRadius: '16px 16px 0 0',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <Box sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '80px',
                  height: '80px',
                  background: `radial-gradient(circle, ${alpha(MODERN_COLORS.light, 0.4)} 0%, transparent 70%)`,
                  transform: 'translate(-20px, -20px)'
                }} />
                <Typography variant="h6" sx={{
                  fontWeight: 600,
                  color: MODERN_COLORS.surface,
                  display: 'flex',
                  alignItems: 'center',
                  position: 'relative',
                  zIndex: 1
                }}>
                  <AssignmentIcon sx={{ mr: 1.5, fontSize: 24 }} />
                  Detalhes do Registro
                </Typography>
              </Box>
              <CardContent sx={{ p: 4, backgroundColor: MODERN_COLORS.surface }}>
                <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
                  <FormControl fullWidth>
                    <InputLabel sx={{ color: MODERN_COLORS.textSecondary }}>TIPO DA OCORRÊNCIA *</InputLabel>
                    <Select
                      value={formData.ocorrencia_tipo_id}
                      onChange={(e) => handleInputChange('ocorrencia_tipo_id', e.target.value)}
                      label="TIPO DA OCORRÊNCIA *"
                      error={!formData.ocorrencia_tipo_id && error?.includes('tipo')}
                      startAdornment={<CategoryIcon sx={{ mr: 1, color: MODERN_COLORS.primary }} />}
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '&:hover fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                        },
                      }}
                    >
                      <MenuItem value="">
                        <em>-- Selecione um Tipo --</em>
                      </MenuItem>
                      {tipos.map((tipo) => (
                        <MenuItem key={tipo.id} value={tipo.id}>
                          {tipo.nome}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel sx={{ color: MODERN_COLORS.textSecondary }}>STATUS</InputLabel>
                    <Select
                      value={formData.status}
                      onChange={(e) => handleInputChange('status', e.target.value)}
                      label="STATUS"
                      sx={{
                        '& .MuiOutlinedInput-root': {
                          '&:hover fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                          '&.Mui-focused fieldset': {
                            borderColor: MODERN_COLORS.primary,
                          },
                        },
                      }}
                    >
                      {statusList.map((status) => (
                        <MenuItem key={status} value={status}>
                          <Chip
                            label={status}
                            size="small"
                            sx={{
                              backgroundColor:
                                status === 'Concluída' ? MODERN_COLORS.success :
                                  status === 'Em Andamento' ? MODERN_COLORS.warning :
                                    status === 'Cancelada' ? MODERN_COLORS.error :
                                      MODERN_COLORS.light,
                              color:
                                status === 'Concluída' || status === 'Em Andamento' || status === 'Cancelada'
                                  ? MODERN_COLORS.surface
                                  : MODERN_COLORS.text,
                              fontWeight: 500
                            }}
                          />
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Box>

                <TextField
                  label="ENDEREÇO ESPECÍFICO (OPCIONAL)"
                  value={formData.endereco_especifico}
                  onChange={(e) => handleInputChange('endereco_especifico', e.target.value)}
                  fullWidth
                  placeholder="Digite o endereço específico"
                  InputProps={{
                    startAdornment: (
                      <LocationIcon sx={{ mr: 1, color: MODERN_COLORS.primary }} />
                    ),
                  }}
                  InputLabelProps={{
                    sx: { color: MODERN_COLORS.textSecondary }
                  }}
                  sx={{
                    mt: 3,
                    '& .MuiOutlinedInput-root': {
                      '&:hover fieldset': {
                        borderColor: MODERN_COLORS.primary,
                      },
                      '&.Mui-focused fieldset': {
                        borderColor: MODERN_COLORS.primary,
                      },
                    },
                  }}
                />

                <FormControl fullWidth sx={{ mt: 3 }}>
                  <InputLabel sx={{ color: MODERN_COLORS.textSecondary }}>COLABORADORES ENVOLVIDOS</InputLabel>
                  <Select
                    multiple
                    value={formData.colaboradores_envolvidos}
                    onChange={(e) => handleInputChange('colaboradores_envolvidos', e.target.value as string[])}
                    label="COLABORADORES ENVOLVIDOS"
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => {
                          const colaborador = colaboradores.find(c => c.id.toString() === value);
                          return (
                            <Chip
                              key={value}
                              label={colaborador?.nome || value}
                              size="small"
                              sx={{
                                backgroundColor: MODERN_COLORS.primary,
                                color: MODERN_COLORS.surface,
                                fontWeight: 500
                              }}
                            />
                          );
                        })}
                      </Box>
                    )}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '&:hover fieldset': {
                          borderColor: MODERN_COLORS.primary,
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: MODERN_COLORS.primary,
                        },
                      },
                    }}
                  >
                    {colaboradores.map((colaborador) => (
                      <MenuItem key={colaborador.id} value={colaborador.id.toString()}>
                        {colaborador.nome}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mt: 3 }}>
                  <InputLabel sx={{ color: MODERN_COLORS.textSecondary }}>ÓRGÃOS PÚBLICOS ACIONADOS</InputLabel>
                  <Select
                    multiple
                    value={formData.orgaos_acionados}
                    onChange={(e) => handleInputChange('orgaos_acionados', e.target.value as string[])}
                    label="ÓRGÃOS PÚBLICOS ACIONADOS"
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => {
                          const orgao = orgaosPublicos.find(o => o.id.toString() === value);
                          return (
                            <Chip
                              key={value}
                              label={orgao?.nome || value}
                              size="small"
                              sx={{
                                backgroundColor: MODERN_COLORS.secondary,
                                color: MODERN_COLORS.surface,
                                fontWeight: 500
                              }}
                            />
                          );
                        })}
                      </Box>
                    )}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        '&:hover fieldset': {
                          borderColor: MODERN_COLORS.primary,
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: MODERN_COLORS.primary,
                        },
                      },
                    }}
                  >
                    {orgaosPublicos.map((orgao) => (
                      <MenuItem key={orgao.id} value={orgao.id.toString()}>
                        {orgao.nome}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </CardContent>
            </Card>
          </Box>

          {/* Coluna Direita - Relatório e Botões */}
          <Box sx={{ flex: { xs: 1, lg: 5 } }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              {/* Relatório Final */}
              <Card sx={{
                borderRadius: 4,
                boxShadow: '0 8px 32px rgba(66, 165, 245, 0.1)',
                flexGrow: 1,
                mb: 3,
                overflow: 'visible',
                border: `1px solid ${alpha(MODERN_COLORS.info, 0.1)}`
              }}>
                <Box sx={{
                  background: `linear-gradient(135deg, ${MODERN_COLORS.info}, ${MODERN_COLORS.accent})`,
                  p: 3,
                  borderRadius: '16px 16px 0 0',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  position: 'relative',
                  overflow: 'hidden'
                }}>
                  <Box sx={{
                    position: 'absolute',
                    top: 0,
                    right: 0,
                    width: '60px',
                    height: '60px',
                    background: `radial-gradient(circle, ${alpha(MODERN_COLORS.light, 0.3)} 0%, transparent 70%)`,
                    transform: 'translate(20px, -20px)'
                  }} />
                  <Typography variant="h6" sx={{
                    fontWeight: 600,
                    color: MODERN_COLORS.surface,
                    display: 'flex',
                    alignItems: 'center',
                    position: 'relative',
                    zIndex: 1
                  }}>
                    <ArticleIcon sx={{ mr: 1.5, fontSize: 24 }} />
                    Relatório Final Oficial
                  </Typography>
                </Box>

                <CardContent sx={{ p: 3, backgroundColor: MODERN_COLORS.surface }}>
                  {/* Campo para Relatório Final */}
                  <Typography variant="subtitle1" sx={{ mb: 2, fontWeight: 600, color: MODERN_COLORS.textSecondary }}>
                    Relatório Final *
                  </Typography>
                  <TextField
                    label="Relatório Final *"
                    value={relatorioFinal}
                    onChange={(e) => handleRelatorioChange(e.target.value)}
                    fullWidth
                    multiline
                    rows={20}
                    placeholder="Descreva detalhadamente a ocorrência..."
                    InputLabelProps={{
                      sx: { color: MODERN_COLORS.textSecondary }
                    }}
                    sx={{
                      mb: 2,
                      '& .MuiInputBase-root': {
                        minHeight: '400px',
                        resize: 'vertical',
                        '&:hover fieldset': {
                          borderColor: MODERN_COLORS.primary,
                        },
                        '&.Mui-focused fieldset': {
                          borderColor: MODERN_COLORS.primary,
                        },
                      }
                    }}
                  />

                  <Button
                    variant="outlined"
                    startIcon={processandoRelatorio ? <CircularProgress size={16} /> : <AutoFixIcon />}
                    onClick={handleProcessarRelatorio}
                    disabled={processandoRelatorio || !relatorioFinal.trim()}
                    sx={{
                      borderColor: MODERN_COLORS.secondary,
                      color: MODERN_COLORS.secondary,
                      '&:hover': {
                        borderColor: MODERN_COLORS.primary,
                        backgroundColor: alpha(MODERN_COLORS.secondary, 0.1),
                      },
                    }}
                  >
                    {processandoRelatorio ? 'Analisando...' : 'Analisar e Preencher'}
                  </Button>
                </CardContent>
              </Card>

              {/* Botões de Ação */}
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
                  onClick={handleSave}
                  disabled={saving || !relatorioFinal.trim() || !formData.ocorrencia_tipo_id}
                  sx={{
                    background: `linear-gradient(135deg, ${MODERN_COLORS.primary}, ${MODERN_COLORS.secondary})`,
                    fontWeight: 600,
                    boxShadow: '0 4px 12px rgba(46, 125, 50, 0.3)',
                    '&:hover': {
                      background: `linear-gradient(135deg, ${MODERN_COLORS.dark}, ${MODERN_COLORS.primary})`,
                      transform: 'translateY(-2px)',
                      boxShadow: '0 6px 20px rgba(46, 125, 50, 0.4)'
                    },
                    '&:disabled': {
                      background: MODERN_COLORS.textSecondary,
                      transform: 'none',
                      boxShadow: 'none'
                    },
                    transition: 'all 0.3s ease-in-out',
                    px: 4,
                    py: 1.5,
                    fontSize: '1.1rem'
                  }}
                >
                  {saving ? 'Salvando...' : (isNewOcorrencia ? 'Registrar Ocorrência' : 'Salvar Alterações')}
                </Button>
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Snackbar para mensagens de sucesso */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={6000}
        onClose={() => setSuccessMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSuccessMessage(null)}
          severity="success"
          sx={{
            width: '100%',
            backgroundColor: MODERN_COLORS.success,
            color: MODERN_COLORS.surface,
            fontWeight: 600
          }}
        >
          {successMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default OcorrenciaEditPage; 