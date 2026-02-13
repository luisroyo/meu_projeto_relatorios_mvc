import React from 'react';
import { PieChart as MuiPieChart } from '@mui/x-charts/PieChart';
import { Box, Typography, Paper } from '@mui/material';

interface PieChartProps {
    data: Array<{
        label: string;
        value: number;
        color?: string;
    }>;
    title: string;
    height?: number;
}

const PieChart: React.FC<PieChartProps> = ({
    data,
    title,
    height = 300
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

    const chartData = data.map((item, index) => ({
        id: index,
        value: item.value,
        label: item.label,
        color: item.color || `hsl(${(index * 137.5) % 360}, 70%, 50%)`,
    }));

    return (
        <Paper sx={{ p: 2, height }}>
            <Typography variant="h6" gutterBottom>
                {title}
            </Typography>
            <Box sx={{ width: '100%', height: height - 80, display: 'flex', justifyContent: 'center' }}>
                <MuiPieChart
                    width={400}
                    height={height - 80}
                    series={[
                        {
                            data: chartData,
                            highlightScope: { fade: 'global', highlighted: 'item' },
                            faded: { innerRadius: 30, additionalRadius: -30, color: 'gray' },
                        },
                    ]}
                />
            </Box>
        </Paper>
    );
};

export default PieChart; 