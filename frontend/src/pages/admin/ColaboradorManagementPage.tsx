import React, { useEffect, useState } from 'react';
import {
    Container,
    Grid,
    Typography,
    Box,
    Alert,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TablePagination,
    IconButton,
    Chip,
    Button,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    DialogContentText,
    Tooltip,
    Stack,
    useTheme,
    alpha
} from '@mui/material';
import {
    Add as AddIcon,
    Edit as EditIcon,
    Delete as DeleteIcon,
    Search as SearchIcon,
    FilterList as FilterIcon,
    Clear as ClearIcon,
    Person as PersonIcon,
    Badge as BadgeIcon
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../hooks';
import {
    fetchColaboradores,
    createColaborador,
    updateColaborador,
    deleteColaborador,
    setFilters,
    clearFilters
} from '../../store/slices/colaboradorSlice';
import LoadingSpinner from '../../components/LoadingSpinner';

const ColaboradorManagementPage: React.FC = () => {
    const theme = useTheme();
    const dispatch = useAppDispatch();
    const { colaboradores, pagination, loading, error, filters } = useAppSelector((state) => state.colaborador);

    const [formOpen, setFormOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [selectedColaborador, setSelectedColaborador] = useState<any>(null);

    // Form State
    const [formData, setFormData] = useState({
        nome_completo: '',
        cargo: '',
        matricula: '',
        data_admissao: '',
        status: 'Ativo'
    });

    useEffect(() => {
        dispatch(fetchColaboradores({
            page: pagination.page,
            per_page: pagination.per_page,
            search: filters.search,
            status: filters.status
        }));
    }, [dispatch, pagination.page, pagination.per_page, filters]);

    const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        dispatch(setFilters({ search: event.target.value }));
    };

    const handleStatusFilterChange = (event: any) => {
        dispatch(setFilters({ status: event.target.value }));
    };

    const handlePageChange = (event: unknown, newPage: number) => {
        // A paginação do backend é 1-indexed, mas o MUI é 0-indexed
        dispatch(fetchColaboradores({ ...filters, page: newPage + 1 }));
    };

    const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        dispatch(fetchColaboradores({ ...filters, page: 1, per_page: parseInt(event.target.value, 10) }));
    };

    // Form Handlers
    const handleOpenForm = (colaborador?: any) => {
        if (colaborador) {
            setSelectedColaborador(colaborador);
            setFormData({
                nome_completo: colaborador.nome_completo,
                cargo: colaborador.cargo,
                matricula: colaborador.matricula || '',
                data_admissao: colaborador.data_admissao ? colaborador.data_admissao.split('T')[0] : '',
                status: colaborador.status
            });
        } else {
            setSelectedColaborador(null);
            setFormData({
                nome_completo: '',
                cargo: '',
                matricula: '',
                data_admissao: '',
                status: 'Ativo'
            });
        }
        setFormOpen(true);
    };

    const handleCloseForm = () => {
        setFormOpen(false);
        setSelectedColaborador(null);
    };

    const handleFormSubmit = async () => {
        if (selectedColaborador) {
            await dispatch(updateColaborador({ id: selectedColaborador.id, data: formData }));
        } else {
            await dispatch(createColaborador(formData));
        }
        handleCloseForm();
        dispatch(fetchColaboradores(filters)); // Refresh list
    };

    // Delete Handlers
    const handleDeleteClick = (colaborador: any) => {
        setSelectedColaborador(colaborador);
        setDeleteDialogOpen(true);
    };

    const confirmDelete = async () => {
        if (selectedColaborador) {
            await dispatch(deleteColaborador(selectedColaborador.id));
            setDeleteDialogOpen(false);
            setSelectedColaborador(null);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
                <Box>
                    <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 600, color: theme.palette.primary.main }}>
                        Gestão de Colaboradores
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Gerencie o cadastro de porteiros, vigilantes e zeladores.
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={() => handleOpenForm()}
                    sx={{ borderRadius: 2 }}
                >
                    Novo Colaborador
                </Button>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {/* Filtros */}
            <Paper sx={{ p: 2, mb: 3, borderRadius: 2 }}>
                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={5}>
                        <TextField
                            fullWidth
                            size="small"
                            label="Buscar por Nome"
                            value={filters.search}
                            onChange={handleSearchChange}
                            InputProps={{
                                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                            }}
                        />
                    </Grid>
                    <Grid item xs={12} sm={3}>
                        <FormControl fullWidth size="small">
                            <InputLabel>Status</InputLabel>
                            <Select
                                value={filters.status}
                                label="Status"
                                onChange={handleStatusFilterChange}
                            >
                                <MenuItem value="Todos">Todos</MenuItem>
                                <MenuItem value="Ativo">Ativo</MenuItem>
                                <MenuItem value="Inativo">Inativo</MenuItem>
                                <MenuItem value="Férias">Férias</MenuItem>
                                <MenuItem value="Afastado">Afastado</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={2}>
                        <Button
                            variant="outlined"
                            onClick={() => dispatch(clearFilters())}
                            startIcon={<ClearIcon />}
                            fullWidth
                        >
                            Limpar
                        </Button>
                    </Grid>
                </Grid>
            </Paper>

            {/* Tabela */}
            <Paper sx={{ borderRadius: 2, overflow: 'hidden' }}>
                <TableContainer>
                    <Table>
                        <TableHead sx={{ bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                            <TableRow>
                                <TableCell sx={{ fontWeight: 600 }}>Nome Completo</TableCell>
                                <TableCell sx={{ fontWeight: 600 }}>Cargo</TableCell>
                                <TableCell sx={{ fontWeight: 600 }}>Matrícula</TableCell>
                                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
                                <TableCell align="right" sx={{ fontWeight: 600 }}>Ações</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {loading ? (
                                <TableRow>
                                    <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                                        <LoadingSpinner />
                                    </TableCell>
                                </TableRow>
                            ) : colaboradores.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                                        <Typography color="text.secondary">Nenhum colaborador encontrado.</Typography>
                                    </TableCell>
                                </TableRow>
                            ) : (
                                colaboradores.map((colaborador) => (
                                    <TableRow key={colaborador.id} hover>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <PersonIcon color="action" fontSize="small" />
                                                <Typography variant="body2" fontWeight="medium">
                                                    {colaborador.nome_completo}
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>{colaborador.cargo}</TableCell>
                                        <TableCell>
                                            {colaborador.matricula && (
                                                <Chip
                                                    icon={<BadgeIcon sx={{ fontSize: 14 }} />}
                                                    label={colaborador.matricula}
                                                    size="small"
                                                    variant="outlined"
                                                />
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={colaborador.status}
                                                color={colaborador.status === 'Ativo' ? 'success' : 'default'}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell align="right">
                                            <Stack direction="row" spacing={1} justifyContent="flex-end">
                                                <Tooltip title="Editar">
                                                    <IconButton size="small" color="primary" onClick={() => handleOpenForm(colaborador)}>
                                                        <EditIcon />
                                                    </IconButton>
                                                </Tooltip>
                                                <Tooltip title="Inativar/Excluir">
                                                    <IconButton size="small" color="error" onClick={() => handleDeleteClick(colaborador)}>
                                                        <DeleteIcon />
                                                    </IconButton>
                                                </Tooltip>
                                            </Stack>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
                <TablePagination
                    rowsPerPageOptions={[5, 10, 25]}
                    component="div"
                    count={pagination.total}
                    rowsPerPage={pagination.per_page}
                    page={pagination.page - 1} // Front usa 0-indexed
                    onPageChange={handlePageChange}
                    onRowsPerPageChange={handleRowsPerPageChange}
                    labelRowsPerPage="Linhas por página:"
                />
            </Paper>

            {/* Dialog Form */}
            <Dialog open={formOpen} onClose={handleCloseForm} maxWidth="sm" fullWidth>
                <DialogTitle>
                    {selectedColaborador ? 'Editar Colaborador' : 'Novo Colaborador'}
                </DialogTitle>
                <DialogContent>
                    <Grid container spacing={2} sx={{ mt: 0.5 }}>
                        <Grid item xs={12}>
                            <TextField
                                autoFocus
                                label="Nome Completo"
                                fullWidth
                                value={formData.nome_completo}
                                onChange={(e) => setFormData({ ...formData, nome_completo: e.target.value })}
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextField
                                label="Cargo"
                                fullWidth
                                value={formData.cargo}
                                onChange={(e) => setFormData({ ...formData, cargo: e.target.value })}
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextField
                                label="Matrícula"
                                fullWidth
                                value={formData.matricula}
                                onChange={(e) => setFormData({ ...formData, matricula: e.target.value })}
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <TextField
                                label="Data de Admissão"
                                type="date"
                                fullWidth
                                InputLabelProps={{ shrink: true }}
                                value={formData.data_admissao}
                                onChange={(e) => setFormData({ ...formData, data_admissao: e.target.value })}
                            />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                            <FormControl fullWidth>
                                <InputLabel>Status</InputLabel>
                                <Select
                                    value={formData.status}
                                    label="Status"
                                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                >
                                    <MenuItem value="Ativo">Ativo</MenuItem>
                                    <MenuItem value="Inativo">Inativo</MenuItem>
                                    <MenuItem value="Férias">Férias</MenuItem>
                                    <MenuItem value="Afastado">Afastado</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                    </Grid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseForm}>Cancelar</Button>
                    <Button onClick={handleFormSubmit} variant="contained">Salvar</Button>
                </DialogActions>
            </Dialog>

            {/* Dialog Delete */}
            <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
                <DialogTitle>Confirmar Exclusão</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Tem certeza que deseja inativar o colaborador "{selectedColaborador?.nome_completo}"?
                        Ele não aparecerá mais nas listas de seleção, mas o histórico será preservado.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>Cancelar</Button>
                    <Button onClick={confirmDelete} color="error" variant="contained">Inativar</Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default ColaboradorManagementPage;
