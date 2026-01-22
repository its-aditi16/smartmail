import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Box,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Slider,
  Stack,
  Grid,
  Button,
  TextField,
} from '@mui/material';
import { Email, Mic, MicOff, VolumeUp, VolumeOff } from '@mui/icons-material';
import emailService from '../../services/emailService';
import voiceRecognitionService from '../../services/voiceRecognitionService';
import speechService from '../../services/speechService';
import { EmailItem, VoiceCommandResponse } from '../../types/email';

const TroubleshootingGuide = () => (
  <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
    <Typography variant="h6" gutterBottom>
      Troubleshooting Guide
    </Typography>
    <Box sx={{ mb: 2 }}>
      <Typography variant="body2">
        If you're having issues with voice recognition, please check the following:
      </Typography>
    </Box>
    <List dense>
      <ListItem>
        <ListItemText
          primary="1. Browser Compatibility"
          secondary="Use Chrome, Edge, or Opera for best results. Voice recognition may not work in other browsers."
        />
      </ListItem>
      <ListItem>
        <ListItemText
          primary="2. Microphone Access"
          secondary="Click the camera icon in your browser's address bar and ensure microphone access is allowed."
        />
      </ListItem>
      <ListItem>
        <ListItemText
          primary="3. Internet Connection"
          secondary="Voice recognition requires an active internet connection. Check your network status."
        />
      </ListItem>
      <ListItem>
        <ListItemText
          primary="4. HTTPS/Localhost"
          secondary="The site must be running on HTTPS or localhost for microphone access to work."
        />
      </ListItem>
    </List>
  </Paper>
);

interface EmailListItemProps {
  email: EmailItem;
  selected?: boolean;
  onClick?: () => void;
}

const EmailListItem: React.FC<EmailListItemProps> = ({ email, selected, onClick }) => (
  <ListItem
    button
    divider
    selected={selected}
    onClick={onClick}
    sx={{
      backgroundColor: email.isUnread
        ? 'rgba(25, 118, 210, 0.08)'
        : 'transparent',
      '&.Mui-selected': {
        backgroundColor: 'rgba(25, 118, 210, 0.16)',
      },
    }}
  >
    <ListItemText
      primary={
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Email color={email.isUnread ? 'primary' : 'disabled'} />
          <Typography
            variant="subtitle1"
            component="span"
            fontWeight={email.isUnread ? 'bold' : 'normal'}
          >
            {email.subject}
          </Typography>
        </Box>
      }
      secondary={
        <Box component="div" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box component="span">
            <Typography variant="body2" component="span">
              {email.sender}
            </Typography>
          </Box>
          <Box component="span">
            <Chip
              label={new Date(email.date).toLocaleDateString()}
              size="small"
              variant="outlined"
              sx={{ height: 24 }}
            />
          </Box>
        </Box>
      }
    />
  </ListItem>
);

const Dashboard: React.FC = () => {
  const [emails, setEmails] = useState<EmailItem[]>([]);
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastCommand, setLastCommand] = useState<string>('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [processingCommand, setProcessingCommand] = useState(false);
  const [speechRate, setSpeechRate] = useState(1.5);
  const [emailStats, setEmailStats] = useState({ total: 0, unread: 0 });
  const [commandFeedback, setCommandFeedback] = useState<string>('');

  useEffect(() => {
    let mounted = true;

    const initializeAssistant = async () => {
      try {
        const response = await emailService.startEmailAssistant();
        if (mounted && response.speech_response) {
          speak(response.speech_response);
        }
        if (mounted) {
          fetchEmails();
        }
      } catch (err) {
        if (mounted) {
          setError('Failed to initialize email assistant');
          setLoading(false);
        }
      }
    };

    initializeAssistant();

    return () => {
      mounted = false;
      // Cleanup speech and voice recognition
      speechService.stop();
      voiceRecognitionService.dispose();
    };
  }, []);

  const speak = useCallback((text: string) => {
    speechService.speak(text, {
      rate: speechRate,
      onStart: () => setIsSpeaking(true),
      onEnd: () => setIsSpeaking(false),
    });
  }, [speechRate]);

  const fetchEmails = async () => {
    try {
      const response = await emailService.getEmails();
      setEmails(response.emails);
      if (response.speech_response) {
        speak(response.speech_response);
      }
      setError(null);
    } catch (err) {
      setError('Failed to fetch emails');
    } finally {
      setLoading(false);
    }
  };

  const handleEmailSelect = (emailId: string) => {
    setSelectedEmailId(emailId);
  };

  const handleVoiceCommand = async (command: string) => {
    setLastCommand(command);
    setProcessingCommand(true);
    setCommandFeedback(`Processing command: ${command}`);

    try {
      // If no email is selected and we have emails, select the first one
      if (!selectedEmailId && emails.length > 0) {
        setSelectedEmailId(emails[0].id);
      }


      const response = await emailService.processVoiceCommand(command);
      console.log('Command response:', response);
      
      // Handle the response based on the action
      switch (response.action) {
        case 'next':
        case 'previous':
        case 'switch_tab':
        case 'search':
          await fetchEmails();
          setCommandFeedback(`Executed command: ${command}`);
          break;
        case 'read':
        case 'mark_unread':
        case 'delete':
        case 'archive':
        case 'star':
          if (response.email) {
            // Update the affected email in the list
            setEmails(prevEmails => 
              prevEmails.map(email => 
                email.id === response.email?.id ? response.email : email
              ).filter(email => email.id !== response.email?.id) // Remove deleted emails
            );
            
            // If the current email was affected, update selection
            if (selectedEmailId === response.email.id) {
              const currentIndex = emails.findIndex(e => e.id === selectedEmailId);
              if (currentIndex < emails.length - 1) {
                setSelectedEmailId(emails[currentIndex + 1].id);
              } else if (currentIndex > 0) {
                setSelectedEmailId(emails[currentIndex - 1].id);
              } else {
                setSelectedEmailId(null);
              }
            }
            setCommandFeedback(`Successfully ${response.action}ed email`);
          }
          break;
        default:
          setCommandFeedback('Unknown command');
          break;
      }

      // Speak the response message if available
      if (response.speech_response) {
        speak(response.speech_response);
      }

      if (!response.success) {
        setError(response.message);
        setCommandFeedback(`Command failed: ${response.message}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to process voice command';
      setError(errorMessage);
      setCommandFeedback(`Error: ${errorMessage}`);
      console.error('Voice command error:', err);
    } finally {
      setProcessingCommand(false);
    }
  };

  const handleMicToggle = useCallback(async () => {
    if (!isListening) {
      try {
        // Check browser support first
        if (!voiceRecognitionService.isSupported()) {
          setError('Voice recognition is not supported in this browser. Please use Chrome, Edge, or Opera.');
          return;
        }

        await voiceRecognitionService.start({
          onStart: () => {
            setIsListening(true);
            speak("I'm listening");
          },
          onEnd: () => setIsListening(false),
          onResult: handleVoiceCommand,
          onError: (error) => {
            setError(error);
            setIsListening(false);
            console.error('Voice recognition error:', error);
          },
        });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to start voice recognition';
        setError(errorMessage);
        setIsListening(false);
        console.error('Voice recognition error:', err);
      }
    } else {
      voiceRecognitionService.stop();
    }
  }, [isListening, handleVoiceCommand, speak]);

  // Add a helper function to check microphone permission
  const checkMicrophonePermission = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      return true;
    } catch (error) {
      console.error('Microphone permission check failed:', error);
      return false;
    }
  }, []);

  // Check microphone permission when component mounts
  useEffect(() => {
    checkMicrophonePermission().then(hasPermission => {
      if (!hasPermission) {
        setError(
          'Microphone access is required. Please click the camera icon in your browser\'s address bar and allow microphone access.'
        );
      }
    });
  }, [checkMicrophonePermission]);

  const handleSpeechRateChange = (event: Event, newValue: number | number[]) => {
    const rate = newValue as number;
    setSpeechRate(rate);
    speechService.setDefaultRate(rate);
  };

  const toggleSpeech = () => {
    if (isSpeaking) {
      speechService.stop();
      setIsSpeaking(false);
    }
  };

  const [debugCommand, setDebugCommand] = useState('');

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }} 
          onClose={() => setError(null)}
          action={
            <Button color="inherit" size="small" onClick={() => setError(null)}>
              Dismiss
            </Button>
          }
        >
          {error}
        </Alert>
      )}

      {/* Debug Command Section */}
      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Debug Command Input
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            fullWidth
            label="Enter command (e.g., 'read body', 'next')"
            value={debugCommand}
            onChange={(e) => setDebugCommand(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleVoiceCommand(debugCommand)}
            size="small"
          />
          <Button 
            variant="contained" 
            onClick={() => handleVoiceCommand(debugCommand)}
            disabled={!debugCommand}
          >
            Send
          </Button>
        </Box>
      </Paper>

      <TroubleshootingGuide />

      <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={2}>
            {processingCommand ? (
              <CircularProgress size={24} />
            ) : (
              <Typography variant="body1">
                Last command: {lastCommand || 'No commands yet'}
              </Typography>
            )}
          </Box>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="body2" color="textSecondary">
              {commandFeedback}
            </Typography>
            <Box sx={{ width: 150 }}>
              <Typography variant="caption" color="textSecondary">
                Speech Rate
              </Typography>
              <Slider
                value={speechRate}
                onChange={handleSpeechRateChange}
                min={0.5}
                max={3}
                step={0.1}
                valueLabelDisplay="auto"
                size="small"
              />
            </Box>
            <Tooltip title={isSpeaking ? 'Stop speaking' : 'Speaking disabled'}>
              <span>
                <IconButton onClick={toggleSpeech} disabled={!isSpeaking}>
                  {isSpeaking ? <VolumeUp /> : <VolumeOff />}
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title={isListening ? 'Stop listening' : 'Start listening'}>
              <IconButton
                onClick={handleMicToggle}
                color={isListening ? 'primary' : 'default'}
                sx={{
                  backgroundColor: isListening ? 'rgba(25, 118, 210, 0.1)' : 'transparent',
                }}
              >
                {isListening ? <Mic /> : <MicOff />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Paper>

      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Inbox
        </Typography>
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : (
          <List>
            {emails.length === 0 ? (
              <ListItem>
                <ListItemText primary="No emails to display" />
              </ListItem>
            ) : (
              emails.map((email) => (
                <EmailListItem 
                  key={email.id} 
                  email={email}
                  selected={email.id === selectedEmailId}
                  onClick={() => handleEmailSelect(email.id)}
                />
              ))
            )}
          </List>
        )}
      </Paper>
    </Container>
  );
};

export default Dashboard; 