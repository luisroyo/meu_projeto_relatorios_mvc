import React, { useEffect } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import {
    Container,
    Box,
    Typography,
    TextField,
    Button,
    Link,
    Paper,
    Alert,
    CircularProgress,
    useTheme,
    alpha,
} from '@mui/material';
import { LockOutlined as LockIcon, Visibility, VisibilityOff } from '@mui/icons-material';
import { toast } from 'react-toastify';

import { useAppSelector, useAppDispatch } from '../hooks';
import { login, clearError } from '../store/slices/authSlice';

// Schema de validação
const schema = yup.object({
    email: yup
        .string()
        .email('Email inválido')
        .required('Email é obrigatório'),
    password: yup
        .string()
        .min(6, 'Senha deve ter pelo menos 6 caracteres')
        .required('Senha é obrigatória'),
}).required();

type LoginFormData = yup.InferType<typeof schema>;

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const dispatch = useAppDispatch();
    const theme = useTheme();
    const { loading, error, isAuthenticated } = useAppSelector((state) => state.auth);
    const [showPassword, setShowPassword] = React.useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormData>({
        resolver: yupResolver(schema),
    });

    useEffect(() => {
        // Se já está autenticado, redirecionar para dashboard
        if (isAuthenticated) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, navigate]);

    useEffect(() => {
        // Limpar erro quando componente montar
        dispatch(clearError());
    }, [dispatch]);

    const onSubmit = async (data: LoginFormData) => {
        try {
            await dispatch(login(data)).unwrap();
            toast.success('Login realizado com sucesso!');
            navigate('/dashboard');
        } catch (error) {
            toast.error(error as string);
        }
    };

    return (
        <Box
            sx={{
                minHeight: '100vh',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 2,
                position: 'relative',
                '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'url("data:image/svg+xml,%3Csvg width="60" height="60" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="none" fill-rule="evenodd"%3E%3Cg fill="%23ffffff" fill-opacity="0.05"%3E%3Ccircle cx="30" cy="30" r="2"/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
                    opacity: 0.3,
                }
            }}
        >
            <Container maxWidth="sm">
                <Paper
                    elevation={24}
                    sx={{
                        padding: { xs: 3, sm: 4 },
                        borderRadius: 3,
                        background: 'rgba(255, 255, 255, 0.95)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        boxShadow: '0 25px 50px rgba(0, 0, 0, 0.15)',
                        position: 'relative',
                        overflow: 'hidden',
                        '&::before': {
                            content: '""',
                            position: 'absolute',
                            top: 0,
                            left: 0,
                            right: 0,
                            height: '4px',
                            background: 'linear-gradient(90deg, #667eea, #764ba2, #667eea)',
                            backgroundSize: '200% 100%',
                            animation: 'gradientShift 3s ease infinite',
                        },
                        '@keyframes gradientShift': {
                            '0%, 100%': { backgroundPosition: '0% 50%' },
                            '50%': { backgroundPosition: '100% 50%' },
                        }
                    }}
                >
                    <Box
                        sx={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            textAlign: 'center',
                            mb: 4,
                        }}
                    >
                        <Box
                            sx={{
                                width: 80,
                                height: 80,
                                borderRadius: '50%',
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                mb: 2,
                                boxShadow: '0 8px 25px rgba(102, 126, 234, 0.3)',
                            }}
                        >
                            <LockIcon sx={{ fontSize: 40, color: 'white' }} />
                        </Box>

                        <Typography
                            component="h1"
                            variant="h4"
                            sx={{
                                fontWeight: 700,
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                backgroundClip: 'text',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                mb: 1,
                            }}
                        >
                            Sistema de Gestão
                        </Typography>

                        <Typography
                            component="h2"
                            variant="h6"
                            sx={{
                                color: 'text.secondary',
                                fontWeight: 500,
                                mb: 3,
                            }}
                        >
                            Acessar Conta
                        </Typography>
                    </Box>

                    {error && (
                        <Alert
                            severity="error"
                            sx={{
                                width: '100%',
                                mb: 3,
                                borderRadius: 2,
                                '& .MuiAlert-icon': {
                                    fontSize: 24,
                                }
                            }}
                        >
                            {error}
                        </Alert>
                    )}

                    <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ mt: 1 }}>
                        <TextField
                            {...register('email')}
                            margin="normal"
                            required
                            fullWidth
                            id="email"
                            label="Email"
                            name="email"
                            autoComplete="email"
                            autoFocus
                            error={!!errors.email}
                            helperText={errors.email?.message}
                            sx={{
                                '& .MuiOutlinedInput-root': {
                                    borderRadius: 2,
                                    '&:hover fieldset': {
                                        borderColor: 'primary.main',
                                    },
                                    '&.Mui-focused fieldset': {
                                        borderColor: 'primary.main',
                                        borderWidth: 2,
                                    },
                                },
                                '& .MuiInputLabel-root.Mui-focused': {
                                    color: 'primary.main',
                                },
                            }}
                        />

                        <TextField
                            {...register('password')}
                            margin="normal"
                            required
                            fullWidth
                            name="password"
                            label="Senha"
                            type={showPassword ? 'text' : 'password'}
                            id="password"
                            autoComplete="current-password"
                            error={!!errors.password}
                            helperText={errors.password?.message}
                            InputProps={{
                                endAdornment: (
                                    <Button
                                        onClick={() => setShowPassword(!showPassword)}
                                        sx={{
                                            minWidth: 'auto',
                                            p: 1,
                                            color: 'text.secondary',
                                            '&:hover': {
                                                backgroundColor: 'transparent',
                                                color: 'primary.main',
                                            }
                                        }}
                                    >
                                        {showPassword ? <VisibilityOff /> : <Visibility />}
                                    </Button>
                                ),
                            }}
                            sx={{
                                '& .MuiOutlinedInput-root': {
                                    borderRadius: 2,
                                    '&:hover fieldset': {
                                        borderColor: 'primary.main',
                                    },
                                    '&.Mui-focused fieldset': {
                                        borderColor: 'primary.main',
                                        borderWidth: 2,
                                    },
                                },
                                '& .MuiInputLabel-root.Mui-focused': {
                                    color: 'primary.main',
                                },
                            }}
                        />

                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            disabled={loading}
                            sx={{
                                mt: 3,
                                mb: 2,
                                py: 1.5,
                                borderRadius: 2,
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                boxShadow: '0 8px 25px rgba(102, 126, 234, 0.3)',
                                fontWeight: 600,
                                fontSize: '1.1rem',
                                textTransform: 'none',
                                transition: 'all 0.3s ease',
                                '&:hover': {
                                    background: 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                                    boxShadow: '0 12px 35px rgba(102, 126, 234, 0.4)',
                                    transform: 'translateY(-2px)',
                                },
                                '&:disabled': {
                                    background: 'linear-gradient(135deg, #cbd5e0 0%, #a0aec0 100%)',
                                    boxShadow: 'none',
                                    transform: 'none',
                                }
                            }}
                        >
                            {loading ? (
                                <CircularProgress size={24} sx={{ color: 'white' }} />
                            ) : (
                                'Entrar'
                            )}
                        </Button>

                        <Box sx={{ textAlign: 'center', mt: 2 }}>
                            <Link
                                component={RouterLink}
                                to="/register"
                                variant="body2"
                                sx={{
                                    color: 'primary.main',
                                    textDecoration: 'none',
                                    fontWeight: 500,
                                    '&:hover': {
                                        textDecoration: 'underline',
                                        color: 'primary.dark',
                                    }
                                }}
                            >
                                Não tem uma conta? Registre-se
                            </Link>
                        </Box>
                    </Box>
                </Paper>
            </Container>
        </Box>
    );
};

export default LoginPage; 