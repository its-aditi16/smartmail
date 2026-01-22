import pyttsx3
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import wave
import os
import logging

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Speed of speech
engine.setProperty('volume', 1.0)  # Volume (0.0 to 1.0)

# Initialize Whisper model
model = WhisperModel("base", device="cpu", compute_type="int8")

def speak(text):
    """Speaks the given text using pyttsx3."""
    try:
        engine.say(text)
        engine.runAndWait()
        return True
    except Exception as e:
        print(f"Error in text-to-speech: {str(e)}")
        return False

def record_audio(duration=5, sample_rate=16000):
    """Records audio from microphone."""
    print("Recording...")
    recording = sd.rec(int(duration * sample_rate),
                      samplerate=sample_rate,
                      channels=1,
                      dtype=np.int16)
    sd.wait()
    print("Recording finished.")
    return recording

def save_audio(recording, sample_rate=16000, filename="temp.wav"):
    """Saves recorded audio to a WAV file."""
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(recording.tobytes())
    return filename

def listen_command(duration=5):
    """Listens for and transcribes user command."""
    try:
        # Record audio
        recording = record_audio(duration=duration)
        if recording is None:
            raise Exception("Failed to record audio")
        
        # Save to temporary file
        temp_file = save_audio(recording)
        if not temp_file:
            raise Exception("Failed to save audio file")
        
        try:
            # Transcribe using Whisper
            segments, info = model.transcribe(temp_file, beam_size=5)
            transcription = " ".join([segment.text for segment in segments])
            
            # Clean up temporary file
            try:
                os.remove(temp_file)
            except:
                pass  # Ignore cleanup errors
                
            return transcription.strip().lower()
        except Exception as e:
            raise Exception(f"Transcription error: {str(e)}")
    except Exception as e:
        logging.error(f"Error in speech recognition: {str(e)}")
        raise Exception(f"Speech recognition failed: {str(e)}")

def process_command(command):
    """Processes the voice command and returns appropriate action."""
    command = command.lower()
    
    if "continue" in command:
        return "continue"
    elif "skip" in command:
        return "skip"
    elif "back" in command:
        return "back"
    elif "promotions" in command:
        return "promotions"
    elif "important" in command:
        return "important"
    elif "quit" in command or "exit" in command:
        return "quit"
    else:
        return "unknown" 