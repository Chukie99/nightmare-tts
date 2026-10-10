"""Horror narrator engine untuk Supertonic-3.
Audit fixes:
- Sintesis PER KALIMAT (bukan chunk 300 char) -> jeda 100% terkontrol, gak ada gap compound.
- Validasi ASR per kalimat + retry kalau ada pengulangan/hallucination.
- Jeda berdasarkan MAKNA (jenis akhir kalimat + kata kunci tegang), bukan sekadar tanda baca.
- Tidak ada echo/reverb. Hanya kompresi/EQ seperlunya per preset.
"""
import re
import os
import subprocess
import difflib
import whisper
from supertonic import TTS

SPEED_MIN = 0.7  # batas model


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text.strip())
    # pecah setelah . ! ? tapi biarkan ... (ellipsis) ikut kalimat sebelumnya
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text)
    return [p.strip() for p in parts if p.strip()]


def norm_words(t: str) -> list[str]:
    t = re.sub(r"[^a-z0-9 ]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip().split()


def find_dups(words: list[str]) -> list[str]:
    dups = []
    for i in range(1, len(words)):
        if words[i] == words[i - 1] and len(words[i]) > 2:
            dups.append(words[i])
        if i >= 3 and words[i - 2:i] == words[i - 4:i - 2]:
            dups.append(" ".join(words[i - 2:i]))
    return dups


TENSION_KW = (
    "nihil", "bungkam", "menguap", "hilang", "misteri", "terkubur",
    "tidak pernah ditemukan", "keheningan", "tidak ada jawaban",
    "tanpa sadar", "gelap", "mayat", "meninggal", "tragis", "senyap",
)


def pause_after(sentence: str, preset: dict) -> float:
    """Jeda (detik) sesudah kalimat, berdasarkan struktur + makna."""
    base = preset["pause_period"]
    s = sentence.rstrip()
    if s.endswith(",") or s.endswith(";"):
        p = preset["pause_clause"]
    elif s.endswith(("...", "\u2026")):
        p = preset["pause_drama"]
    elif s.endswith(("?", "!")):
        p = preset["pause_drama"]
    else:
        p = base
    low = s.lower()
    if any(k in low for k in TENSION_KW):
        p = max(p, preset["pause_tension"])
    if s.endswith((".", "!", "?")) and any(k in low for k in TENSION_KW):
        p = max(p, preset["pause_tension"])
    return p


PRESETS = {
    # tempo percakapan naratif (bukan slow motion), jeda moderat
    "dark_documentary": dict(
        speed=0.95, pause_clause=0.16, pause_period=0.40,
        pause_drama=0.75, pause_tension=0.65,
        afx="acompressor=threshold=-20dB:ratio=3:attack=10:release=120:makeup=1.1",
    ),
    "cinematic_mystery": dict(
        speed=0.92, pause_clause=0.18, pause_period=0.48,
        pause_drama=0.90, pause_tension=0.85,
        afx=("acompressor=threshold=-22dB:ratio=3.5:attack=8:release=110:makeup=1.15,"
             "equalizer=f=150:t=q:w=1:g=1.5"),
    ),
    "horror_thriller": dict(
        speed=0.89, pause_clause=0.18, pause_period=0.52,
        pause_drama=1.0, pause_tension=0.95,
        afx=("acompressor=threshold=-24dB:ratio=4:attack=6:release=90:makeup=1.2,"
             "equalizer=f=100:t=q:w=1:g=2.0,equalizer=f=7000:t=q:w=1:g=-3.0"),
    ),
}


class HorrorNarrator:
    def __init__(self, voice="M2", total_steps=16, asr_model="base", log=print):
        self.tts = TTS("supertonic-3")
        self.vs = self.tts.get_voice_style(voice)
        self.total_steps = total_steps
        self.asr = whisper.load_model(asr_model)
        self.log = log
        self.report = []

    def _synth(self, sentence: str, speed: float) -> str:
        wav, _ = self.tts.synthesize(
            sentence, voice_style=self.vs, speed=speed,
            silence_duration=0.0, total_steps=self.total_steps,
            max_chunk_length=3000, lang="id",
        )
        path = "F:/hermes/tts-supertonic/_tmp_audit/_s.wav"
        self.tts.save_audio(wav, path)
        return path

    def _check(self, sentence: str, wav_path: str) -> dict:
        ref = norm_words(sentence)
        hyp = norm_words(self.asr.transcribe(
            wav_path, language="id", condition_on_previous_text=False)["text"])
        dups = find_dups(hyp)
        ratio = difflib.SequenceMatcher(None, ref, hyp).ratio()
        ok = (not dups) and ratio >= 0.78
        return dict(ok=ok, dups=dups, ratio=round(ratio, 3),
                    missing=len(ref) - len(hyp))

    def render(self, text: str, preset_name: str, out_path: str) -> dict:
        preset = PRESETS[preset_name]
        sentences = split_sentences(text)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        os.makedirs("F:/hermes/tts-supertonic/_tmp_audit", exist_ok=True)

        pieces = []
        stats = []
        for i, s in enumerate(sentences):
            best, best_path, best_res = None, None, None
            for attempt in range(3):  # retry kalau hallucination
                p = self._synth(s, preset["speed"])
                res = self._check(s, p)
                if best_res is None or res["ratio"] > best_res["ratio"]:
                    best, best_path, best_res = p, p, res
                if res["ok"]:
                    break
                self.log(f"  retry {i}/attempt{attempt+1}: dups={res['dups']} ratio={res['ratio']}")
            # pakai hasil terbaik (bahkan kalau belum sempurna -> dilaporkan)
            # trim hening bawaan model di awal/akhir kalimat -> jeda 100% milik
            # pause_after(), bukan akumulasi dua sumber (ini yang bikin gap 1.5-2.2s)
            seg = f"F:/hermes/tts-supertonic/_tmp_audit/seg{i:02d}.wav"
            subprocess.run(
                ["ffmpeg", "-y", "-i", best_path, "-af",
                 "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,"
                 "areverse,"
                 "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.10,"
                 "areverse", "-ar", "44100", seg],
                check=True, capture_output=True)
            pieces.append(seg)
            stats.append(dict(i=i, text=s, **best_res))
            if not best_res["ok"]:
                self.log(f"  WARN kalimat {i}: {best_res}")

            p = pause_after(s, preset)
            if i < len(sentences) - 1:
                sil = f"F:/hermes/tts-supertonic/_tmp_audit/sil{i:02d}.wav"
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "lavfi", "-i",
                     "anullsrc=r=44100:cl=mono", "-t", f"{p:.2f}", sil],
                    check=True, capture_output=True)
                pieces.append(sil)

        lst = "F:/hermes/tts-supertonic/_tmp_audit/list.txt"
        with open(lst, "w", encoding="utf-8") as f:
            for x in pieces:
                f.write(f"file '{os.path.abspath(x).replace(chr(92), '/')}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
             "-af", preset["afx"], "-ar", "44100",
             "-c:a", "libmp3lame", "-q:a", "2", out_path],
            check=True, capture_output=True)

        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", out_path],
            capture_output=True, text=True).stdout.strip())
        bad = [s for s in stats if not s["ok"]]
        rep = dict(preset=preset_name, out=out_path, duration=round(dur, 1),
                   sentences=len(sentences), issues=bad)
        self.report.append(rep)
        return rep


if __name__ == "__main__":
    script = (
        "18 Oktober 2020. Desa Salapian, Kabupaten Langkat, Sumatera Utara. "
        "Siang itu seharusnya menjadi hari yang biasa saja bagi Yogi, Nizam, dan Alfaro. "
        "Mereka pamit ke orang tua mereka, hanya untuk melihat alat berat bekerja di "
        "kebun sawit tak jauh dari rumah. Pukul dua siang, suara tawa mereka masih terdengar. "
        "Mereka berlari kecil, antusias melihat excavator yang mengeruk tanah. "
        "Namun, tak sampai satu jam kemudian, keheningan mulai menyelimuti kebun sawit itu. "
        "Ketika sang ibu memanggil untuk makan siang, tidak ada jawaban. "
        "Pencarian besar-besaran pun dilakukan. Ratusan warga, anjing pelacak, dan aparat "
        "turun ke lokasi. Mereka menyisir setiap jengkal semak, menguras parit di sekitar kebun. "
        "Namun hasilnya nihil. Tanah Langkat seolah bungkam. Tidak ada jejak kaki, tidak ada "
        "tanda kekerasan. Tiga bocah itu seolah menguap ke udara. Sampai detik ini, mereka "
        "tidak pernah ditemukan. Dan di balik deretan pohon sawit itu, sebuah misteri abadi "
        "tetap terkubur."
    )
    n = HorrorNarrator()
    for name in ("dark_documentary", "cinematic_mystery", "horror_thriller"):
        print(f"=== {name} ===")
        rep = n.render(script, name,
                       f"F:/hermes/tts-supertonic/output/FIX_{name}.mp3")
        print(f"  durasi={rep['duration']}s kalimat={rep['sentences']} "
              f"issue={len(rep['issues'])}")
        for it in rep["issues"]:
            print(f"   ! {it['i']}: dups={it['dups']} ratio={it['ratio']} "
                  f"| {it['text'][:60]}")
    print("ALL DONE")
