"""
Supertonic-3 TTS Runner — Indonesian (id), dark storytelling voice.
Reads: naskah.txt | Output: output.wav
API asli: TTS() -> get_voice_style(voice) -> synthesize(text, style, speed, lang)
Voices: M1..M5 (pria), F1..F5 (wanita)
"""
from pathlib import Path
from supertonic import TTS

BASE = Path("F:/hermes/tts-supertonic")

def main():
    naskah_path = BASE / "naskah.txt"
    if not naskah_path.exists():
        print("Error: naskah.txt tidak ditemukan!")
        return

    text = naskah_path.read_text(encoding="utf-8").strip()
    print(f"[INFO] Membaca naskah ({len(text)} karakter)...")

    tts = TTS(model="supertonic-3")  # auto download model pertama kali
    style = tts.get_voice_style("M2")  # M2 = pria, cocok narasi misteri
    print("[INFO] Generate audio (lang=id, speed=0.92)...")
    wav, sr = tts.synthesize(text, style, speed=0.92, lang="id")

    out_path = BASE / "output.wav"
    tts.save_audio(wav, str(out_path))
    print(f"[OK] Audio tersimpan di: {out_path}")

if __name__ == "__main__":
    main()