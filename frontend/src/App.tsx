import React, { useState, useCallback, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, Box } from '@mui/material';
import Header from './components/Layout/Header';
import Dashboard from './components/Dashboard/Dashboard';
import LandingPage from './components/LandingPage/LandingPage';
import voiceRecognitionService from './services/voiceRecognition';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#E558C3',
      light: '#FF79FF',
      dark: '#B024A1',
    },
    secondary: {
      main: '#3FB8ED',
      light: '#71EAFF',
      dark: '#0088BA',
    },
    background: {
      default: '#1A1B2E',
      paper: 'rgba(26, 27, 46, 0.8)',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 700,
      fontSize: '3.5rem',
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 30,
          textTransform: 'none',
          fontSize: '1.1rem',
          padding: '12px 24px',
        },
      },
    },
  },
});

const App: React.FC = () => {
  const [isListening, setIsListening] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const location = useLocation();

  useEffect(() => {
    // Check for authentication success in URL
    const params = new URLSearchParams(location.search);
    if (params.get('auth') === 'success') {
      setIsAuthenticated(true);
    }
  }, [location]);

  const handleVoiceResult = useCallback((text: string) => {
    console.log('Voice command recognized:', text);
  }, []);

  const handleVoiceError = useCallback((error: string) => {
    console.error('Voice recognition error:', error);
    setIsListening(false);
  }, []);

  const handleCommandProcessed = useCallback((response: any) => {
    console.log('Command processed:', response);
    // Handle different types of responses here
    if (response.action === 'READ_EMAILS') {
      // Update email list
    } else if (response.action === 'SEND_EMAIL') {
      // Show confirmation
    }
  }, []);

  const handleMicToggle = useCallback(() => {
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
  }, [isListening, handleVoiceResult, handleVoiceError, handleCommandProcessed]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        {isAuthenticated && (
          <Header
            isListening={isListening}
            onMicToggle={handleMicToggle}
          />
        )}
        <Box component="main" sx={{ flexGrow: 1 }}>
          <Routes>
            <Route
              path="/"
              element={
                isAuthenticated ? (
                  <Dashboard />
                ) : (
                  <LandingPage />
                )
              }
            />
          </Routes>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

// Wrap App with Router
const AppWithRouter: React.FC = () => (
  <Router>
    <App />
  </Router>
);

export default AppWithRouter;
