import React, { useState } from 'react';
import {
  Container,
  Typography,
  Button,
  Box,
  AppBar,
  Toolbar,
  IconButton,
  Menu,
  MenuItem,
  CircularProgress,
} from '@mui/material';
import { Google, MoreVert, Mic } from '@mui/icons-material';
import SoundWave from '../common/SoundWave';
import { useNavigate } from 'react-router-dom';
import voiceRecognitionService from '../../services/voiceRecognition';

const LandingPage: React.FC = () => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleVoiceResult = (text: string) => {
    console.log('Voice command recognized:', text);
    // Process voice commands here
    if (text.toLowerCase().includes('sign in')) {
      handleGoogleSignIn();
    }
  };

  const handleVoiceError = (error: string) => {
    console.error('Voice recognition error:', error);
    setIsListening(false);
  };

  const handleCommandProcessed = (response: any) => {
    console.log('Command processed:', response);
  };

  const handleMicToggle = () => {
    if (!isListening) {
      voiceRecognitionService.start(
        handleVoiceResult,
        handleVoiceError,
        handleCommandProcessed
      );
    } else {
      voiceRecognitionService.stop();
    }
    setIsListening(!isListening);
  };

  const handleGoogleSignIn = async () => {
    setIsLoading(true);
    try {
      // Redirect to backend OAuth endpoint
      window.location.href = 'http://localhost:5000/auth/google';
    } catch (error) {
      console.error('Google sign-in error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #1A1B2E 0%, #2B1B44 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <AppBar position="static" color="transparent" elevation={0}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            SmartMail
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button color="inherit">OUR TEAM</Button>
            <Button color="inherit">DEVELOPMENT</Button>
            <Button color="inherit">CONTACT US</Button>
          </Box>
          <IconButton
            size="large"
            edge="end"
            color="inherit"
            onClick={handleMenu}
            sx={{ ml: 2 }}
          >
            <MoreVert />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem onClick={handleClose}>Settings</MenuItem>
            <MenuItem onClick={handleClose}>Help</MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg">
        <Box
          sx={{
            minHeight: 'calc(100vh - 64px)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            position: 'relative',
            py: 8,
          }}
        >
          <Box sx={{ maxWidth: '600px', mb: 6 }}>
            <Typography
              variant="h1"
              component="h1"
              sx={{
                fontWeight: 700,
                mb: 3,
                background: 'linear-gradient(135deg, #E558C3 0%, #3FB8ED 100%)',
                backgroundClip: 'text',
                textFillColor: 'transparent',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Voice Assistant
            </Typography>
            <Typography
              variant="h6"
              color="text.secondary"
              sx={{ mb: 4, maxWidth: '500px' }}
            >
              Experience the future of email management with our advanced voice assistant. 
              Control your inbox effortlessly using natural voice commands.
            </Typography>
            <Button
              variant="contained"
              size="large"
              color="primary"
              sx={{ mr: 2 }}
            >
              Read More
            </Button>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 4 }}>
            <Button
              variant="outlined"
              size="large"
              startIcon={<Google />}
              onClick={handleGoogleSignIn}
                disabled={isLoading}
            >
                {isLoading ? <CircularProgress size={24} /> : 'Sign in with Google'}
            </Button>
              <IconButton
                onClick={handleMicToggle}
                sx={{
                  width: 56,
                  height: 56,
                  backgroundColor: isListening ? 'primary.main' : 'transparent',
                  '&:hover': {
                    backgroundColor: isListening ? 'primary.dark' : 'rgba(255, 255, 255, 0.1)',
                  },
                }}
              >
                <Mic />
              </IconButton>
            </Box>
          </Box>

          <Box
            sx={{
              position: 'absolute',
              right: '-5%',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '60%',
              opacity: 0.9,
            }}
          >
            <SoundWave />
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default LandingPage; 