# -*- coding: utf-8 -*-
"""
PENGATUR GAYA & PROSODI TTS - "Ardan Nightmare Side"
(Drama Radio Horor Klasik)

Ubah naskah biasa -> narasi mencekam lewat JEDA & PACING.
Bukan penurunan pitch ekstrem. Suara tetap MANUSIA.

Konfigurasi TTS Supertonic-3:
  speaking_rate -> speed=0.82
  pitch_shift   -> rubberband -1.0 semitone (FFmpeg post, JANGAN lebih)
  expressiveness-> diakali kompresi ringan (close-mic feel)
  temperature   -> model deterministik, tidak didukung
  style_blend   -> voice M2 + preprocessing ini

Aturan:
  1. Sisip '...' antar frasa kunci (jeda dramatis)
  2. DILARANG ALL CAPS & tanda seru berlebihan
  3. Panjangkan vokal kata klimaks HALUS (1x per naskah)
  4. Kalimat menggantung di akhir frasa
"""
import re

SPEAKING_RATE = 0.82
PITCH_SHIFT_ST = -1.0
VOICE = "M2"

# Konjungsi yang jadi titik pecah frasa
KONJUNGSI = ("tapi", "namun", "yang", "karena", "hingga", "sehingga",
             "sampai", "ketika", "saat", "lalu", "kemudian", "bahkan")

# Kata klimaks (elongasi vokal halus, 1x dalam naskah)
KLIMAKS = ["perlahan", "terbang", "menghilang", "berpindah", "menimbun",
           "runtuh", "terkubur", "terhapus", "selamanya", "diam"]


def _normalize(text: str) -> str:
    """Buang ALL CAPS, tanda seru, titik berlebih, spasi aneh."""
    text = text.replace("\n", " ")
    text = re.sub(r"!", ".", text)                       # tanda seru -> titik
    text = re.sub(r"([A-Z]{4,})", lambda m: m.group(0).capitalize(), text)  # ALL CAPS -> normal
    text = re.sub(r"\.{2,}", "...", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_kalimat(text: str) -> list:
    """Pisah jadi kalimat utuh (berdasar . ? :)."""
    return [k.strip() for k in re.split(r"(?<=[.?])\s+", text) if k.strip()]


def _split_frasa(kalimat: str) -> list:
    """
    Pecah kalimat jadi frasa alami:
    - di koma
    - sebelum konjungsi (tapi/karena/hingga/dll)
    Kalimat pendek (<7 kata) gak dipecah.
    """
    if len(kalimat.split()) < 7:
        return [kalimat]

    # pecah sebelum konjungsi
    pat = r"(?:,\s+|\s+)(?=(" + "|".join(KONJUNGSI) + r")\b)"
    frasa = [f.strip() for f in re.split(pat, kalimat, flags=re.IGNORECASE) if f and f.strip()]

    # gabung konjungsi kembali ke frasa setelahnya, baru pecah ulang per koma
    hasil = []
    buf = ""
    i = 0
    while i < len(frasa):
        f = frasa[i]
        if f.lower() in KONJUNGSI and i + 1 < len(frasa):
            buf += (f + " " + frasa[i + 1]).strip()
            i += 2
        else:
            buf = (buf + " " + f).strip() if buf else f
            i += 1
        # pecah buf di koma internal jadi sub-frasa
        sub = [s.strip() for s in buf.split(",") if s.strip()]
        hasil.extend(sub)
        buf = ""
    if buf:
        hasil.append(buf)
    return hasil if hasil else [kalimat]


def _panjangkan_klimaks(text: str) -> str:
    """Elongasi vokal HALUS di 1 kata klimaks (yang paling akhir muncul)."""
    for k in KLIMAKS:
        m = re.search(rf"\b{re.escape(k)}\b", text, flags=re.IGNORECASE)
        if m:
            word = m.group(0)
            new = re.sub(r"([aiueoAIUEO])", lambda mm: mm.group(1) * 2, word, count=1)
            if new != word:
                text = text[:m.start()] + new + text[m.end():]
            break
    return text


def nightmare_side(text: str) -> str:
    """Pipeline utama."""
    text = _normalize(text)
    out_kalimat = []
    for kal in _split_kalimat(text):
        frasa = _split_frasa(kal)
        # gabung frasa dengan '...' (tanpa koma, tanpa spasi aneh)
        joined = " ... ".join(frasa)
        # rapetin titik-titik dobel
        joined = re.sub(r"\.\s*\.\s*\.", "...", joined)
        out_kalimat.append(joined)

    hasil = " ".join(out_kalimat)
    hasil = _panjangkan_klimaks(hasil)

    # kalimat terakhir -> menggantung: akhiri '...' bukan '.'
    hasil = re.sub(r"\.\s*$", " ...", hasil)
    hasil = re.sub(r"\s+", " ", hasil).strip()
    return hasil


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "F:/hermes/tts-supertonic/naskah_full_bersih.txt"
    dst = sys.argv[2] if len(sys.argv) > 2 else "F:/hermes/tts-supertonic/naskah_nightmare.txt"
    teks = open(src, encoding="utf-8").read()
    hasil = nightmare_side(teks)
    open(dst, "w", encoding="utf-8").write(hasil)
    print("=== HASIL OLAHAN (Ardan Nightmare Side) ===")
    print(hasil)
    print(f"\n[OK] {dst} ({len(hasil)} karakter)")