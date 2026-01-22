class SpeechService {
  private synthesis: SpeechSynthesis;
  private voice: SpeechSynthesisVoice | null = null;
  private defaultRate: number = 1.5; // Faster default rate
  private defaultPitch: number = 1.0;
  private currentUtterance: SpeechSynthesisUtterance | null = null;

  constructor() {
    if (!('speechSynthesis' in window)) {
      throw new Error('Speech synthesis not supported');
    }
    this.synthesis = window.speechSynthesis;
    this.initVoice();
  }

  private initVoice() {
    // Get available voices
    const voices = this.synthesis.getVoices();
    if (voices.length > 0) {
      // Try to find a female voice
      this.voice = voices.find(voice => 
        voice.name.toLowerCase().includes('female') ||
        voice.name.toLowerCase().includes('woman')
      ) || voices[0];
    }
  }

  public speak(text: string, options: {
    rate?: number;
    pitch?: number;
    onEnd?: () => void;
    onStart?: () => void;
  } = {}) {
    // Cancel any ongoing speech
    this.stop();

    const utterance = new SpeechSynthesisUtterance(text);
    this.currentUtterance = utterance;
    
    // Set voice and speech properties
    if (this.voice) {
      utterance.voice = this.voice;
    }
    utterance.rate = options.rate || this.defaultRate;
    utterance.pitch = options.pitch || this.defaultPitch;

    // Set callbacks
    if (options.onStart) {
      utterance.onstart = options.onStart;
    }
    if (options.onEnd) {
      utterance.onend = () => {
        this.currentUtterance = null;
        if (options.onEnd) {
          options.onEnd();
        }
      };
    } else {
      utterance.onend = () => {
        this.currentUtterance = null;
      };
    }

    // Start speaking
    this.synthesis.speak(utterance);
  }

  public stop() {
    if (this.currentUtterance) {
      this.synthesis.cancel();
      this.currentUtterance = null;
    }
  }

  public setDefaultRate(rate: number) {
    this.defaultRate = rate;
  }

  public getDefaultRate(): number {
    return this.defaultRate;
  }

  public isSpeaking(): boolean {
    return this.synthesis.speaking;
  }

  public isSupported(): boolean {
    return 'speechSynthesis' in window;
  }
}

// Add type declarations for the Web Speech API
declare global {
  interface Window {
    readonly speechSynthesis: SpeechSynthesis;
  }
}

export default new SpeechService(); 