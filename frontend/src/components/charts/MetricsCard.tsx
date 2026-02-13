import React from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { TrendingUp, TrendingDown, Remove } from '@mui/icons-material';

interface MetricsCardProps {
    title: string;
    value: number | string;
    subtitle?: string;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
    icon?: React.ReactNode;
}

const MetricsCard: React.FC<MetricsCardProps> = ({
    title,
    value,
    subtitle,
    trend,
    color = 'primary',
    icon
}) => {
    const getTrendIcon = () => {
        if (!trend) return <Remove />;
        return trend.isPositive ? <TrendingUp /> : <TrendingDown />;
    };

    const getTrendColor = () => {
        if (!trend) return 'default';
        return trend.isPositive ? 'success' : 'error';
    };

    return (
        <Card sx={{ height: '100%', minHeight: 120 }}>
            <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        {title}
                    </Typography>
                    {icon && (
                        <Box color={`${color}.main`}>
                            {icon}
                        </Box>
                    )}
                </Box>

                <Typography variant="h4" component="div" color={`${color}.main`} gutterBottom>
                    {typeof value === 'number' ? value.toLocaleString('pt-BR') : value}
                </Typography>

                {subtitle && (
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                        {subtitle}
                    </Typography>
                )}

                {trend && (
                    <Box display="flex" alignItems="center" gap={0.5}>
                        {getTrendIcon()}
                        <Chip
                            label={`${trend.isPositive ? '+' : ''}${trend.value}%`}
                            size="small"
                            color={getTrendColor() as any}
                            variant="outlined"
                        />
                    </Box>
                )}
            </CardContent>
        </Card>
    );
};

export default MetricsCard; 