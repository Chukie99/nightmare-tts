import os
import subprocess
import numpy as np
from supertonic import TTS

# Naskah standar yang bersih dari hyphen berlebih atau karakter aneh yang memicu pengulangan
script_text = (
    "18 Oktober 2020. Desa Salapian, Kabupaten Langkat, Sumatera Utara. "
    "Siang itu seharusnya menjadi hari yang biasa saja bagi Yogi, Nizam, dan Alfaro. "
    "Mereka pamit ke orang tua mereka, hanya untuk melihat alat berat bekerja di kebun sawit tak jauh dari rumah. "
    "Pukul dua siang, suara tawa mereka masih terdengar. Mereka berlari kecil, antusias melihat excavator yang mengeruk tanah. "
    "Namun, tak sampai satu jam kemudian, keheningan mulai menyelimuti kebun sawit itu. "
    "Ketika sang ibu memanggil untuk makan siang, tidak ada jawaban. "
    "Pencarian besar-besaran pun dilakukan. Ratusan warga, anjing pelacak, dan aparat turun ke lokasi. "
    "Mereka menyisir setiap jengkal semak, menguras parit di sekitar kebun. "
    "Namun hasilnya nihil. Tanah Langkat seolah bungkam. Tidak ada jejak kaki, tidak ada tanda kekerasan. "
    "Tiga bocah itu seolah menguap ke udara. "
    "Sampai detik ini, mereka tidak pernah ditemukan. "
    "Dan di balik deretan pohon sawit itu, sebuah misteri abadi tetap terkubur."
)

tts = TTS("supertonic-3")
vs = tts.get_voice_style("M2")
os.makedirs("F:/hermes/tts-supertonic/output", exist_ok=True)

# 1. Dark Documentary
print("Generating Variant 1: Dark Documentary...")
wav1, _ = tts.synthesize(script_text, voice_style=vs, speed=0.86, silence_duration=0.5, total_steps=16)
tts.save_audio(wav1, "F:/hermes/tts-supertonic/output/_v1_raw.wav")
fc1 = "acompressor=threshold=-20dB:ratio=3:attack=10:release=120:makeup=1.1,volume=0.95"
subprocess.run(['ffmpeg','-y','-i','F:/hermes/tts-supertonic/output/_v1_raw.wav','-af',fc1,'-ar','44100','F:/hermes/tts-supertonic/output/Narasi_1_Dark_Documentary.mp3'], check=True, capture_output=True)

# 2. Cinematic Mystery
print("Generating Variant 2: Cinematic Mystery...")
wav2, _ = tts.synthesize(script_text, voice_style=vs, speed=0.82, silence_duration=0.7, total_steps=16)
tts.save_audio(wav2, "F:/hermes/tts-supertonic/output/_v2_raw.wav")
# Subtle EQ enhancement for cinematic warmth + compression
fc2 = "equalizer=f=120:t=q:w=1:g=2.5,acompressor=threshold=-22dB:ratio=4:attack=8:release=100:makeup=1.2,volume=0.95"
subprocess.run(['ffmpeg','-y','-i','F:/hermes/tts-supertonic/output/_v2_raw.wav','-af',fc2,'-ar','44100','F:/hermes/tts-supertonic/output/Narasi_2_Cinematic_Mystery.mp3'], check=True, capture_output=True)

# 3. Horror Thriller
print("Generating Variant 3: Horror Thriller...")
wav3, _ = tts.synthesize(script_text, voice_style=vs, speed=0.79, silence_duration=0.9, total_steps=16)
tts.save_audio(wav3, "F:/hermes/tts-supertonic/output/_v3_raw.wav")
# Closer presence, deeper compression and slight high cut for tension
fc3 = "equalizer=f=100:t=q:w=1:g=3.0,equalizer=f=6000:t=q:w=1:g=-3.0,acompressor=threshold=-24dB:ratio=4.5:attack=5:release=80:makeup=1.3,volume=0.95"
subprocess.run(['ffmpeg','-y','-i','F:/hermes/tts-supertonic/output/_v3_raw.wav','-af',fc3,'-ar','44100','F:/hermes/tts-supertonic/output/Narasi_3_Horror_Thriller.mp3'], check=True, capture_output=True)

print("All 3 variations generated successfully!")
