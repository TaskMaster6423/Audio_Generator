import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread
import subprocess
import sys
import platform

class MKVAudioExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("MKV Audio Extractor (GPU Accelerated)")
        self.root.geometry("650x450")
        
        # Variables
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.audio_format = tk.StringVar(value="mp3")
        self.use_gpu = tk.BooleanVar(value=True)
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
        
        # GPU Acceleration Option
        tk.Checkbutton(root, text="Enable GPU Acceleration (CUDA)", variable=self.use_gpu).pack(pady=10)
        
        tk.Button(root, text="Extract Audio", command=self.start_extraction, bg="#4CAF50", fg="white").pack(pady=20)
        
        # Progress Bar
        self.progress_bar = ttk.Progressbar(root, variable=self.progress, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        # Status Label
        tk.Label(root, textvariable=self.status, wraplength=600).pack(pady=5)
        
        # Check GPU support at startup
        self.gpu_supported = self.check_gpu_support()
        if not self.gpu_supported:
            self.use_gpu.set(False)
    
    def check_gpu_support(self):
        """Check if CUDA acceleration is available"""
        try:
            result = subprocess.run(['ffmpeg', '-hwaccels'], capture_output=True, text=True)
            if result.returncode == 0 and 'cuda' in result.stdout.lower():
                # Test CUDA actually works
                test_cmd = [
                    'ffmpeg',
                    '-hwaccel', 'cuda',
                    '-hwaccel_output_format', 'cuda',
                    '-i', 'none',  # This will fail but we want to see the error
                    '-f', 'null', '-'
                ]
                test_result = subprocess.run(test_cmd, capture_output=True, text=True)
                return 'cuda' in test_result.stderr.lower()
            return False
        except:
            return False
    
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
            # Base command
            cmd = ['ffmpeg', '-i', input_file]
            
            # Add GPU acceleration if enabled and supported
            if self.use_gpu.get() and self.gpu_supported:
                cmd.extend([
                    '-hwaccel', 'cuda',
                    '-hwaccel_output_format', 'cuda',
                    '-extra_hw_frames', '2'  # Helps with performance
                ])
            
            # Common parameters
            cmd.extend(['-map', '0:a'])
            
            # Format-specific parameters
            if audio_format == "mp3":
                cmd.extend(['-q:a', '0', '-acodec', 'libmp3lame'])
            elif audio_format == "aac":
                cmd.extend(['-q:a', '0', '-acodec', 'aac'])
            else:  # FLAC
                cmd.extend(['-acodec', 'flac'])
            
            # Output file
            cmd.append(output_file)
            
            # Run FFmpeg command
            result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Verify GPU was actually used if enabled
            if self.use_gpu.get() and self.gpu_supported:
                output = result.stderr.decode('utf-8').lower()
                if 'cuda' not in output:
                    print("Warning: GPU acceleration was enabled but may not have been used")
            
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode('utf-8')
            print(f"Error extracting audio: {error_msg}")
            
            # If GPU failed, try CPU fallback
            if self.use_gpu.get() and ('cuda' in error_msg.lower() or 'hwaccel' in error_msg.lower()):
                self.status.set("GPU acceleration failed, retrying with CPU...")
                self.root.update_idletasks()
                return self.extract_audio_with_cpu(input_file, output_file, audio_format)
            
            return False
    
    def extract_audio_with_cpu(self, input_file, output_file, audio_format):
        """Fallback method using CPU only"""
        try:
            if audio_format == "mp3":
                cmd = [
                    'ffmpeg',
                    '-i', input_file,
                    '-q:a', '0',
                    '-map', '0:a:0',
                    '-acodec', 'libmp3lame',
                    output_file
                ]
            elif audio_format == "aac":
                cmd = [
                    'ffmpeg',
                    '-i', input_file,
                    '-q:a', '0',
                    '-map', '0:a:0',
                    '-acodec', 'aac',
                    output_file
                ]
            else:  # FLAC
                cmd = [
                    'ffmpeg',
                    '-i', input_file,
                    '-map', '0:a:0',
                    '-acodec', 'flac',
                    output_file
                ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except subprocess.CalledProcessError as e:
            print(f"CPU fallback failed: {e.stderr.decode('utf-8')}")
            return False
    
    def start_extraction(self):
        # Check if FFmpeg is installed
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            ffmpeg_version = result.stdout.split('\n')[0]
            self.status.set(f"Using {ffmpeg_version}")
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
        success_count = 0
        
        for i, input_path in enumerate(mkv_files):
            rel_path = os.path.relpath(input_path, input_folder)
            audio_rel_path = os.path.splitext(rel_path)[0] + f'.{audio_format}'
            output_path = os.path.join(output_folder, audio_rel_path)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            self.status.set(f"Extracting: {rel_path} ({i+1}/{total_files})")
            success = self.extract_audio(input_path, output_path, audio_format)
            
            if success:
                success_count += 1
            
            self.progress.set((i + 1) / total_files * 100)
            self.root.update_idletasks()
        
        self.status.set(f"Completed! Successfully extracted {success_count} of {total_files} audio files")
        messagebox.showinfo("Success", f"Audio extraction complete!\n\nSuccessfully extracted {success_count} of {total_files} files.")

if __name__ == "__main__":
    root = tk.Tk()
    app = MKVAudioExtractor(root)
    root.mainloop()