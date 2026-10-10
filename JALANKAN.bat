@echo off
cd /d "F:\hermes\tts-supertonic"
python -c "import soundfile, supertonic; from pathlib import Path; import torch; from supertonic import TTS"
echo Dependencies ready
python -c "
from pathlib import Path
import soundfile as sf
from supertonic import TTS

naskah = Path('F:/hermes/tts-supertonic/naskah.txt')
text = naskah.read_text(encoding='utf-8').strip()
print(f'Reading {len(text)} chars...')

tts = TTS(language='id')
audio, sr = tts.tts(text=text, voice_style='whispering', speed=0.92, pitch=-3)

out = Path('F:/hermes/tts-supertonic/output.wav')
sf.write(out, audio, sr)
print(f'Saved to {out}')
"
echo Done! Check output.wav
pause