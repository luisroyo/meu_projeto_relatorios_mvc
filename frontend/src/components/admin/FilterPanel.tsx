import React from 'react';
import {
    Paper,
    Box,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Button,
    Typography,
    Chip,
    Stack
} from '@mui/material';
import { FilterList, Clear } from '@mui/icons-material';
import type { DashboardFilters } from '../../types';

interface FilterPanelProps {
    filters: DashboardFilters;
    onFiltersChange: (filters: Partial<DashboardFilters>) => void;
    onApplyFilters: () => void;
    onClearFilters: () => void;
    showDateRange?: boolean;
    showCondominio?: boolean;
    showSupervisor?: boolean;
    showApiKey?: boolean;
    showService?: boolean;
    showUserId?: boolean;
    showDays?: boolean;
    condominios?: Array<{ id: number; nome: string }>;
    supervisores?: Array<{ id: number; username: string }>;
    apiKeys?: string[];
    services?: string[];
    users?: Array<{ id: number; username: string }>;
}

const FilterPanel: React.FC<FilterPanelProps> = ({
    filters,
    onFiltersChange,
    onApplyFilters,
    onClearFilters,
    showDateRange = false,
    showCondominio = false,
    showSupervisor = false,
    showApiKey = false,
    showService = false,
    showUserId = false,
    showDays = false,
    condominios = [],
    supervisores = [],
    apiKeys = [],
    services = [],
    users = []
}) => {
    const currentYear = new Date().getFullYear();
    const years = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i);
    const months = [
        { value: 1, label: 'Janeiro' },
        { value: 2, label: 'Fevereiro' },
        { value: 3, label: 'Março' },
        { value: 4, label: 'Abril' },
        { value: 5, label: 'Maio' },
        { value: 6, label: 'Junho' },
        { value: 7, label: 'Julho' },
        { value: 8, label: 'Agosto' },
        { value: 9, label: 'Setembro' },
        { value: 10, label: 'Outubro' },
        { value: 11, label: 'Novembro' },
        { value: 12, label: 'Dezembro' }
    ];

    const hasActiveFilters = () => {
        return Object.values(filters).some(value =>
            value !== undefined && value !== null && value !== ''
        );
    };

    return (
        <Paper sx={{ p: 2, mb: 2 }}>
            <Box display="flex" alignItems="center" gap={1} mb={2}>
                <FilterList color="primary" />
                <Typography variant="h6">Filtros</Typography>
                {hasActiveFilters() && (
                    <Chip
                        label="Filtros ativos"
                        color="primary"
                        size="small"
                        variant="outlined"
                    />
                )}
            </Box>

            <Box display="flex" flexWrap="wrap" gap={2} mb={2}>
                {/* Ano */}
                <FormControl size="small" sx={{ minWidth: 120 }}>
                    <InputLabel>Ano</InputLabel>
                    <Select
                        value={filters.ano || ''}
                        label="Ano"
                        onChange={(e) => onFiltersChange({ ano: e.target.value as number })}
                    >
                        {years.map(year => (
                            <MenuItem key={year} value={year}>{year}</MenuItem>
                        ))}
                    </Select>
                </FormControl>

                {/* Mês */}
                <FormControl size="small" sx={{ minWidth: 120 }}>
                    <InputLabel>Mês</InputLabel>
                    <Select
                        value={filters.mes || ''}
                        label="Mês"
                        onChange={(e) => onFiltersChange({ mes: e.target.value as number })}
                    >
                        {months.map(month => (
                            <MenuItem key={month.value} value={month.value}>
                                {month.label}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>

                {/* Dias (para Gemini Dashboard) */}
                {showDays && (
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>Período (dias)</InputLabel>
                        <Select
                            value={filters.days || 7}
                            label="Período (dias)"
                            onChange={(e) => onFiltersChange({ days: e.target.value as number })}
                        >
                            <MenuItem value={1}>Último dia</MenuItem>
                            <MenuItem value={7}>Últimos 7 dias</MenuItem>
                            <MenuItem value={30}>Últimos 30 dias</MenuItem>
                            <MenuItem value={90}>Últimos 90 dias</MenuItem>
                        </Select>
                    </FormControl>
                )}

                {/* Condomínio */}
                {showCondominio && (
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>Condomínio</InputLabel>
                        <Select
                            value={filters.condominio_id || ''}
                            label="Condomínio"
                            onChange={(e) => onFiltersChange({ condominio_id: e.target.value as number })}
                        >
                            <MenuItem value="">Todos</MenuItem>
                            {condominios.map(condominio => (
                                <MenuItem key={condominio.id} value={condominio.id}>
                                    {condominio.nome}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                )}

                {/* Supervisor */}
                {showSupervisor && (
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>Supervisor</InputLabel>
                        <Select
                            value={filters.supervisor_id || ''}
                            label="Supervisor"
                            onChange={(e) => onFiltersChange({ supervisor_id: e.target.value as number })}
                        >
                            <MenuItem value="">Todos</MenuItem>
                            {supervisores.map(supervisor => (
                                <MenuItem key={supervisor.id} value={supervisor.id}>
                                    {supervisor.username}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                )}

                {/* API Key */}
                {showApiKey && (
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>API Key</InputLabel>
                        <Select
                            value={filters.api_key || 'all'}
                            label="API Key"
                            onChange={(e) => onFiltersChange({ api_key: e.target.value })}
                        >
                            <MenuItem value="all">Todas</MenuItem>
                            {apiKeys.map(apiKey => (
                                <MenuItem key={apiKey} value={apiKey}>
                                    {apiKey}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                )}

                {/* Service */}
                {showService && (
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>Serviço</InputLabel>
                        <Select
                            value={filters.service || 'all'}
                            label="Serviço"
                            onChange={(e) => onFiltersChange({ service: e.target.value })}
                        >
                            <MenuItem value="all">Todos</MenuItem>
                            {services.map(service => (
                                <MenuItem key={service} value={service}>
                                    {service}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                )}

                {/* User ID */}
                {showUserId && (
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                        <InputLabel>Usuário</InputLabel>
                        <Select
                            value={filters.user_id || 0}
                            label="Usuário"
                            onChange={(e) => onFiltersChange({ user_id: e.target.value as number })}
                        >
                            <MenuItem value={0}>Todos</MenuItem>
                            {users.map(user => (
                                <MenuItem key={user.id} value={user.id}>
                                    {user.username}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                )}
            </Box>

            {/* Action Buttons */}
            <Stack direction="row" spacing={2}>
                <Button
                    variant="contained"
                    onClick={onApplyFilters}
                    startIcon={<FilterList />}
                >
                    Aplicar Filtros
                </Button>
                <Button
                    variant="outlined"
                    onClick={onClearFilters}
                    startIcon={<Clear />}
                >
                    Limpar Filtros
                </Button>
            </Stack>
        </Paper>
    );
};

export default FilterPanel; 