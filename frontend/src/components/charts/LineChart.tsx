import React from 'react';
import { LineChart as MuiLineChart } from '@mui/x-charts/LineChart';
import { Box, Typography, Paper } from '@mui/material';

interface LineChartProps {
    data: Array<{
        x: string | number;
        y: number;
    }>;
    title: string;
    xAxisLabel?: string;
    yAxisLabel?: string;
    height?: number;
    color?: string;
}

const LineChart: React.FC<LineChartProps> = ({
    data,
    title,
    xAxisLabel = 'Período',
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
            data: data.map(item => item.y),
            label: title,
            color: color,
        }
    ];

    const xAxis = data.map(item => item.x);

    return (
        <Paper sx={{ p: 2, height }}>
            <Typography variant="h6" gutterBottom>
                {title}
            </Typography>
            <Box sx={{ width: '100%', height: height - 80 }}>
                <MuiLineChart
                    width={800}
                    height={height - 80}
                    series={chartData}
                    xAxis={[{ data: xAxis, scaleType: 'point' }]}
                    sx={{
                        '.MuiLineElement-root': {
                            stroke: color,
                            strokeWidth: 2,
                        },
                        '.MuiMarkElement-root': {
                            stroke: color,
                            fill: color,
                        },
                    }}
                />
            </Box>
        </Paper>
    );
};

export default LineChart; 