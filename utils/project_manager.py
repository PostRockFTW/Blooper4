# Blooper4/utils/project_manager.py
import json
import tkinter as tk
from tkinter import filedialog
import pygame
from models import Song

class ProjectManager:
    """Handles all File I/O and reconstruction logic for Blooper 4.0."""
    
    @staticmethod
    def save(song):
        root = tk.Tk(); root.withdraw()
        path = filedialog.asksaveasfilename(
            defaultextension=".bloop", 
            filetypes=[("Blooper Project", "*.bloop")]
        )
        root.destroy()
        # Flush the 'Selection Click' so it doesn't hit the Editor
        pygame.event.clear()
        
        if path:
            try:
                with open(path, 'w') as f:
                    json.dump(song.to_dict(), f, indent=4)
                song.file_path = path
                print(f"Project Saved: {path}")
                return True
            except Exception as e:
                print(f"Save Error: {e}")
        return False

    @staticmethod
    def load():
        root = tk.Tk(); root.withdraw()
        path = filedialog.askopenfilename(
            filetypes=[("Blooper Project", "*.bloop")]
        )
        root.destroy()
        pygame.event.clear()
        
        if path:
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                new_song = Song()
                new_song.from_dict(data)
                print(f"Project Loaded: {path}")
                return new_song
            except Exception as e:
                print(f"Load Error: {e}")
        return None