import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import scrolledtext, messagebox, filedialog
import threading
import subprocess
import os
import re
import time
import shutil
from pathlib import Path
import math

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Supertonic-3: NIGHTMARE SIDE ENGINE v2.0")
        self.root.geometry("1000x850")
        self.style = tb.Style("superhero")
        
        # Default Params (Based on Ardan Radio Analysis)
        self.default_voice = "M2"
        self.default_rate = 0.80
        self.default_pitch = -1.5
        self.default_bass = 4.0
        self.default_compress = 70
        self.default_pause = 2.5 # Detik hening per '...'
        
        from supertonic import TTS
        self.tts = TTS("supertonic-3")
        self.voice_style = self.tts.get_voice_style(self.default_voice)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Notebook untuk Tab
        self.nb = tb.Notebook(self.root, bootstyle="info")
        self.nb.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Tab 1: Generate
        self.tab1 = tb.Frame(self.nb)
        self.nb.add(self.tab1, text=" 🎙️ Generate Narasi ")
        self.setup_tab1()
        
        # Tab 2: Batch
        self.tab2 = tb.Frame(self.nb)
        self.nb.add(self.tab2, text=" 📁 Batch Processing ")
        self.setup_tab2()

    def setup_tab1(self):
        # Title Input
        header_frame = tb.Frame(self.tab1)
        header_frame.pack(fill=X, padx=20, pady=10)
        
        tb.Label(header_frame, text="Judul Video:", font=("Helvetica", 11, "bold")).pack(side=LEFT)
        self.title_entry = tb.Entry(header_frame, width=50)
        self.title_entry.pack(side=LEFT, padx=10)
        self.title_entry.insert(0, "Misteri_Video_Baru")

        # Text Input Area
        tb.Label(self.tab1, text="Naskah Narasi (Gunakan '...' untuk jeda panjang):", font=("Helvetica", 10)).pack(anchor=W, padx=20)
        self.text_area = scrolledtext.ScrolledText(self.tab1, height=12, font=("Montserrat", 11))
        self.text_area.pack(fill=BOTH, padx=20, pady=5)
        
        # Auto Format Button
        btn_frame = tb.Frame(self.tab1)
        btn_frame.pack(fill=X, padx=20, pady=5)
        
        tb.Button(btn_frame, text="✨ Auto-Format: Nightmare Side Style", bootstyle="warning-outline", 
                  command=self.auto_format_text).pack(side=LEFT)
        
        # Controls Frame
        ctrl_frame = tb.Frame(self.tab1)
        ctrl_frame.pack(fill=X, padx=20, pady=10)
        
        # Left Side: Audio Settings
        audio_frame = tb.LabelFrame(ctrl_frame, text=" Pengaturan Audio (Nightmare Side Standard) ", padding=15)
        audio_frame.pack(side=LEFT, fill=BOTH, expand=YES, marginRight=10)
        
        # Voice Select
        tb.Label(audio_frame, text="Suara:").grid(row=0, column=0, sticky=W)
        self.voice_var = tb.StringVar(value=self.default_voice)
        voices = ["M1", "M2", "M3", "M4", "M5", "F1", "F2", "F3", "F4", "F5"]
        vc = tb.Combobox(audio_frame, textvariable=self.voice_var, values=voices, width=10)
        vc.grid(row=0, column=1, sticky=W, pady=5)
        vc.bind('<<ComboboxSelected>>', lambda e: setattr(self, 'voice_style', self.tts.get_voice_style(self.voice_var.get())))
        
        # Speed
        tb.Label(audio_frame, text="Tempo (Speed):").grid(row=1, column=0, sticky=W)
        self.speed_scale = tb.Scale(audio_frame, from_=0.5, to=1.5, value=self.default_rate, bootstyle="info")
        self.speed_scale.grid(row=1, column=1, sticky=EW, padx=5)
        
        # Pitch
        tb.Label(audio_frame, text="Nada (Pitch):").grid(row=2, column=0, sticky=W)
        self.pitch_scale = tb.Scale(audio_frame, from_=-5.0, to=5.0, value=self.default_pitch, bootstyle="danger")
        self.pitch_scale.grid(row=2, column=1, sticky=EW, padx=5)

        # Right Side: Effects
        fx_frame = tb.LabelFrame(ctrl_frame, text=" Efek Suara (Close-Mic FX) ", padding=15)
        fx_frame.pack(side=LEFT, fill=BOTH, expand=YES)
        
        # Bass
        tb.Label(fx_frame, text="Bass Boost (Deep):").grid(row=0, column=0, sticky=W)
        self.bass_scale = tb.Scale(fx_frame, from_=0, to=10, value=self.default_bass, bootstyle="success")
        self.bass_scale.grid(row=0, column=1, sticky=EW, padx=5)
        
        # Compression
        tb.Label(fx_frame, text="Kompresi (Vocal):").grid(row=1, column=0, sticky=W)
        self.comp_scale = tb.Scale(fx_frame, from_=0, to=100, value=self.default_compress, bootstyle="primary")
        self.comp_scale.grid(row=1, column=1, sticky=EW, padx=5)
        
        # Pause Duration
        tb.Label(fx_frame, text="Jeda '...' (Detik):").grid(row=2, column=0, sticky=W)
        self.pause_scale = tb.Scale(fx_frame, from_=0.5, to=5.0, value=self.default_pause, bootstyle="warning")
        self.pause_scale.grid(row=2, column=1, sticky=EW, padx=5)

        # Output Folder
        out_frame = tb.Frame(self.tab1)
        out_frame.pack(fill=X, padx=20, pady=10)
        tb.Label(out_frame, text="Folder Output:").pack(side=LEFT)
        self.out_path = tb.Entry(out_frame, width=60)
        self.out_path.pack(side=LEFT, padx=10)
        self.out_path.insert(0, "F:/hermes/tts-supertonic/output")
        tb.Button(out_frame, text="Browse", command=self.browse_output).pack(side=LEFT)

        # Generate Button
        self.gen_btn = tb.Button(self.tab1, text="🎵 GENERATE AUDIO (NIGHTMARE SIDE MODE)", 
                                bootstyle="success", width=50, command=self.start_generate)
        self.gen_btn.pack(pady=20)
        
        # Progress
        self.progress = tb.Progressbar(self.tab1, mode='determinate', bootstyle="success-striped")
        self.progress.pack(fill=X, padx=20, pady=5)
        self.status_lbl = tb.Label(self.tab1, text="Ready.")
        self.status_lbl.pack()

    def setup_tab2(self):
        # Similar to Tab 1 but for folder selection
        tb.Label(self.tab2, text="Pilih Folder berisi file .txt naskah:", font=("Helvetica", 10)).pack(anchor=W, padx=20, pady=10)
        batch_input_frame = tb.Frame(self.tab2)
        batch_input_frame.pack(fill=X, padx=20)
        
        self.batch_input_path = tb.Entry(batch_input_frame, width=70)
        self.batch_input_path.pack(side=LEFT, padx=5)
        tb.Button(batch_input_frame, text="Pilih Folder", command=self.browse_batch_input).pack(side=LEFT)
        
        self.batch_btn = tb.Button(self.tab2, text="🚀 JALANKAN BATCH GENERATE (60 VIDEO TARGET)", 
                                   bootstyle="info", width=50, command=self.start_batch)
        self.batch_btn.pack(pady=30)
        
        self.batch_log = scrolledtext.ScrolledText(self.tab2, height=15, font=("Consolas", 9))
        self.batch_log.pack(fill=BOTH, padx=20, pady=10)

    # Logic functions
    def auto_format_text(self):
        text = self.text_area.get("1.0", END).strip()
        if not text: return
        
        # 1. Nightmare Side Preprocessing
        # Ganti tanda baca jadi jeda panjang
        text = re.sub(r'([,.?!])', r'\1...', text)
        text = re.sub(r'\.\.\.\.\.\.', r'...', text) # Clean up
        
        # 2. Elongasi vokal klimaks (simple logic)
        vowels = "aeiou"
        words = text.split()
        new_words = []
        for i, w in enumerate(words):
            # Cek kata terakhir sebelum jeda atau kata panjang
            if len(w) > 5 and i % 7 == 0 and any(v in w[-2:].lower() for v in vowels):
                w = w[:-1] + w[-1]*3 + "..."
            new_words.append(w)
        
        formatted = " ".join(new_words)
        self.text_area.delete("1.0", END)
        self.text_area.insert("1.0", formatted)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.out_path.delete(0, END)
            self.out_path.insert(0, path)

    def browse_batch_input(self):
        path = filedialog.askdirectory()
        if path:
            self.batch_input_path.delete(0, END)
            self.batch_input_path.insert(0, path)

    def start_generate(self):
        threading.Thread(target=self.generate_worker, daemon=True).start()

    def generate_worker(self):
        title = self.title_entry.get().strip()
        text = self.text_area.get("1.0", END).strip()
        out_dir = self.out_path.get().strip()
        
        if not title or not text:
            messagebox.showerror("Error", "Isi Judul dan Naskah dulu bos!")
            return

        self.gen_btn.config(state=DISABLED)
        self.status_lbl.config(text="Memproses naskah per frasa...")
        
        try:
            # 1. Split text into segments by ...
            segments = [s.strip() for s in text.split('...') if s.strip()]
            os.makedirs(out_dir, exist_ok=True)
            tmp_dir = "F:/hermes/tts-supertonic/_emo_tmp"
            if os.path.exists(tmp_dir): shutil.rmtree(tmp_dir)
            os.makedirs(tmp_dir)
            
            final_files = []
            pause_sec = float(self.pause_scale.get())
            
            for i, seg in enumerate(segments):
                self.status_lbl.config(text=f"Generating frasa {i+1}/{len(segments)}...")
                self.progress['value'] = (i / len(segments)) * 100
                
                # Dynamic variations per segment
                is_last = (i == len(segments)-1)
                seg_rate = float(self.speed_scale.get()) * (0.92 if is_last else 1.0)
                seg_pitch = float(self.pitch_scale.get()) + (-0.5 if is_last else 0.0)
                
                raw_wav = f"{tmp_dir}/seg_{i}.wav"
                proc_wav = f"{tmp_dir}/seg_{i}_proc.wav"
                
                # Supertonic-3 API
                wav, sr = self.tts.synthesize(seg, voice_style=self.voice_style, speed=seg_rate, lang="id")
                self.tts.save_audio(wav, raw_wav)
                
                # Apply FFmpeg Effects (Bass, Compression, Pitch)
                bass = self.bass_scale.get()
                comp = self.comp_scale.get() / 100.0
                
                filter_chain = f"rubberband=pitch={2**(seg_pitch/12.0)},equalizer=f=150:t=q:w=1:g={bass},acompressor=threshold=-20dB:ratio=4:attack=5:release=50:makeup={1.0+comp},asoftclip=type=atan"
                subprocess.run(['ffmpeg', '-y', '-i', raw_wav, '-af', filter_chain, proc_wav], check=True, capture_output=True)
                
                final_files.append(proc_wav)
                # Add silence segment
                silence_wav = f"{tmp_dir}/silence_{i}.wav"
                subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', f'anullsrc=r=22050:cl=mono', '-t', str(pause_sec), silence_wav], check=True, capture_output=True)
                final_files.append(silence_wav)

            # Combine all
            self.status_lbl.config(text="Menggabungkan audio & menambahkan ambience...")
            concat_list = f"{tmp_dir}/list.txt"
            with open(concat_list, "w") as f:
                for f_path in final_files:
                    f.write(f"file '{os.path.abspath(f_path)}'\n")
            
            output_file = f"{out_dir}/{title}.mp3"
            subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_list, '-c:a', 'libmp3lame', '-q:a', '2', output_file], check=True, capture_output=True)
            
            self.status_lbl.config(text=f"BERHASIL! File: {title}.mp3")
            messagebox.showinfo("Sukses", f"Audio horor selesai!\nLokasi: {output_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Gagal generate: {str(e)}")
        finally:
            self.gen_btn.config(state=NORMAL)
            self.progress['value'] = 0

    def start_batch(self):
        # Placeholder logic for batch
        messagebox.showinfo("Batch", "Mode Batch 60 Video Siap!")

    def start_app(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tb.Window(themename="superhero")
    app = TTSApp(root)
    root.mainloop()
