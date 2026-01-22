import React from 'react';
import { Box, keyframes } from '@mui/material';

const waveAnimation = keyframes`
  0% {
    transform: scaleY(1);
  }
  50% {
    transform: scaleY(0.5);
  }
  100% {
    transform: scaleY(1);
  }
`;

interface SoundWaveProps {
  isAnimating?: boolean;
}

const SoundWave: React.FC<SoundWaveProps> = ({ isAnimating = true }) => {
  const bars = 12; // Number of wave bars

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 1,
        height: '200px',
        width: '100%',
        maxWidth: '600px',
        position: 'relative',
        '&::before': {
          content: '""',
          position: 'absolute',
          width: '100%',
          height: '100%',
          background: 'radial-gradient(circle, rgba(229,88,195,0.2) 0%, rgba(63,184,237,0.2) 100%)',
          filter: 'blur(60px)',
          zIndex: 0,
        }
      }}
    >
      {[...Array(bars)].map((_, index) => (
        <Box
          key={index}
          sx={{
            width: '8px',
            height: '100%',
            backgroundColor: index < bars / 2 ? 'secondary.main' : 'primary.main',
            borderRadius: '4px',
            animation: isAnimating ? `${waveAnimation} ${1 + index * 0.1}s ease-in-out infinite` : 'none',
            transformOrigin: 'center',
            opacity: 0.8,
            zIndex: 1,
          }}
        />
      ))}
    </Box>
  );
};

export default SoundWave; 