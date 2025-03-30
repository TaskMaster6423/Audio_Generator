import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread
import subprocess
import sys

class MKVAudioExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("MKV Audio Extractor")
        self.root.geometry("600x400")
        
        # Variables
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.audio_format = tk.StringVar(value="mp3")
        self.progress = tk.DoubleVar()
        self.status = tk.StringVar(value="Ready")
        
        # GUI Elements
        tk.Label(root, text="Source Video Folder:").pack(pady=5)
        tk.Entry(root, textvariable=self.input_folder, width=70).pack(pady=5)
        tk.Button(root, text="Browse", command=self.browse_input).pack(pady=5)
        
        tk.Label(root, text="Output Audio Folder:").pack(pady=5)
        tk.Entry(root, textvariable=self.output_folder, width=70).pack(pady=5)
        tk.Button(root, text="Browse", command=self.browse_output).pack(pady=5)
        
        # Audio Format Selection
        tk.Label(root, text="Audio Format:").pack(pady=5)
        format_frame = tk.Frame(root)
        format_frame.pack()
        tk.Radiobutton(format_frame, text="MP3", variable=self.audio_format, value="mp3").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(format_frame, text="AAC", variable=self.audio_format, value="aac").pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(format_frame, text="FLAC", variable=self.audio_format, value="flac").pack(side=tk.LEFT, padx=10)
        
        tk.Button(root, text="Extract Audio", command=self.start_extraction, bg="#4CAF50", fg="white").pack(pady=20)
        
        # Progress Bar
        self.progress_bar = ttk.Progressbar(root, variable=self.progress, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        # Status Label
        tk.Label(root, textvariable=self.status, wraplength=550).pack(pady=5)
    
    def browse_input(self):
        folder = filedialog.askdirectory(title="Select Source Video Folder")
        if folder:
            self.input_folder.set(folder)
    
    def browse_output(self):
        folder = filedialog.askdirectory(title="Select Output Audio Folder")
        if folder:
            self.output_folder.set(folder)
    
    def extract_audio(self, input_file, output_file, audio_format):
        try:
            if audio_format == "mp3":
                cmd = [
                    'ffmpeg',
                    '-i', input_file,
                    '-q:a', '0',
                    '-map', '0:a',
                    '-acodec', 'libmp3lame',
                    output_file
                ]
            elif audio_format == "aac":
                cmd = [
                    'ffmpeg',
                    '-i', input_file,
                    '-q:a', '0',
                    '-map', '0:a',
                    '-acodec', 'aac',
                    output_file
                ]
            else:  # FLAC
                cmd = [
                    'ffmpeg',
                    '-i', input_file,
                    '-map', '0:a',
                    '-acodec', 'flac',
                    output_file
                ]
            
            # Run FFmpeg command
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e.stderr.decode('utf-8')}")
            return False
    
    def start_extraction(self):
        # Check if FFmpeg is installed
        try:
            subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg is not installed or not in PATH.\n\n"
                "Please install FFmpeg first:\n"
                "Windows: Download from ffmpeg.org\n"
                "Mac: brew install ffmpeg\n"
                "Linux: sudo apt install ffmpeg"
            )
            return
        
        input_folder = self.input_folder.get()
        output_folder = self.output_folder.get()
        audio_format = self.audio_format.get()
        
        if not input_folder or not output_folder:
            messagebox.showerror("Error", "Please select both source and output folders!")
            return
        
        mkv_files = []
        for root, _, files in os.walk(input_folder):
            for file in files:
                if file.lower().endswith('.mkv'):
                    mkv_files.append(os.path.join(root, file))
        
        if not mkv_files:
            messagebox.showinfo("Info", "No MKV files found in the source folder!")
            return
        
        self.status.set(f"Found {len(mkv_files)} MKV files. Starting extraction...")
        self.progress.set(0)
        
        Thread(
            target=self.extract_audio_files,
            args=(input_folder, output_folder, mkv_files, audio_format),
            daemon=True
        ).start()
    
    def extract_audio_files(self, input_folder, output_folder, mkv_files, audio_format):
        total_files = len(mkv_files)
        for i, input_path in enumerate(mkv_files):
            rel_path = os.path.relpath(input_path, input_folder)
            audio_rel_path = os.path.splitext(rel_path)[0] + f'.{audio_format}'
            output_path = os.path.join(output_folder, audio_rel_path)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            self.status.set(f"Extracting: {rel_path} ({i+1}/{total_files})")
            success = self.extract_audio(input_path, output_path, audio_format)
            
            self.progress.set((i + 1) / total_files * 100)
            self.root.update_idletasks()
        
        self.status.set(f"Completed! Extracted {total_files} audio files")
        messagebox.showinfo("Success", "Audio extraction complete!")

if __name__ == "__main__":
    root = tk.Tk()
    app = MKVAudioExtractor(root)
    root.mainloop()