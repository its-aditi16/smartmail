# Whisper Model Directory

This directory is intended to store the Whisper model files for offline speech recognition.

## Usage

The `faster-whisper` library will automatically download and cache the model files when first used. The model files will be stored in the user's cache directory.

## Model Options

- `tiny`: Fastest, least accurate
- `base`: Good balance of speed and accuracy
- `small`: More accurate, slower
- `medium`: Even more accurate, slower
- `large`: Most accurate, slowest

## Configuration

The model is configured in `tools/voice_tools.py` with the following settings:

```python
model = WhisperModel("base", device="cpu", compute_type="int8")
```

You can change the model size and compute settings as needed. 