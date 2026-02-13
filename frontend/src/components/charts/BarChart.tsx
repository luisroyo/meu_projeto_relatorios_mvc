import React from 'react';
import { BarChart as MuiBarChart } from '@mui/x-charts/BarChart';
import { Box, Typography, Paper } from '@mui/material';

interface BarChartProps {
    data: Array<{
        label: string;
        value: number;
    }>;
    title: string;
    xAxisLabel?: string;
    yAxisLabel?: string;
    height?: number;
    color?: string;
}

const BarChart: React.FC<BarChartProps> = ({
    data,
    title,
    xAxisLabel = 'Categoria',
    yAxisLabel = 'Quantidade',
    height = 300,
    color = '#1976d2'
}) => {
    if (!data || data.length === 0) {
        return (
            <Paper sx={{ p: 2, height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                    Nenhum dado disponível
                </Typography>
            </Paper>
        );
    }

    const chartData = [
        {
            data: data.map(item => item.value),
            label: title,
            color: color,
        }
    ];

    const xAxis = data.map(item => item.label);

    return (
        <Paper sx={{ p: 2, height }}>
            <Typography variant="h6" gutterBottom>
                {title}
            </Typography>
            <Box sx={{ width: '100%', height: height - 80 }}>
                <MuiBarChart
                    width={800}
                    height={height - 80}
                    series={chartData}
                    xAxis={[{ data: xAxis, scaleType: 'band' }]}
                    sx={{
                        '.MuiBarElement-root': {
                            fill: color,
                        },
                    }}
                />
            </Box>
        </Paper>
    );
};

export default BarChart; 