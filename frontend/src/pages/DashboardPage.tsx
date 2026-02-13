import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../hooks';
import { fetchDashboardStats, fetchRecentOcorrencias, fetchRecentRondas } from '../store/slices/dashboardSlice';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Avatar,
    Chip,
    useTheme,
    alpha
} from '@mui/material';
import {
    Report as ReportIcon,
    Security as SecurityIcon,
    Business as BusinessIcon,
    Schedule as ScheduleIcon
} from '@mui/icons-material';
import LoadingSpinner from '../components/LoadingSpinner';

const DashboardPage: React.FC = () => {
    const theme = useTheme();
    const dispatch = useAppDispatch();
    const { stats, recentOcorrencias, recentRondas, loading, error } = useAppSelector((state) => state.dashboard);

    useEffect(() => {
        dispatch(fetchDashboardStats());
        dispatch(fetchRecentOcorrencias());
        dispatch(fetchRecentRondas());
    }, [dispatch]);

    if (loading) {
        return <LoadingSpinner message="Carregando dashboard..." size="large" />;
    }

    if (error) {
        return (
            <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="h6" color="error">
                    Erro ao carregar dashboard: {error}
                </Typography>
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
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
                    Dashboard
                </Typography>
                <Typography variant="h6" color="text.secondary">
                    Visão geral do sistema de gestão de segurança
                </Typography>
            </Box>

            {/* Estatísticas */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, mb: 4 }}>
                <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
                    <Card sx={{
                        borderRadius: 3,
                        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.primary.main, 0.05)})`,
                        border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
                    }}>
                        <CardContent sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <Avatar sx={{
                                    bgcolor: theme.palette.primary.main,
                                    mr: 2,
                                    width: 48,
                                    height: 48
                                }}>
                                    <ReportIcon />
                                </Avatar>
                                <Box>
                                    <Typography variant="h4" fontWeight={700} color="primary">
                                        {stats?.stats?.total_ocorrencias || 0}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Total de Ocorrências
                                    </Typography>
                                </Box>
                            </Box>
                            <Chip
                                label={`${stats?.stats?.ocorrencias_ultimo_mes || 0} este mês`}
                                size="small"
                                color="primary"
                                variant="outlined"
                            />
                        </CardContent>
                    </Card>
                </Box>

                <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
                    <Card sx={{
                        borderRadius: 3,
                        background: `linear-gradient(135deg, ${alpha(theme.palette.secondary.main, 0.1)}, ${alpha(theme.palette.secondary.main, 0.05)})`,
                        border: `1px solid ${alpha(theme.palette.secondary.main, 0.2)}`
                    }}>
                        <CardContent sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <Avatar sx={{
                                    bgcolor: theme.palette.secondary.main,
                                    mr: 2,
                                    width: 48,
                                    height: 48
                                }}>
                                    <SecurityIcon />
                                </Avatar>
                                <Box>
                                    <Typography variant="h4" fontWeight={700} color="secondary">
                                        {stats?.stats?.total_rondas || 0}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Total de Rondas
                                    </Typography>
                                </Box>
                            </Box>
                            <Chip
                                label={`${stats?.stats?.rondas_ultimo_mes || 0} este mês`}
                                size="small"
                                color="secondary"
                                variant="outlined"
                            />
                        </CardContent>
                    </Card>
                </Box>

                <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
                    <Card sx={{
                        borderRadius: 3,
                        background: `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.1)}, ${alpha(theme.palette.success.main, 0.05)})`,
                        border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`
                    }}>
                        <CardContent sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <Avatar sx={{
                                    bgcolor: theme.palette.success.main,
                                    mr: 2,
                                    width: 48,
                                    height: 48
                                }}>
                                    <BusinessIcon />
                                </Avatar>
                                <Box>
                                    <Typography variant="h4" fontWeight={700} color="success.main">
                                        {stats?.stats?.total_condominios || 0}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Condomínios
                                    </Typography>
                                </Box>
                            </Box>
                            <Chip
                                label="Ativos"
                                size="small"
                                color="success"
                                variant="outlined"
                            />
                        </CardContent>
                    </Card>
                </Box>

                <Box sx={{ flex: '1 1 300px', minWidth: 0 }}>
                    <Card sx={{
                        borderRadius: 3,
                        background: `linear-gradient(135deg, ${alpha(theme.palette.warning.main, 0.1)}, ${alpha(theme.palette.warning.main, 0.05)})`,
                        border: `1px solid ${alpha(theme.palette.warning.main, 0.2)}`
                    }}>
                        <CardContent sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <Avatar sx={{
                                    bgcolor: theme.palette.warning.main,
                                    mr: 2,
                                    width: 48,
                                    height: 48
                                }}>
                                    <ScheduleIcon />
                                </Avatar>
                                <Box>
                                    <Typography variant="h4" fontWeight={700} color="warning.main">
                                        {stats?.stats?.rondas_em_andamento || 0}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Rondas em Andamento
                                    </Typography>
                                </Box>
                            </Box>
                            <Chip
                                label="Tempo Real"
                                size="small"
                                color="warning"
                                variant="outlined"
                            />
                        </CardContent>
                    </Card>
                </Box>
            </Box>

            {/* Conteúdo Principal */}
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                {/* Ocorrências Recentes */}
                <Box sx={{ flex: '1 1 500px', minWidth: 0 }}>
                    <Card sx={{ borderRadius: 3, height: '100%' }}>
                        <CardContent sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <ReportIcon color="primary" sx={{ mr: 1 }} />
                                <Typography variant="h6" fontWeight={600}>
                                    Ocorrências Recentes
                                </Typography>
                            </Box>

                            <Box sx={{ textAlign: 'center', py: 4 }}>
                                <ReportIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                                <Typography variant="body1" color="text.secondary">
                                    Nenhuma ocorrência recente
                                </Typography>
                            </Box>
                        </CardContent>
                    </Card>
                </Box>

                {/* Rondas Recentes */}
                <Box sx={{ flex: '1 1 500px', minWidth: 0 }}>
                    <Card sx={{ borderRadius: 3, height: '100%' }}>
                        <CardContent sx={{ p: 3 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <SecurityIcon color="secondary" sx={{ mr: 1 }} />
                                <Typography variant="h6" fontWeight={600}>
                                    Rondas Recentes
                                </Typography>
                            </Box>

                            <Box sx={{ textAlign: 'center', py: 4 }}>
                                <SecurityIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 2 }} />
                                <Typography variant="body1" color="text.secondary">
                                    Nenhuma ronda recente
                                </Typography>
                            </Box>
                        </CardContent>
                    </Card>
                </Box>
            </Box>
        </Box>
    );
};

export default DashboardPage; 
