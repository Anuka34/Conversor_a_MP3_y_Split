#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Conversor M4A a MP3 con división automática
VERSIÓN OPTIMIZADA MULTIPLATAFORMA (Windows/Linux/Mac)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import threading
import json
import math
import time
import re
import os
import platform
from pathlib import Path
from datetime import datetime

class AudioConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎶 Conversor M4A → MP3 - ¡A toda máquina! 🚀")
        self.root.geometry("850x850")
        self.root.resizable(True, True)
        
        # --- CONFIGURACIÓN DE ENTORNO ---
        self.os_name = platform.system()
        
        # Selección de fuente según sistema operativo
        if self.os_name == "Windows":
            self.main_font = 'Segoe UI'
        elif self.os_name == "Darwin": # macOS
            self.main_font = 'Helvetica'
        else: # Linux
            self.main_font = 'Liberation Sans'
            
        # --------------------------------

        # Variables
        self.input_file = None
        self.output_dir = None
        self.chunk_duration = 600  # 10 minutos en segundos
        self.total_duration = 0
        self.current_progress = 0
        self.current_time = 0
        self.start_time = None
        self.is_processing = False
        
        self.setup_ui()
        
        # Verificar dependencias completas
        if not self.check_dependencies():
            msg = "FFmpeg o FFprobe no están instalados o no se encuentran en el PATH.\n\n"
            if self.os_name == "Windows":
                msg += "Descárgalos de ffmpeg.org y añádelos a tus variables de entorno."
            else:
                msg += "Instálalo con: sudo apt-get install ffmpeg"
                
            messagebox.showerror("Error Crítico de Dependencias", msg)
            self.root.quit()
    
    def check_dependencies(self):
        """Verifica que ffmpeg y ffprobe estén instalados."""
        try:
            # Check ffmpeg
            subprocess.run(['ffmpeg', '-version'], 
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL,
                          check=True,
                          creationflags=subprocess.CREATE_NO_WINDOW if self.os_name == "Windows" else 0)
            
            # Check ffprobe (NUEVO: Verificación añadida)
            subprocess.run(['ffprobe', '-version'], 
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL,
                          check=True,
                          creationflags=subprocess.CREATE_NO_WINDOW if self.os_name == "Windows" else 0)
            return True
        except:
            return False
    
    def setup_ui(self):
        """Configura la interfaz optimizada."""
        # Marco principal con scroll
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # TÍTULO
        title_label = ttk.Label(main_frame, 
                                text="⚡🎧 CONVERSOR M4A → MP3 🎵🎼🎶", 
                                font=(self.main_font, 20, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=15)
        
        # SUBTÍTULO
        subtitle = ttk.Label(main_frame,
                            text="Convierte y divide en fragmentos de 10 minutos",
                            font=(self.main_font, 14))
        subtitle.grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
        # SELECCIÓN DE ARCHIVO
        file_frame = ttk.LabelFrame(main_frame, text="📂 Archivo de entrada", padding="10")
        file_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        file_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="Archivo:", font=(self.main_font, 12)).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.input_entry = ttk.Entry(file_frame, width=60)
        self.input_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        ttk.Button(file_frame, text="Seleccionar...", 
                  command=self.select_input_file).grid(row=0, column=2, padx=5)
        
        # DIRECTORIO DE SALIDA
        output_frame = ttk.LabelFrame(main_frame, text="📂 Directorio de salida", padding="10")
        output_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        output_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="Carpeta:", font=(self.main_font, 12)).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.output_entry = ttk.Entry(output_frame, width=60)
        self.output_entry.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        ttk.Button(output_frame, text="Cambiar...", 
                  command=self.select_output_dir).grid(row=0, column=2, padx=5)
        
        # INFORMACIÓN DEL ARCHIVO
        self.info_frame = ttk.LabelFrame(main_frame, text="🔎 Información del archivo", padding="10")
        self.info_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.info_text = tk.Text(self.info_frame, height=5, width=80, 
                                 font=(self.main_font, 10), state='disabled')
        self.info_text.grid(row=0, column=0, padx=5, pady=5)
        
        # PROGRESO
        progress_frame = ttk.LabelFrame(main_frame, text="📊 Progreso de conversión", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', 
                                           length=800, maximum=100)
        self.progress_bar.grid(row=0, column=0, columnspan=3, pady=5)
        
        # Labels de progreso
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=1, column=0, columnspan=3, pady=5)
        
        self.percentage_label = ttk.Label(stats_frame, text="0%", 
                                         font=(self.main_font, 18, 'bold'))
        self.percentage_label.grid(row=0, column=0, padx=20)
        
        self.time_label = ttk.Label(stats_frame, text="Tiempo: 00:00", font=(self.main_font, 12))
        self.time_label.grid(row=0, column=1, padx=20)
        
        self.speed_label = ttk.Label(stats_frame, text="Velocidad: --", font=(self.main_font, 12))
        self.speed_label.grid(row=0, column=2, padx=20)
        
        self.eta_label = ttk.Label(stats_frame, text="ETA: --:--", font=(self.main_font, 12))
        self.eta_label.grid(row=0, column=3, padx=20)
        
        self.status_label = ttk.Label(progress_frame, text="Listo para comenzar",
                                     foreground="green", font=(self.main_font, 12))
        self.status_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        # CONSOLA DE LOGS
        log_frame = ttk.LabelFrame(main_frame, text="📝 Registro de actividad", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.grid_rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, width=85, 
                                                  font=(self.main_font, 9), wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # BOTONES
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=15)
        
        self.convert_button = ttk.Button(button_frame, text="🚀 INICIAR CONVERSIÓN", 
                                        command=self.start_conversion,
                                        state='disabled')
        self.convert_button.grid(row=0, column=0, padx=5, ipadx=20, ipady=4)
        
        self.stop_button = ttk.Button(button_frame, text="⏹️ DETENER", 
                                     command=self.stop_conversion,
                                     state='disabled')
        self.stop_button.grid(row=0, column=1, padx=5, ipadx=20, ipady=4)
        
        self.open_button = ttk.Button(button_frame, text="📂 ABRIR CARPETA", 
                                     command=self.open_output_folder,
                                     state='disabled')
        self.open_button.grid(row=0, column=2, padx=5, ipadx=20, ipady=4)
        
        ttk.Button(button_frame, text="🗑️ LIMPIAR", 
                  command=self.clear_logs).grid(row=0, column=3, padx=5, ipadx=15, ipady=4)
        
        ttk.Button(button_frame, text="❌ SALIR", 
                  command=self.root.quit).grid(row=0, column=4, padx=5, ipadx=15, ipady=4)
    
    def log(self, message):
        """Añade mensaje a la consola con timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_logs(self):
        """Limpia la consola."""
        self.log_text.delete("1.0", tk.END)
    
    def select_input_file(self):
        """Selecciona archivo de entrada."""
        filetypes = [
            ("Archivos M4A", "*.m4a"),
            ("Archivos de audio", "*.m4a *.mp3 *.wav *.flac"),
            ("Todos los archivos", "*.*")
        ]
        
        initial_dir = str(Path.home() / "Desktop") if self.os_name == "Windows" else str(Path.home() / "Escritorio")
        
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            initialdir=initial_dir,
            filetypes=filetypes
        )
        
        if file_path:
            self.input_file = Path(file_path)
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, str(self.input_file))
            
            # Actualizar info y habilitar botón
            self.update_file_info()
            self.convert_button.configure(state='normal')
            
            # Establecer directorio de salida por defecto
            if not self.output_entry.get():
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, str(self.input_file.parent))
    
    def select_output_dir(self):
        """Selecciona directorio de salida."""
        initial_dir = str(Path.home() / "Desktop") if self.os_name == "Windows" else str(Path.home() / "Escritorio")
        dir_path = filedialog.askdirectory(
            title="Seleccionar carpeta de salida",
            initialdir=initial_dir
        )
        
        if dir_path:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, dir_path)
    
    def get_audio_info(self):
        """Obtiene información del audio usando ffprobe."""
        cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'format=duration,size,bit_rate',
            '-of', 'json',
            str(self.input_file)
        ]
        
        try:
            # Flags para ocultar ventana en Windows
            creation_flags = subprocess.CREATE_NO_WINDOW if self.os_name == "Windows" else 0
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  check=True, timeout=5, creationflags=creation_flags)
            data = json.loads(result.stdout)
            
            return {
                "duration": float(data["format"]["duration"]),
                "size": int(data["format"]["size"]),
                "bitrate": int(data["format"]["bit_rate"]),
                "size_mb": int(data["format"]["size"]) / (1024 * 1024)
            }
        except Exception as e:
            self.log(f"❌ Error obteniendo info con FFprobe: {e}")
            return None
    
    def update_file_info(self):
        """Actualiza información del archivo."""
        if not self.input_file or not self.input_file.exists():
            return
        
        info = self.get_audio_info()
        if not info:
            return
        
        duration = info["duration"]
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        chunks = math.ceil(duration / 600)
        
        info_text = f"""Archivo: {self.input_file.name}
Duración: {hours:02d}:{minutes:02d}:{seconds:02d} ({duration:.0f} segundos)
Tamaño: {info['size_mb']:.1f} MB
Fragmentos: {chunks} archivos de 10 minutos
Bitrate detectado: {info['bitrate'] // 1000} kbps"""
        
        self.info_text.configure(state='normal')
        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", info_text)
        self.info_text.configure(state='disabled')
        
        self.total_duration = duration
    
    def start_conversion(self):
        """Inicia conversión."""
        if not self.input_file or not self.input_file.exists():
            messagebox.showerror("Error", "Selecciona un archivo válido.")
            return
        
        output_dir = Path(self.output_entry.get())
        if not output_dir:
            output_dir = self.input_file.parent
        
        output_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir = output_dir
        
        self.convert_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        self.open_button.configure(state='disabled')
        
        self.current_progress = 0
        self.current_time = 0
        self.start_time = time.time()
        self.is_processing = True
        
        self.clear_logs()
        self.log("=" * 70)
        self.log("🚀 INICIANDO CONVERSIÓN TURBO")
        self.log(f"📄 Archivo: {self.input_file.name}")
        self.log(f"📂 Salida: {self.output_dir}")
        self.log("=" * 70)
        
        thread = threading.Thread(target=self.run_conversion, daemon=True)
        thread.start()
        
        self.update_timer()
    
    def run_conversion(self):
        """Ejecuta conversión con configuración OPTIMIZADA."""
        try:
            base_name = self.input_file.stem.replace('"', '').replace("'", "")
            output_pattern = str(self.output_dir / f"%03d_{base_name}.mp3")
            
            # --- CORRECCIÓN 1: ELIMINACIÓN DE CONFLICTO Y OPTIMIZACIÓN ---
            # Se ha eliminado "-b:a 192k". 
            # Se usa solo "-q:a 2" (VBR estándar ~190kbps) para máxima velocidad.
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "info",
                "-i", str(self.input_file),
                "-vn",
                "-map", "0:a",
                "-acodec", "libmp3lame",
                # "-b:a", "192k",  <-- ELIMINADO PARA EVITAR CONFLICTO Y GANAR VELOCIDAD
                "-q:a", "2",     # Calidad VBR (0=mejor, 9=peor, 2=estándar alto)
                "-threads", "0",
                "-f", "segment",
                "-segment_time", str(self.chunk_duration),
                "-segment_format", "mp3",
                "-reset_timestamps", "1",
                "-progress", "pipe:1",
                "-nostats",
                "-y",
                output_pattern
            ]
            
            creation_flags = subprocess.CREATE_NO_WINDOW if self.os_name == "Windows" else 0
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=creation_flags
            )
            
            time_pattern = re.compile(r"out_time_ms=(\d+)")
            
            while process.poll() is None and self.is_processing:
                line = process.stdout.readline()
                if not line:
                    time.sleep(0.05)
                    continue
                
                line = line.strip()
                
                time_match = time_pattern.search(line)
                if time_match:
                    try:
                        out_time_ms = int(time_match.group(1))
                        self.current_time = out_time_ms / 1000000.0
                        
                        if self.total_duration > 0:
                            self.current_progress = min(1.0, self.current_time / self.total_duration)
                            self.root.after(0, self.update_progress_ui, self.current_progress)
                    except:
                        pass
                
                if "error" in line.lower():
                    self.root.after(0, self.log, f"ERROR: {line}")
            
            return_code = process.wait(timeout=30)
            
            if return_code == 0:
                elapsed = time.time() - self.start_time
                self.root.after(0, self.conversion_complete, 
                              f"Conversión completada en {elapsed:.1f}s")
            else:
                self.root.after(0, self.conversion_error, 
                              f"FFmpeg terminó con código {return_code}")
                
        except Exception as e:
            self.root.after(0, self.conversion_error, str(e))
    
    def update_progress_ui(self, progress):
        self.progress_bar['value'] = progress * 100
        self.percentage_label.config(text=f"{progress*100:.0f}%")
        self.status_label.config(text=f"Procesando... {progress*100:.0f}%")
    
    def update_timer(self):
        if not self.is_processing:
            return
        
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        self.time_label.config(text=f"Tiempo: {minutes:02d}:{seconds:02d}")
        
        if elapsed > 0 and self.current_time > 0:
            speed = self.current_time / elapsed
            self.speed_label.config(text=f"Velocidad: {speed:.1f}x")
            
            if self.current_progress > 0 and self.current_progress < 1:
                remaining = (1 - self.current_progress) * elapsed / self.current_progress
                eta_min = int(remaining // 60)
                eta_sec = int(remaining % 60)
                self.eta_label.config(text=f"ETA: {eta_min:02d}:{eta_sec:02d}")
        
        if self.is_processing:
            self.root.after(1000, self.update_timer)
    
    def stop_conversion(self):
        self.is_processing = False
        self.stop_button.configure(state='disabled')
        self.status_label.config(text="⏹️ Deteniendo...")
        self.log("Solicitud de detención enviada...")
    
    def conversion_complete(self, message):
        self.is_processing = False
        self.progress_bar['value'] = 100
        self.percentage_label.config(text="100%")
        self.status_label.config(text="✅ Conversión completada", foreground="green")
        
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        self.time_label.config(text=f"Tiempo total: {minutes:02d}:{seconds:02d}")
        
        self.convert_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.open_button.configure(state='normal')
        
        self.log("=" * 70)
        self.log(f"COMPLETADO: {message}")
        
        try:
            mp3_files = list(self.output_dir.glob(f"*_{self.input_file.stem}.mp3"))
            mp3_files.sort()
            self.log(f"Archivos creados: {len(mp3_files)}")
            for i, f in enumerate(mp3_files[:5], 1):
                size_mb = f.stat().st_size / (1024 * 1024)
                self.log(f"  {i:03d}. {f.name} ({size_mb:.1f} MB)")
        except Exception as e:
            self.log(f"Info: {e}")
        
        messagebox.showinfo("Éxito", f"¡Listo!\n{message}\nCarpeta: {self.output_dir}")
    
    def conversion_error(self, error_msg):
        self.is_processing = False
        self.status_label.config(text="❌ Error", foreground="red")
        self.convert_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.log(f"❌ ERROR: {error_msg}")
        messagebox.showerror("Error", f"Fallo en conversión:\n{error_msg}")
    
    def open_output_folder(self):
        """Abre carpeta de salida (COMPATIBLE WINDOWS/LINUX/MAC)."""
        if self.output_dir and self.output_dir.exists():
            try:
                # --- CORRECCIÓN 3: COMPATIBILIDAD MULTIPLATAFORMA ---
                if self.os_name == "Windows":
                    os.startfile(self.output_dir)
                elif self.os_name == "Darwin": # macOS
                    subprocess.run(["open", str(self.output_dir)])
                else: # Linux
                    subprocess.run(["xdg-open", str(self.output_dir)])
            except Exception as e:
                self.log(f"❌ Error abriendo carpeta: {e}")

def main():
    root = tk.Tk()
    app = AudioConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
