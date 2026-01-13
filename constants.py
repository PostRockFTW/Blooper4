# Blooper4/constants.py
import pygame

# --- VERSION ---
VERSION = "4.0.0"

# --- GLOBAL UI STATE & SCALING ---
UI_SCALE = 1.0

# Every BaseUIElement automatically adds itself to this list on creation.
# This allows main.py to broadcast events (like MouseUp) to every component
# regardless of which 'View' is currently active.
ACTIVE_COMPONENTS = []

def scale(val):
    """Universal helper to adjust logical pixels to current UI_SCALE."""
    return int(val * UI_SCALE)

# --- AUDIO STANDARDS ---
SAMPLE_RATE = 44100
BUFFER_SIZE = 512       # Low latency buffer
TPQN = 480              # Ticks Per Quarter Note
NUM_TRACKS = 16

# --- MIDI DRUM RANGE ---
MIDI_RANGE = 128
DRUM_NOTE_START = 34
DRUM_NOTE_END = 52

# --- BASE DIMENSIONS (Logical Pixels) ---
# These are the 'Stock' sizes. We multiply these by UI_SCALE in the containers.
WINDOW_W = 1280
WINDOW_H = 800

HEADER_H = 60
MIXER_H = 250
# Main View is the area between the header and the mixer
MAIN_VIEW_H = WINDOW_H - HEADER_H - MIXER_H 

EDITOR_SIDEBAR_W = 70
GRID_HEIGHT = 20 # Logical height of one MIDI note row
MODULE_W = 300    # Standard width for Builder plugins

# --- COLORS (PRO DAW THEME) ---
COLOR_BG = (10, 10, 12)
COLOR_PANEL = (25, 25, 30)
COLOR_ACCENT = (0, 255, 128) # Teal-Green highlight
WHITE = (240, 240, 240)
BLACK = (0, 0, 0)
GRAY = (60, 60, 65)
RED = (255, 50, 50)
GREEN = (0, 255, 100)
BLUE = (50, 150, 255)

# --- RAINBOW OCTAVES (Red=High, Violet=Low) ---
OCTAVE_COLORS = [
    (148, 0, 211), (75, 0, 130), (0, 0, 255), (0, 255, 0),
    (255, 255, 0), (255, 165, 0), (255, 69, 0), (255, 0, 0),
    (200, 0, 0), (150, 0, 0), (100, 0, 0)
]

# --- QUANTIZATION ---
QUANT_MAP = {
    "1/4": 480, "1/4T": 320, "1/8": 240, "1/8T": 160,
    "1/16": 120, "1/16T": 80, "1/32": 60, "1/64": 30
}
QUANT_LABELS = list(QUANT_MAP.keys())

# --- PERFORMANCE ---
FPS = 60

# --- SAMPLER / WORKSTATION SETTINGS ---
SAMPLER_DEFAULT_START = 33
SAMPLER_CHUNK_SIZE = 16