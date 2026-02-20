import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  alpha
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
  CalendarToday as CalendarIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Assignment as AssignmentIcon,
  WhatsApp as WhatsAppIcon,
  AutoFixHigh as AutoFixIcon
} from '@mui/icons-material';
import LoadingSpinner from '../components/LoadingSpinner';
import { rondaService, ocorrenciaService, userService } from '../services/api';

// Cores modernas
const MODERN_COLORS = {
  primary: '#2E7D32',
  secondary: '#4CAF50',
  accent: '#81C784',
  success: '#66BB6A',
  warning: '#FFA726',
  error: '#EF5350',
  info: '#42A5F5',
  dark: '#1B5E20',
  light: '#E8F5E8',
  background: '#F8FBF8',
  surface: '#FFFFFF',
  text: '#2C3E50',
  textSecondary: '#7F8C8D'
};

const RondaEditPage: React.FC = () => {
  const theme = useTheme();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isNewRonda = !id;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [processingWhatsapp, setProcessingWhatsapp] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Form selections options
  const [users, setUsers] = useState<any[]>([]);
  const [condominios, setCondominios] = useState<any[]>([]);
  const [statusList] = useState<string[]>(['Realizada', 'Em Andamento', 'Não Realizada']);
  const [turnos] = useState<string[]>(['Noturno Par', 'Noturno Impar', 'Diurno Par', 'Diurno Impar']);

  // Formulário
  const [formData, setFormData] = useState({
    condominio_id: '',
    supervisor_id: '',
    data_inicio: new Date().toISOString().split('T')[0],
    turno: '',
    status: 'Realizada',
    observacoes: ''
  });

  // Texto processado
  const [relatorioFinal, setRelatorioFinal] = useState('');
  const [logBruto, setLogBruto] = useState('');

  useEffect(() => {
    loadFormData();
    if (id) {
      loadRonda(parseInt(id));
    } else {
      setLoading(false);
    }
  }, [id]);

  const loadRonda = async (rondaId: number) => {
    try {
      const response = await rondaService.getById(rondaId);
      setFormData({
        condominio_id: response.condominio_id?.toString() || '',
        supervisor_id: response.supervisor_id?.toString() || '',
        data_inicio: response.data_inicio ? new Date(response.data_inicio).toISOString().split('T')[0] : '',
        turno: '', // Rondas não tinham turno estrito antes, então omitido
        status: response.status || 'Realizada',
        observacoes: response.observacoes || ''
      });
    } catch (error: any) {
      console.error('Erro ao carregar ronda:', error);
      setError(error.message || 'Erro ao carregar ronda');
    } finally {
      setLoading(false);
    }
  };

  const loadFormData = async () => {
    try {
      const [usersResponse, condominiosResponse] = await Promise.all([
        userService.list(),
        ocorrenciaService.getCondominios()
      ]);

      setUsers(usersResponse.users || []);
      setCondominios(condominiosResponse.condominios || []);
    } catch (error: any) {
      console.error('Erro ao carregar dados do formulário:', error);
      setError('Erro ao carregar dados do formulário');
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleProcessarWhatsApp = async () => {
    if (!formData.condominio_id) {
      setError('O Condomínio é obrigatório para importar do WhatsApp.');
      return;
    }
    if (!formData.data_inicio) {
      setError('A Data do Plantão é obrigatória para importar do WhatsApp.');
      return;
    }
    if (!formData.turno) {
      setError('O Turno é obrigatório para definir o horário da busca (ex: 18h às 06h).');
      return;
    }

    setProcessingWhatsapp(true);
    setError(null);
    setSuccessMessage(null);

    // Calcular data_fim baseado no turno (12h de duração como base)
    const startDate = new Date(formData.data_inicio);
    const dataFim = new Date(startDate.getTime() + 24 * 60 * 60 * 1000).toISOString().split('T')[0];

    try {
      const response = await rondaService.processarWhatsApp({
        condominio_id: parseInt(formData.condominio_id),
        data_inicio: formData.data_inicio,
        data_fim: dataFim // backend filtra horas internamente ou podemos passar data-hora
      });

      if (response.success && response.relatorio_processado) {
        setRelatorioFinal(response.relatorio_processado);
        setLogBruto(response.log_bruto || 'Nenhum log bruto recuperado.');
        setSuccessMessage('Log do WhatsApp processado! Corrija possíveis erros antes de salvar.');
      } else {
        setError(response.message || 'Nenhuma ronda encontrada neste período.');
      }
    } catch (error: any) {
      console.error('Erro ao processar WhatsApp:', error);
      setError(error.message || 'Erro ao buscar mensagens do WhatsApp.');
    } finally {
      setProcessingWhatsapp(false);
    }
  };

  const handleSave = async () => {
    if (!formData.condominio_id || !formData.supervisor_id || !formData.data_inicio) {
      setError('Preencha os campos obrigatórios (Condomínio, Supervisor e Data).');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      const rondaData = {
        condominio_id: parseInt(formData.condominio_id),
        supervisor_id: parseInt(formData.supervisor_id),
        data_inicio: formData.data_inicio,
        status: formData.status,
        observacoes: (relatorioFinal + '\\n\\n' + formData.observacoes).trim()
      };

      if (isNewRonda) {
        await rondaService.create(rondaData);
        setSuccessMessage('Ronda registrada com sucesso!');
      } else {
        await rondaService.update(parseInt(id!), rondaData);
        setSuccessMessage('Ronda atualizada com sucesso!');
      }

      setTimeout(() => navigate('/rondas'), 2000);
    } catch (error: any) {
      console.error('Erro ao salvar ronda:', error);
      setError(error.message || 'Erro ao salvar ronda');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSpinner message="Carregando..." size="large" />;

  return (
    <Box sx={{ backgroundColor: MODERN_COLORS.background, minHeight: '100vh', py: 4 }}>
      <Box sx={{ maxWidth: '1400px', mx: 'auto', px: 2 }}>
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h3" sx={{ fontWeight: 700, color: MODERN_COLORS.primary, display: 'flex', alignItems: 'center' }}>
              <AssignmentIcon sx={{ mr: 2, fontSize: 36 }} />
              {isNewRonda ? 'Registrar Nova Ronda (Correção Mágica)' : `Editar Ronda #${id}`}
            </Typography>
            <Typography variant="h6" color="textSecondary">
              Busque as rondas do WhatsApp ou insira manualmente.
            </Typography>
          </Box>
          <Button variant="outlined" startIcon={<ArrowBackIcon />} onClick={() => navigate('/rondas')}>
            Voltar
          </Button>
        </Box>

        {error && <Alert severity="error" sx={{ mb: 4 }} onClose={() => setError(null)}>{error}</Alert>}
        {successMessage && <Alert severity="success" sx={{ mb: 4 }} onClose={() => setSuccessMessage(null)}>{successMessage}</Alert>}

        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', lg: 'row' }, gap: 4 }}>
          {/* Coluna Esquerda - Filtros / Metadados */}
          <Box sx={{ flex: { xs: 1, lg: 5 } }}>
            <Card sx={{ borderRadius: 4, boxShadow: '0 8px 32px rgba(46, 125, 50, 0.1)', mb: 3 }}>
              <Box sx={{ background: `linear-gradient(135deg, ${MODERN_COLORS.primary}, ${MODERN_COLORS.secondary})`, p: 3, borderRadius: '16px 16px 0 0' }}>
                <Typography variant="h6" sx={{ color: MODERN_COLORS.surface, fontWeight: 600 }}>Parâmetros do Plantão</Typography>
              </Box>
              <CardContent sx={{ p: 4 }}>
                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>CONDOMÍNIO *</InputLabel>
                  <Select value={formData.condominio_id} onChange={(e) => handleInputChange('condominio_id', e.target.value)} label="CONDOMÍNIO *">
                    <MenuItem value=""><em>-- Selecione --</em></MenuItem>
                    {condominios.map((c) => <MenuItem key={c.id} value={c.id}>{c.nome}</MenuItem>)}
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>SUPERVISOR *</InputLabel>
                  <Select value={formData.supervisor_id} onChange={(e) => handleInputChange('supervisor_id', e.target.value)} label="SUPERVISOR *">
                    <MenuItem value=""><em>-- Selecione --</em></MenuItem>
                    {users.filter((u: any) => u.is_supervisor).map((u) => <MenuItem key={u.id} value={u.id}>{u.username}</MenuItem>)}
                  </Select>
                </FormControl>

                <TextField
                  fullWidth
                  label="DATA DO PLANTÃO *"
                  type="date"
                  value={formData.data_inicio}
                  onChange={(e) => handleInputChange('data_inicio', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  sx={{ mb: 3 }}
                />

                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>TURNO *</InputLabel>
                  <Select value={formData.turno} onChange={(e) => handleInputChange('turno', e.target.value)} label="TURNO *">
                    <MenuItem value=""><em>-- Selecione --</em></MenuItem>
                    {turnos.map((t) => <MenuItem key={t} value={t}>{t}</MenuItem>)}
                  </Select>
                </FormControl>

                <FormControl fullWidth sx={{ mb: 3 }}>
                  <InputLabel>STATUS</InputLabel>
                  <Select value={formData.status} onChange={(e) => handleInputChange('status', e.target.value)} label="STATUS">
                    {statusList.map((s) => <MenuItem key={s} value={s}>{s}</MenuItem>)}
                  </Select>
                </FormControl>

                {isNewRonda && (
                   <Button
                     fullWidth
                     variant="contained"
                     color="success"
                     size="large"
                     sx={{ py: 2, mt: 2, borderRadius: 2 }}
                     startIcon={processingWhatsapp ? <CircularProgress size={20} color="inherit" /> : <WhatsAppIcon />}
                     onClick={handleProcessarWhatsApp}
                     disabled={processingWhatsapp}
                   >
                     {processingWhatsapp ? 'Buscando do WhatsApp...' : 'Processar WhatsApp (Correção Mágica)'}
                   </Button>
                )}
              </CardContent>
            </Card>
          </Box>

          {/* Coluna Direita - Textos da Ronda */}
          <Box sx={{ flex: { xs: 1, lg: 7 } }}>
            <Card sx={{ borderRadius: 4, height: '100%', boxShadow: '0 8px 32px rgba(66, 165, 245, 0.1)' }}>
              <Box sx={{ background: `linear-gradient(135deg, ${MODERN_COLORS.info}, ${MODERN_COLORS.accent})`, p: 3, borderRadius: '16px 16px 0 0' }}>
                <Typography variant="h6" sx={{ color: MODERN_COLORS.surface, fontWeight: 600 }}>Log Processado / Observações</Typography>
              </Box>
              <CardContent sx={{ p: 4 }}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Revise o texto extraído do WhatsApp. Você pode corrigir as falhas manualmente antes de salvar.
                </Typography>

                {isNewRonda && (
                  <TextField
                    fullWidth
                    multiline
                    rows={12}
                    variant="outlined"
                    placeholder="O relatório corrigido aparecerá aqui..."
                    value={relatorioFinal}
                    onChange={(e) => setRelatorioFinal(e.target.value)}
                    sx={{ mb: 4, '& .MuiOutlinedInput-root': { backgroundColor: MODERN_COLORS.light, fontFamily: 'monospace' } }}
                  />
                )}

                <TextField
                  fullWidth
                  multiline
                  rows={isNewRonda ? 4 : 12}
                  label="Observações Adicionais"
                  value={formData.observacoes}
                  onChange={(e) => handleInputChange('observacoes', e.target.value)}
                  placeholder="Se houver alguma anotação extra, digite aqui..."
                />

                <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={handleSave}
                    disabled={saving}
                    startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                    sx={{ px: 4, py: 1.5, borderRadius: 2, background: `linear-gradient(135deg, ${MODERN_COLORS.primary}, ${MODERN_COLORS.secondary})` }}
                  >
                    {saving ? 'Salvando...' : 'Salvar no Sistema'}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default RondaEditPage;
