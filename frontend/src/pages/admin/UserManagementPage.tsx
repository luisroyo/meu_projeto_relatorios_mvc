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
    Stack
} from '@mui/material';
import {
    CheckCircle,
    Cancel,
    AdminPanelSettings,
    SupervisorAccount,
    Delete,
    Search,
    FilterList,
    Clear,
    Visibility
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../hooks';
import {
    fetchUsers,
    approveUser,
    revokeUser,
    toggleAdmin,
    toggleSupervisor,
    deleteUser,
    setFilters,
    clearFilters
} from '../../store/slices/userManagementSlice';
import LoadingSpinner from '../../components/LoadingSpinner';

const UserManagementPage: React.FC = () => {
    const dispatch = useAppDispatch();
    const { users, pagination, loading, error, filters } = useAppSelector((state) => state.userManagement);
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [userToDelete, setUserToDelete] = useState<number | null>(null);

    useEffect(() => {
        dispatch(fetchUsers({
            page: page + 1,
            per_page: rowsPerPage,
            search: filters.search,
            status: filters.status,
            role: filters.role
        }));
    }, [dispatch, page, rowsPerPage, filters]);

    const handleChangePage = (event: unknown, newPage: number) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };

    const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        dispatch(setFilters({ search: event.target.value }));
    };

    const handleStatusFilterChange = (event: any) => {
        dispatch(setFilters({ status: event.target.value }));
    };

    const handleRoleFilterChange = (event: any) => {
        dispatch(setFilters({ role: event.target.value }));
    };

    const handleClearFilters = () => {
        dispatch(clearFilters());
    };

    const handleApproveUser = (userId: number) => {
        dispatch(approveUser(userId));
    };

    const handleRevokeUser = (userId: number) => {
        dispatch(revokeUser(userId));
    };

    const handleToggleAdmin = (userId: number) => {
        dispatch(toggleAdmin(userId));
    };

    const handleToggleSupervisor = (userId: number) => {
        dispatch(toggleSupervisor(userId));
    };

    const handleDeleteUser = (userId: number) => {
        setUserToDelete(userId);
        setDeleteDialogOpen(true);
    };

    const confirmDeleteUser = () => {
        if (userToDelete) {
            dispatch(deleteUser(userToDelete));
            setDeleteDialogOpen(false);
            setUserToDelete(null);
        }
    };

    const getStatusChip = (isApproved: boolean) => (
        <Chip
            label={isApproved ? 'Aprovado' : 'Pendente'}
            color={isApproved ? 'success' : 'warning'}
            size="small"
        />
    );

    const getRoleChips = (user: any) => (
        <Stack direction="row" spacing={0.5}>
            {user.is_admin && (
                <Chip
                    icon={<AdminPanelSettings />}
                    label="Admin"
                    color="error"
                    size="small"
                />
            )}
            {user.is_supervisor && (
                <Chip
                    icon={<SupervisorAccount />}
                    label="Supervisor"
                    color="primary"
                    size="small"
                />
            )}
        </Stack>
    );

    if (loading) {
        return <LoadingSpinner />;
    }

    return (
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            <Box mb={4}>
                <Typography variant="h4" component="h1" gutterBottom>
                    Gerenciamento de Usuários
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    Gerencie usuários do sistema, aprovações e permissões
                </Typography>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}

            {/* Filtros */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={4}>
                        <TextField
                            fullWidth
                            size="small"
                            label="Buscar usuário"
                            value={filters.search}
                            onChange={handleSearchChange}
                            InputProps={{
                                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
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
                                <MenuItem value="all">Todos</MenuItem>
                                <MenuItem value="approved">Aprovados</MenuItem>
                                <MenuItem value="pending">Pendentes</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={3}>
                        <FormControl fullWidth size="small">
                            <InputLabel>Função</InputLabel>
                            <Select
                                value={filters.role}
                                label="Função"
                                onChange={handleRoleFilterChange}
                            >
                                <MenuItem value="all">Todas</MenuItem>
                                <MenuItem value="admin">Administradores</MenuItem>
                                <MenuItem value="supervisor">Supervisores</MenuItem>
                                <MenuItem value="user">Usuários</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={2}>
                        <Button
                            variant="outlined"
                            onClick={handleClearFilters}
                            startIcon={<Clear />}
                            fullWidth
                        >
                            Limpar
                        </Button>
                    </Grid>
                </Grid>
            </Paper>

            {/* Tabela de Usuários */}
            <Paper>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Usuário</TableCell>
                                <TableCell>Email</TableCell>
                                <TableCell>Status</TableCell>
                                <TableCell>Funções</TableCell>
                                <TableCell>Data de Registro</TableCell>
                                <TableCell>Último Login</TableCell>
                                <TableCell align="center">Ações</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {users.map((user) => (
                                <TableRow key={user.id}>
                                    <TableCell>
                                        <Typography variant="body2" fontWeight="medium">
                                            {user.username}
                                        </Typography>
                                    </TableCell>
                                    <TableCell>{user.email}</TableCell>
                                    <TableCell>{getStatusChip(user.is_approved)}</TableCell>
                                    <TableCell>{getRoleChips(user)}</TableCell>
                                    <TableCell>
                                        {user.date_registered
                                            ? new Date(user.date_registered).toLocaleDateString('pt-BR')
                                            : 'N/A'
                                        }
                                    </TableCell>
                                    <TableCell>
                                        {user.last_login
                                            ? new Date(user.last_login).toLocaleDateString('pt-BR')
                                            : 'N/A'
                                        }
                                    </TableCell>
                                    <TableCell align="center">
                                        <Stack direction="row" spacing={1} justifyContent="center">
                                            {!user.is_approved ? (
                                                <Tooltip title="Aprovar usuário">
                                                    <IconButton
                                                        color="success"
                                                        onClick={() => handleApproveUser(user.id)}
                                                        size="small"
                                                    >
                                                        <CheckCircle />
                                                    </IconButton>
                                                </Tooltip>
                                            ) : (
                                                <Tooltip title="Revogar aprovação">
                                                    <IconButton
                                                        color="warning"
                                                        onClick={() => handleRevokeUser(user.id)}
                                                        size="small"
                                                    >
                                                        <Cancel />
                                                    </IconButton>
                                                </Tooltip>
                                            )}

                                            <Tooltip title={user.is_admin ? "Remover admin" : "Tornar admin"}>
                                                <IconButton
                                                    color={user.is_admin ? "error" : "primary"}
                                                    onClick={() => handleToggleAdmin(user.id)}
                                                    size="small"
                                                >
                                                    <AdminPanelSettings />
                                                </IconButton>
                                            </Tooltip>

                                            <Tooltip title={user.is_supervisor ? "Remover supervisor" : "Tornar supervisor"}>
                                                <IconButton
                                                    color={user.is_supervisor ? "error" : "primary"}
                                                    onClick={() => handleToggleSupervisor(user.id)}
                                                    size="small"
                                                >
                                                    <SupervisorAccount />
                                                </IconButton>
                                            </Tooltip>

                                            <Tooltip title="Deletar usuário">
                                                <IconButton
                                                    color="error"
                                                    onClick={() => handleDeleteUser(user.id)}
                                                    size="small"
                                                >
                                                    <Delete />
                                                </IconButton>
                                            </Tooltip>
                                        </Stack>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>

                <TablePagination
                    rowsPerPageOptions={[5, 10, 25]}
                    component="div"
                    count={pagination.total}
                    rowsPerPage={rowsPerPage}
                    page={page}
                    onPageChange={handleChangePage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                    labelRowsPerPage="Linhas por página:"
                    labelDisplayedRows={({ from, to, count }) =>
                        `${from}-${to} de ${count !== -1 ? count : `mais de ${to}`}`
                    }
                />
            </Paper>

            {/* Dialog de Confirmação de Exclusão */}
            <Dialog
                open={deleteDialogOpen}
                onClose={() => setDeleteDialogOpen(false)}
            >
                <DialogTitle>Confirmar Exclusão</DialogTitle>
                <DialogContent>
                    <DialogContentText>
                        Tem certeza que deseja excluir este usuário? Esta ação não pode ser desfeita.
                    </DialogContentText>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>
                        Cancelar
                    </Button>
                    <Button onClick={confirmDeleteUser} color="error" variant="contained">
                        Excluir
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
};

export default UserManagementPage; 