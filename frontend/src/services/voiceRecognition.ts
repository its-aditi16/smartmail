import { emailApi } from './api';

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
  error: SpeechRecognitionError;
}

interface SpeechRecognitionError extends Event {
  error: string;
  message: string;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  isFinal: boolean;
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  maxAlternatives: number;
  onaudiostart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onaudioend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onerror: ((this: SpeechRecognition, ev: SpeechRecognitionError) => any) | null;
  onnomatch: ((this: SpeechRecognition, ev: Event) => any) | null;
  onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null;
  onsoundstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onsoundend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  onspeechend: ((this: SpeechRecognition, ev: Event) => any) | null;
  onstart: ((this: SpeechRecognition, ev: Event) => any) | null;
  abort(): void;
  start(): void;
  stop(): void;
}

interface SpeechRecognitionConstructor {
  new (): SpeechRecognition;
}

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

class VoiceRecognitionService {
  private recognition: SpeechRecognition | null = null;
  private isListening: boolean = false;
  private processingCommand: boolean = false;

  constructor() {
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        this.recognition = new SpeechRecognition();
        this.setupRecognition();
      }
    }
  }

  private setupRecognition() {
    if (!this.recognition) return;

    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = 'en-US';
  }

  public async start(
    onResult: (text: string) => void,
    onError: (error: string) => void,
    onCommandProcessed: (response: any) => void
  ) {
    if (!this.recognition) {
      onError('Speech recognition is not supported in this browser.');
      return;
    }

    if (this.isListening) return;

    this.recognition.onstart = () => {
      this.isListening = true;
    };

    this.recognition.onend = () => {
      this.isListening = false;
    };

    this.recognition.onresult = async (event: SpeechRecognitionEvent) => {
      const last = event.results.length - 1;
      const result = event.results[last];
      
      if (result.isFinal && !this.processingCommand) {
        const command = result.item(0).transcript.trim();
        onResult(command);
        
        try {
          this.processingCommand = true;
          const response = await emailApi.processVoiceCommand(command);
          onCommandProcessed(response);
        } catch (error) {
          onError('Error processing voice command');
        } finally {
          this.processingCommand = false;
        }
      }
    };

    this.recognition.onerror = (event: SpeechRecognitionError) => {
      onError(event.error);
      this.isListening = false;
    };

    try {
      this.recognition.start();
    } catch (error) {
      onError('Failed to start voice recognition');
    }
  }

  public stop() {
    if (!this.recognition || !this.isListening) return;

    this.recognition.stop();
    this.isListening = false;
  }

  public isSupported(): boolean {
    return ('SpeechRecognition' in window) || ('webkitSpeechRecognition' in window);
  }
}

const voiceRecognitionService = new VoiceRecognitionService();
export default voiceRecognitionService; 