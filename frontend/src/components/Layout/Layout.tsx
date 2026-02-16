import React from 'react';
import { Outlet } from 'react-router-dom';
import { Box, AppBar, Toolbar, Typography, IconButton, Drawer, List, ListItem, ListItemIcon, ListItemText, useTheme, useMediaQuery, Divider } from '@mui/material';
import {
    Menu as MenuIcon,
    Dashboard,
    Psychology as AnalisadorIcon,
    Report as OcorrenciasIcon,
    Security as RondasIcon,
    Logout,
    AdminPanelSettings,
    People,
    Assessment,
    Timeline,
    Report as ReportIcon,
    Badge,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../hooks';
import { logout } from '../../store/slices/authSlice';

const drawerWidth = 240;

const Layout: React.FC = () => {
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const [mobileOpen, setMobileOpen] = React.useState(false);
    const navigate = useNavigate();
    const dispatch = useAppDispatch();
    const user = useAppSelector((state) => state.auth.user);

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const handleLogout = () => {
        dispatch(logout());
        navigate('/login');
    };

    const menuItems = [
        { text: 'Dashboard', icon: <Dashboard />, path: '/dashboard' },
        { text: 'Analisador IA', icon: <AnalisadorIcon />, path: '/analisador' },
        { text: 'Ocorrências', icon: <OcorrenciasIcon />, path: '/ocorrencias' },
        { text: 'Rondas', icon: <RondasIcon />, path: '/rondas' },
    ];

    const adminMenuItems = [
        { text: 'Métricas Gerais', icon: <Assessment />, path: '/admin/metrics' },
        { text: 'Dashboard Rondas', icon: <Timeline />, path: '/admin/rondas-dashboard' },
        { text: 'Dashboard Ocorrências', icon: <ReportIcon />, path: '/admin/ocorrencias-dashboard' },
        { text: 'Gerenciar Usuários', icon: <People />, path: '/admin/users' },
        { text: 'Gerenciar Colaboradores', icon: <Badge />, path: '/admin/colaboradores' },
    ];

    const drawer = (
        <Box>
            <Toolbar>
                <Typography variant="h6" noWrap component="div">
                    Gestão Segurança
                </Typography>
            </Toolbar>
            <List>
                {menuItems.map((item) => (
                    <ListItem
                        key={item.text}
                        onClick={() => {
                            navigate(item.path);
                            if (isMobile) setMobileOpen(false);
                        }}
                    >
                        <ListItemIcon>{item.icon}</ListItemIcon>
                        <ListItemText primary={item.text} />
                    </ListItem>
                ))}

                {/* Seção Administrativa */}
                {user?.is_admin && (
                    <>
                        <Divider sx={{ my: 2 }} />
                        <ListItem>
                            <ListItemIcon><AdminPanelSettings /></ListItemIcon>
                            <ListItemText
                                primary="Administração"
                                primaryTypographyProps={{
                                    variant: 'subtitle2',
                                    color: 'primary',
                                    fontWeight: 'bold'
                                }}
                            />
                        </ListItem>
                        {adminMenuItems.map((item) => (
                            <ListItem
                                key={item.text}
                                onClick={() => {
                                    navigate(item.path);
                                    if (isMobile) setMobileOpen(false);
                                }}
                                sx={{ pl: 4 }}
                            >
                                <ListItemIcon>{item.icon}</ListItemIcon>
                                <ListItemText primary={item.text} />
                            </ListItem>
                        ))}
                    </>
                )}

                <Divider sx={{ my: 2 }} />
                <ListItem onClick={handleLogout}>
                    <ListItemIcon><Logout /></ListItemIcon>
                    <ListItemText primary="Sair" />
                </ListItem>
            </List>
        </Box>
    );

    return (
        <Box sx={{ display: 'flex' }}>
            <AppBar
                position="fixed"
                sx={{
                    width: { md: `calc(100% - ${drawerWidth}px)` },
                    ml: { md: `${drawerWidth}px` },
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        edge="start"
                        onClick={handleDrawerToggle}
                        sx={{ mr: 2, display: { md: 'none' } }}
                    >
                        <MenuIcon />
                    </IconButton>
                    <Typography variant="h6" noWrap component="div">
                        {user?.username ? `Bem-vindo, ${user.username}` : 'Sistema de Gestão'}
                    </Typography>
                </Toolbar>
            </AppBar>

            <Box
                component="nav"
                sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
            >
                <Drawer
                    variant="temporary"
                    open={mobileOpen}
                    onClose={handleDrawerToggle}
                    ModalProps={{
                        keepMounted: true, // Better open performance on mobile.
                    }}
                    sx={{
                        display: { xs: 'block', md: 'none' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
                    }}
                >
                    {drawer}
                </Drawer>
                <Drawer
                    variant="permanent"
                    sx={{
                        display: { xs: 'none', md: 'block' },
                        '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
                    }}
                    open
                >
                    {drawer}
                </Drawer>
            </Box>

            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    p: 3,
                    width: { md: `calc(100% - ${drawerWidth}px)` },
                    mt: '64px', // Height of AppBar
                }}
            >
                <Outlet />
            </Box>
        </Box>
    );
};

export default Layout; 
