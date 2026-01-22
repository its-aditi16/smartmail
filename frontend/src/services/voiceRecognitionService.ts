// Define the base interfaces for Web Speech API
interface SpeechRecognitionErrorEvent {
  error: string;
  message?: string;
}

interface SpeechRecognitionResult {
  readonly length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  readonly transcript: string;
  readonly confidence: number;
}

interface SpeechRecognitionResultList {
  readonly length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionEvent extends Event {
  readonly resultIndex: number;
  readonly results: SpeechRecognitionResultList;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  grammars: any;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onaudioend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onaudiostart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null;
  onnomatch: ((this: SpeechRecognition, ev: Event) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onsoundend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onsoundstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  abort(): void;
  start(): void;
  stop(): void;
}

interface SpeechRecognitionConstructor {
  new(): SpeechRecognition;
  prototype: SpeechRecognition;
}

declare global {
  var SpeechRecognition: SpeechRecognitionConstructor | undefined;
  var webkitSpeechRecognition: SpeechRecognitionConstructor | undefined;
}

class VoiceRecognitionService {
  private recognition: SpeechRecognition | null = null;
  private isListening: boolean = false;
  private retryCount: number = 0;
  private maxRetries: number = 3;
  private retryDelay: number = 2000; // 2 seconds
  private isOnline: boolean = navigator.onLine;
  private currentOptions: {
    onStart?: () => void;
    onEnd?: () => void;
    onResult?: (text: string) => void;
    onError?: (error: string) => void;
  } = {};
  private retryTimer: NodeJS.Timeout | null = null;

  constructor() {
    // Check browser support first
    if (!this.isSupported()) {
      console.error('Speech recognition is not supported in this browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.error('Speech recognition constructor not found');
      return;
    }

    try {
      this.initRecognition(SpeechRecognition);
    } catch (error) {
      console.error('Failed to initialize speech recognition:', error);
    }
    
    // Add online/offline event listeners
    window.addEventListener('online', this.handleOnlineStatus);
    window.addEventListener('offline', this.handleOnlineStatus);
  }

  private handleOnlineStatus = () => {
    this.isOnline = navigator.onLine;
    console.log('Network status changed:', this.isOnline ? 'online' : 'offline');
  }

  private async checkNetworkConnectivity(): Promise<boolean> {
    try {
      // Try our backend first
      const response = await fetch('http://localhost:5000/api/health', {
        method: 'GET', // Use GET instead of HEAD
        cache: 'no-cache',
        mode: 'cors',
        credentials: 'same-origin'
      });
      return response.ok;
    } catch (error) {
      console.error('Backend health check failed:', error);
      // If we can't reach our backend, try a simple ping to a reliable service
      try {
        const pingResponse = await fetch('https://api.ipify.org?format=json', {
          method: 'GET',
          mode: 'cors',
          cache: 'no-cache'
        });
        return pingResponse.ok;
      } catch (pingError) {
        console.error('Fallback network check failed:', pingError);
        return false;
      }
    }
  }

  private async requestMicrophonePermission(): Promise<boolean> {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      console.log('Microphone permission granted');
      return true;
    } catch (error) {
      console.error('Microphone permission denied:', error);
      return false;
    }
  }

  private initRecognition(SpeechRecognition: SpeechRecognitionConstructor) {
    try {
      this.recognition = new SpeechRecognition();
      if (this.recognition) {
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;
      }
    } catch (error) {
      console.error('Failed to initialize speech recognition:', error);
      this.recognition = null;
    }
  }

  public async start(options: {
    onStart?: () => void;
    onEnd?: () => void;
    onResult?: (text: string) => void;
    onError?: (error: string) => void;
  } = {}) {
    this.currentOptions = options;
    
    // Check browser support
    if (!this.isSupported()) {
      if (options.onError) {
        options.onError('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Opera.');
      }
      return;
    }

    // Check if we're on HTTPS or localhost
    if (window.location.protocol !== 'https:' && window.location.hostname !== 'localhost') {
      if (options.onError) {
        options.onError('Speech recognition requires HTTPS or localhost. Please use a secure connection.');
      }
      return;
    }

    // Check network connectivity with a more lenient approach
    const isConnected = await this.checkNetworkConnectivity();
    if (!isConnected) {
      console.warn('Network connectivity check failed, but proceeding with voice recognition anyway');
      // Continue with voice recognition even if network check fails
      // as the Web Speech API might still work
    }

    // Check microphone permission
    const hasMicPermission = await this.requestMicrophonePermission();
    if (!hasMicPermission) {
      if (options.onError) {
        options.onError('Microphone permission denied. Please allow microphone access in your browser settings.');
      }
      return;
    }

    if (!this.recognition) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.initRecognition(SpeechRecognition);
      }
    }

    if (!this.recognition) {
      if (options.onError) {
        options.onError('Speech recognition not supported or failed to initialize');
      }
      return;
    }

    this.retryCount = 0;
    this.isListening = true;

    this.recognition.onstart = () => {
      console.log('Voice recognition started');
      if (this.currentOptions.onStart) {
        this.currentOptions.onStart();
      }
    };

    this.recognition.onend = async () => {
      console.log('Voice recognition ended');
      // If still listening and under max retries, attempt to restart on network error
      if (this.isListening && this.retryCount < this.maxRetries) {
        this.retryCount++;
        console.log(`Retrying voice recognition (attempt ${this.retryCount}/${this.maxRetries})`);
        this.retryTimer = setTimeout(() => {
          if (this.recognition && this.isListening) {
            try {
              this.recognition.start();
            } catch (error) {
              console.error('Failed to restart voice recognition:', error);
              this.isListening = false;
              if (this.currentOptions.onError) {
                this.currentOptions.onError('Failed to restart voice recognition. Please try again.');
              }
              if (this.currentOptions.onEnd) {
                this.currentOptions.onEnd();
              }
            }
          }
        }, this.retryDelay);
      } else {
        this.isListening = false;
        if (this.currentOptions.onEnd) {
          this.currentOptions.onEnd();
        }
      }
    };

    this.recognition.onresult = (event: SpeechRecognitionEvent) => {
      if (event.results.length > 0) {
        const result = event.results[event.resultIndex];
        if (result.length > 0) {
          const text = result[0].transcript.trim();
          console.log('Recognized text:', text);
          if (this.currentOptions.onResult) {
            this.currentOptions.onResult(text);
          }
          // Reset retry count on successful result
          this.retryCount = 0;
        }
      }
    };

    this.recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      if (event.error === 'not-allowed') {
        this.isListening = false;
        if (options.onError) {
          options.onError('Microphone access denied. Please allow microphone access in your browser settings.');
        }
      } else if (event.error === 'network') {
        console.log(`Network error (attempt ${this.retryCount + 1}/${this.maxRetries})`);
        // Let onend handler manage retries for network errors
      } else if (event.error === 'no-speech') {
        // Don't treat no-speech as a fatal error, just retry
        console.log('No speech detected, continuing to listen...');
        if (this.recognition && this.isListening) {
          try {
            this.recognition.stop();  // Stop current recognition
            setTimeout(() => {
              if (this.recognition && this.isListening) {
                this.recognition.start();  // Restart recognition
              }
            }, 100);  // Small delay before restart
          } catch (error) {
            console.error('Error restarting recognition:', error);
          }
        } else {
          this.isListening = false;
          if (options.onError) {
            options.onError(`Voice recognition error: ${event.error}`);
          }
        }
      } else {
        this.isListening = false;
        if (options.onError) {
          options.onError(`Voice recognition error: ${event.error}`);
        }
      }
    };

    try {
      await this.recognition.start();
    } catch (error) {
      console.error('Failed to start voice recognition:', error);
      this.isListening = false;
      if (options.onError) {
        options.onError('Failed to start voice recognition. Please try again.');
      }
    }
  }

  public stop() {
    this.isListening = false;
    
    // Clear any pending retry timer
    if (this.retryTimer) {
      clearTimeout(this.retryTimer);
      this.retryTimer = null;
    }

    if (this.recognition) {
      try {
        this.recognition.stop();
        // Force cleanup if needed, as onend might not trigger if not started
        // But usually onEnd is triggered. 
        // If we are in the wait-for-retry loop, recognition is not running, so onEnd won't trigger.
        // So we must manually trigger onEnd if valid.
        // We can safely trigger onEnd if the service was thinking it's listening.
      } catch (error) {
        console.error('Error stopping voice recognition:', error);
      }
    }
    
    // Ensure the UI is updated even if we were just waiting for a retry
    if (this.currentOptions.onEnd) {
      this.currentOptions.onEnd();
    }
  }

  public isSupported(): boolean {
    return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  }

  public dispose() {
    window.removeEventListener('online', this.handleOnlineStatus);
    window.removeEventListener('offline', this.handleOnlineStatus);
    this.stop();
  }
}

export default new VoiceRecognitionService(); 