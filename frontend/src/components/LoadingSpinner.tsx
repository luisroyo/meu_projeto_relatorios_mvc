import React from 'react';
import { Box, CircularProgress, Typography, Fade } from '@mui/material';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  message = 'Carregando...', 
  size = 'medium' 
}) => {
  const getSize = () => {
    switch (size) {
      case 'small': return 40;
      case 'large': return 80;
      default: return 60;
    }
  };

  return (
    <Fade in={true} timeout={500}>
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
        gap={2}
      >
        <CircularProgress 
          size={getSize()} 
          thickness={4}
          sx={{
            color: 'primary.main',
            '& .MuiCircularProgress-circle': {
              strokeLinecap: 'round',
            },
          }}
        />
        <Typography 
          variant="body1" 
          color="text.secondary"
          sx={{ 
            fontWeight: 500,
            textAlign: 'center',
            maxWidth: 300,
          }}
        >
          {message}
        </Typography>
      </Box>
    </Fade>
  );
};

export default LoadingSpinner; 