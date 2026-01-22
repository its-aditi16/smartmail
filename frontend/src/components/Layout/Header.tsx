import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Snackbar,
  Alert,
  CircularProgress,
} from '@mui/material';
import { Mic, MicOff } from '@mui/icons-material';

interface HeaderProps {
  isListening: boolean;
  onMicToggle: () => void;
}

const Header: React.FC<HeaderProps> = ({ isListening, onMicToggle }) => {
  const [feedback, setFeedback] = React.useState<{
    message: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);
  const [isProcessing, setIsProcessing] = React.useState(false);

  const handleVoiceResult = (text: string) => {
    setFeedback({ message: `Recognized: ${text}`, type: 'info' });
  };

  const handleVoiceError = (error: string) => {
    setFeedback({ message: `Error: ${error}`, type: 'error' });
  };

  const handleCommandProcessed = (response: any) => {
    setFeedback({
      message: `Command executed: ${response.action || 'Unknown action'}`,
      type: 'success',
    });
    setIsProcessing(false);
  };

  const handleCloseFeedback = () => {
    setFeedback(null);
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Smartmail
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {isProcessing && (
            <CircularProgress
              size={24}
              sx={{ color: 'white' }}
            />
          )}
          <IconButton
            color="inherit"
            onClick={onMicToggle}
            sx={{
              backgroundColor: isListening ? 'rgba(255,255,255,0.2)' : 'transparent',
              '&:hover': {
                backgroundColor: isListening
                  ? 'rgba(255,255,255,0.3)'
                  : 'rgba(255,255,255,0.1)',
              },
            }}
          >
            {isListening ? <Mic /> : <MicOff />}
          </IconButton>
        </Box>
      </Toolbar>
      {feedback && (
        <Snackbar
          open={true}
          autoHideDuration={6000}
          onClose={handleCloseFeedback}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert
            onClose={handleCloseFeedback}
            severity={feedback.type}
            sx={{ width: '100%' }}
          >
            {feedback.message}
          </Alert>
        </Snackbar>
      )}
    </AppBar>
  );
};

export default Header; 