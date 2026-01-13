# Project Source Code Context

## Project Structure
```text
./
    CLAUDE.md
    Claude_questions.md
    constants.py
    main.py
    models.py
    project_context.md
    project_to_md.py
    READ_ME.md
    requirements.txt
    ui_components.py
    .claude/
        agents/
            daw-code-architect.md
    audio_engine/
        base_processor.py
        bridge.py
        manager.py
        plugin_factory.py
        __init__.py
        src/
            synthesizer.cpp
    components/
        base_element.py
        drum_roll.py
        mixer_panel.py
        mixer_strip.py
        note_type_toolbar.py
        piano_roll.py
        __init__.py
        builder/
            mode_toggle.py
            piano_roll_settings.py
            sampler_brain.py
            __init__.py
        builder_plugins/
            dual_osc.py
            eq.py
            noise_drum.py
            reverb.py
            square_cymbal.py
            __init__.py
    containers/
        base_view.py
        builder_view.py
        editor_view.py
        main_menu.py
    Save_Files/
        metal drums NES.bloop
        testo.bloop
        testosterone.bloop
        testosterone2.bloop
    utils/
        project_manager.py
        requirements_check.py
```

---

## File: CLAUDE.md
```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Blooper 4.0 is a modular Digital Audio Workstation (DAW) built in Python with Pygame. It features a plugin-based architecture for audio synthesis and effects, MIDI sequencing, and a dual-mode track system (SYNTH vs SAMPLER).

## Development Commands

### Running the Application
```bash
python main.py
```

### Python Environment
- Python 3.12.7
- Dependencies: `pygame==2.6.1`, `numpy>=1.26.0`, `scipy>=1.11.0`
- Auto-installs missing packages via `utils/requirements_check.py` on startup

### Testing Audio Plugins
To test a new plugin without full DAW restart, the plugin factory uses `importlib.reload()` for hot-reloading during development.

## Core Architecture

### Signal Flow: Serial Pipeline
1. **Clock** (`main.py`): High-resolution tick counter triggers notes at precise timing
2. **AudioManager** (`audio_engine/manager.py`): Orchestrates 64-voice polyphony
3. **Source Generation**: Plugins generate raw audio buffer (C++ bridge or Python)
4. **FX Chain**: Serial processing through track effects list
5. **Mixer**: Applies volume/pan/mute/solo, converts to 16-bit stereo PCM
6. **Output**: Pygame mixer channels for playback

### Track Modes (4.1 Architecture)
- **SYNTH Mode**: Single source plugin (e.g., DUAL_OSC) for all notes on the track
- **SAMPLER Mode**: 128 independent engines, one per MIDI pitch (workstation/drum machine)

### Plugin Contract
All plugins in `components/builder_plugins/` must contain:

**class Processor(BaseProcessor)**:
- Sources: Implement `.generate_modular(params_dict, note_model, bpm)` → returns numpy float32 buffer
- Effects: Implement `.process(buffer, params_dict)` → returns modified buffer

**class UI(BaseUIElement)**:
- Must implement `.draw(screen, track_model, active, scale)`
- Must implement `.handle_event(event, track_model, scale)` → returns action string or None
- Must call `super().__init__(x, y, w, h)` to register with global event system

### UI Scaling System
- All dimensions use `scale(value)` from `constants.py` to support resolution independence
- `UI_SCALE` global factor enables dynamic window resizing
- `BaseUIElement` uses anchor points (TL, TR, BL, BR) for docking widgets
- Builder plugins snap together horizontally using `dock_to(other_element, 'TL', 'TR')`

### Global Event Registry
- `constants.ACTIVE_COMPONENTS[]` auto-registers all UI elements
- `main.py` broadcasts `MOUSEBUTTONUP` to all components via `.global_release()`
- Prevents "sticky sliders" when switching views mid-drag

## Data Model (models.py)

### Song Structure
```
Song
├── bpm (int)
├── length_ticks (int, based on TPQN=480)
└── tracks[16]
    ├── mode ("SYNTH" | "SAMPLER")
    ├── source_type (string, e.g., "DUAL_OSC")
    ├── source_params (dict, plugin-specific)
    ├── sampler_map[0-127] (dict per MIDI pitch)
    │   ├── engine (string, e.g., "NOISE_DRUM")
    │   └── params (dict, plugin-specific)
    ├── effects[] (list of {"type", "params", "active"})
    ├── params ({"volume", "pan", "mute", "solo"})
    └── notes[] (sorted by tick)
        ├── tick (int)
        ├── pitch (int, 0-127)
        ├── duration (int, in ticks)
        └── velocity (int, 0-127)
```

### Serialization
- Save format: JSON `.bloop` files via `utils/project_manager.py`
- All models implement `.to_dict()` and `.from_dict(data)` for recursive serialization
- Forward compatibility: Uses `.get()` with defaults to handle missing keys from older versions

## Audio Engine Details

### C++ Bridge (audio_engine/bridge.py)
- Loads `synth.dll` via ctypes for machine-code oscillator math
- Provides `generate_waveform(waveform_type, frequency, duration, sample_rate)` → numpy array
- Used by DUAL_OSC plugin for low-latency synthesis

### Plugin Factory (audio_engine/plugin_factory.py)
- **Source Registry**: Maps engine IDs to Python files (e.g., "DUAL_OSC" → "dual_osc.py")
- **Effect Registry**: Same pattern for effects (e.g., "EQ" → "eq.py")
- Caches processor instances per plugin type (one instance shared across tracks)
- `.get_ui_class(plugin_id)` returns UI class (not instance) for BuilderView to instantiate per-track

### Real-Time Mixer Updates
- `AudioManager.update(song)` runs every frame (60 FPS)
- Applies fader/pan changes to all active pygame.Channel objects
- Enables smooth parameter tweaking during playback without glitches
- Instantly stops channels when mute/solo state changes

## View System (containers/)

### EditorView
- Piano Roll (0-127 MIDI range) or Drum Roll (34-52 range)
- Grid coordinates translate mouse positions to tick/pitch
- Uses `note_type_toolbar.py` for quantization and song length controls

### BuilderView
- Horizontal rack that snaps plugin UI modules together
- In SYNTH mode: Shows single source + up to 8 effects
- In SAMPLER mode: Shows sampler_brain.py for pad selection + pad-specific source UI
- Handles TOGGLE (power on/off) and DELETE actions from plugin UI

### MainMenu
- Pause overlay with NEW/SAVE/LOAD/EXIT/FULLSCREEN options
- Uses tkinter file dialogs for project I/O (requires `pygame.event.clear()` after to prevent click-through)

## Key Files and Their Responsibilities

- **main.py**: Master event loop, audio clock, view routing, fullscreen toggle
- **constants.py**: Central registry for math (TPQN, SAMPLE_RATE), UI dimensions, colors, quantization map
- **models.py**: Data schema with recursive JSON serialization
- **ui_components.py**: Primitive widgets (Button, MenuButton, Slider) with collision detection
- **audio_engine/manager.py**: Voice allocation, signal chain execution, real-time mixer
- **audio_engine/bridge.py**: Ctypes wrapper for synth.dll (C++ oscillators)
- **components/base_element.py**: Parent class for all widgets, handles anchors and global release
- **components/mixer_strip.py**: Per-track vertical channel strip (fader, pan, mute, solo, select)
- **utils/project_manager.py**: Save/Load .bloop files using tkinter dialogs

## Development Patterns

### Adding a New Source Plugin
1. Create `components/builder_plugins/my_plugin.py`
2. Implement `class Processor(BaseProcessor)` with `.generate_modular(params, note, bpm)`
3. Implement `class UI(BaseUIElement)` with `.draw()` and `.handle_event()`
4. Add entry to `plugin_factory.py` source_registry: `"MY_PLUGIN": "my_plugin"`

### Adding a New Effect Plugin
1. Create effect file in `builder_plugins/`
2. Implement `class Processor(BaseProcessor)` with `.process(buffer, params)`
3. Implement `class UI(BaseUIElement)`
4. Add entry to `plugin_factory.py` effect_registry

### Handling Resolution Changes
- Update `constants.WINDOW_W/WINDOW_H` dynamically
- Call `main._refresh_layout()` to rebuild mixer strips and update view rects
- All scale-aware components automatically adapt via `scale()` function

### Audio Thread Safety
- Pygame mixer runs audio on a separate thread
- All buffer generation happens on main thread before `channel.play()`
- Avoid file I/O or blocking operations in `.generate()` or `.process()` methods
- Parameter changes are atomic (single float/int assignments)

## Hotkeys
- **SPACE**: Play/Pause transport
- **TAB**: Toggle between EDITOR and BUILDER views
- **Hamburger Menu (top-left)**: Open MainMenu overlay

## File Formats
- **Project Files**: `.bloop` (JSON format with version field)
- **Audio Output**: 16-bit stereo PCM, 44100 Hz, 512 sample buffer

## Future Architecture Notes
- Plugin system designed for hot-reloading during development
- Anchor system prepared for node-based signal routing (non-linear FX graphs)
- AudioManager can be moved to separate process for zero-latency under heavy CPU load
- Resolution independence via `scale()` enables 4K display support

```

## File: Claude_questions.md
```markdown
while looking at the builder_view for a dual oscillator synth, if I move the curser offscreen, the program crashes. If I hover over swap to drum, it clicks without me clicking. I also am not given the ability to switch back to synth from drums. the drum builder also only got half refactored and needs some work. The intended behavior was to go from a drum synth with a built in sample pad to a standalone sampler that I could assign different drum synths too. In essence, I want the builder mode to be able to switch between pianorolling a synth sorce or drum sample-pading that synth source.

Alright, we are gettingg closer, but a ways to go still. The problem is that, since I broke drum_synth into 2 parts to make the sampler independent, I need to spin something of the synth to become the thing that holds the swap button. The sampler needs to swap with some sort of 1 shot control or other theoretical place holders. maybe it can switch between the piano roll being chromatic or modal. Or possibly even microtonal. Either way, I need the builder to swap between a piano rolled instance of any of the given synth plugins (be they piano like or drum like) or a sample pad instance Where in the current synth is assigned to the current highlighted pad in the sample pad selector. by the way, the sample pad selector radio buttons in the original drum synth worked for a small range of notes, but the stand alone sampler radio buttons still don't work. clicking 33 highlights 41. it appears all clicks ae off vertically by 2 buttons.

OK, better. Still not getting any clicks working in the sampler. That bug asside, the sample window itself should be underneath the button that toggles between piano roll and sample pads. when Piano roll is selected a new box should replace it with piano roll settings, like chromatic/modal/microtonal selections.

Oh much better! We are on to something now. Next, the 3 piano roll modes should be in a menu rectangle just like sampler brain, built from the same stuff. I'm trying to make everything from generics so I can updates styles uniformly in the future.  It should even be the same size even though it's only 3 buttons as I will be adding more to it in the future. Any case, the synth soure window (dual osc or drum) hould then be to the right of this piano-type/drum-roll menu, not bellow it. it should have a dropdown menu above it at the same height as the piano roll / sample pads buttons that shows other available synth plugins. selecting a different one should swap out the current plugin window.
```

## File: constants.py
```python
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
```

## File: main.py
```python
# Blooper 4.0 - Universal Orchestrator
import pygame
import sys
import os

# 1. Environment and Manager Imports
from utils.requirements_check import check_requirements
check_requirements()

from constants import *
from models import Song
from ui_components import MenuButton, Button
from components.mixer_strip import ChannelStrip
from audio_engine.manager import AudioManager
from utils.project_manager import ProjectManager

# 2. View Containers
from containers.editor_view import EditorView
from containers.builder_view import BuilderView
from containers.main_menu import MainMenu

class Blooper4:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption(f"Blooper {VERSION}")
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=BUFFER_SIZE)
        
        self.font = pygame.font.SysFont("Consolas", 12, bold=True)
        self.clock = pygame.time.Clock()

        # Core Engines
        self.song = Song()
        self.audio = AudioManager(self.song)
        
        # State
        self.view_mode = "EDITOR" 
        self.active_track_idx = 0
        self.is_playing = False
        self.current_tick = 0.0
        self.is_fullscreen = False

        # Persistent UI
        self.hamburger_btn = MenuButton(10, 10)
        self.btn_editor_tab = Button(100, 15, 80, 30, "EDITOR", GREEN)
        self.btn_builder_tab = Button(185, 15, 80, 30, "BUILDER", GRAY)

        # Initialize Views
        self.editor_view = EditorView(self.font)
        self.builder_view = BuilderView(self.font, self.audio.factory)
        self.main_menu = MainMenu(self.font)
        self.mixer_strips = []
        self._rebuild_mixer()

    def _rebuild_mixer(self):
        self.mixer_strips = []
        strip_w = scale(WINDOW_W // 16)
        mixer_y = WINDOW_H - scale(MIXER_H)
        for i in range(NUM_TRACKS):
            self.mixer_strips.append(ChannelStrip(i, i * strip_w, mixer_y, strip_w, scale(MIXER_H)))

    def run(self):
        while True:
            dt = self.clock.tick(FPS)
            self.screen.fill(COLOR_BG)

            # --- 1. AUDIO CLOCK ---
            if self.is_playing:
                ticks_per_ms = (self.song.bpm * TPQN) / 60000.0
                prev_tick = self.current_tick
                self.current_tick += (dt * ticks_per_ms)
                
                if self.current_tick >= self.song.length_ticks:
                    self._check_and_trigger(prev_tick, self.song.length_ticks)
                    self.current_tick %= self.song.length_ticks
                    prev_tick = 0.0
                self._check_and_trigger(prev_tick, self.current_tick)

            self.audio.update(self.song)

            # --- 2. UNIVERSAL EVENTS ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self._quit_app()
                if event.type == pygame.MOUSEBUTTONUP:
                    for comp in ACTIVE_COMPONENTS: 
                        if hasattr(comp, 'global_release'): comp.global_release()

                # ROUTE: MENU
                if self.view_mode == "MENU":
                    self._handle_menu_events(event)
                    continue

                # ROUTE: HEADER
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.hamburger_btn.is_clicked(event.pos): self.view_mode = "MENU"
                    if self.btn_editor_tab.is_clicked(event.pos): self.view_mode = "EDITOR"
                    if self.btn_builder_tab.is_clicked(event.pos): self.view_mode = "BUILDER"

                # ROUTE: HOTKEYS
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE: self.is_playing = not self.is_playing
                    if event.key == pygame.K_TAB: self.view_mode = "BUILDER" if self.view_mode == "EDITOR" else "EDITOR"

                # ROUTE: MIXER & CONTENT
                for i, strip in enumerate(self.mixer_strips):
                    if strip.handle_event(event, self.song.tracks[i], UI_SCALE) == "SELECT":
                        self.active_track_idx = i

                if self.view_mode == "EDITOR": self.editor_view.handle_event(event, self.song, self.active_track_idx)
                elif self.view_mode == "BUILDER": self.builder_view.handle_event(event, self.song, self.active_track_idx)

            # --- 3. DRAWING ---
            self._render_ui()
            pygame.display.flip()

    def _handle_menu_events(self, event):
        action = self.main_menu.handle_event(event)
        if not action: return
        
        if action == "RESUME": self.view_mode = "EDITOR"
        elif action == "EXIT": self._quit_app()
        elif action == "NEW": 
            self.song = Song()
            self.audio.current_song_ref = self.song
            self.view_mode = "EDITOR"
        elif action == "SAVE": ProjectManager.save(self.song)
        elif action == "LOAD":
            new_song = ProjectManager.load()
            if new_song:
                self.song = new_song
                self.audio.current_song_ref = self.song
                self.view_mode = "EDITOR"
        elif action == "TOGGLE_FS": self._toggle_fullscreen()
        elif action == "REBUILD_UI": self._refresh_layout()

    def _render_ui(self):
        if self.view_mode == "MENU":
            self.main_menu.draw(self.screen)
        else:
            if self.view_mode == "EDITOR": self.editor_view.draw(self.screen, self.song, self.active_track_idx, self.current_tick, self.font)
            else: self.builder_view.draw(self.screen, self.song, self.active_track_idx)

            for i, strip in enumerate(self.mixer_strips):
                strip.draw(self.screen, self.song.tracks[i], i == self.active_track_idx, self.font, UI_SCALE)

            pygame.draw.rect(self.screen, COLOR_PANEL, (0, 0, WINDOW_W, HEADER_H))
            self.hamburger_btn.draw(self.screen)
            self.btn_editor_tab.color = GREEN if self.view_mode == "EDITOR" else GRAY
            self.btn_builder_tab.color = GREEN if self.view_mode == "BUILDER" else GRAY
            self.btn_editor_tab.draw(self.screen, self.font)
            self.btn_builder_tab.draw(self.screen, self.font)
            
            status = f"{'PLAY' if self.is_playing else 'STOP'} | BPM: {self.song.bpm} | TRACK: {self.active_track_idx+1}"
            self.screen.blit(self.font.render(status, True, WHITE), (320, 25))

    def _check_and_trigger(self, start, end):
        for i, track in enumerate(self.song.tracks):
            for note in track.notes:
                if start <= note.tick < end:
                    self.audio.play_note(i, track, note, self.song.bpm)

    def _toggle_fullscreen(self):
        import constants
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            info = pygame.display.Info()
            constants.WINDOW_W, constants.WINDOW_H = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((constants.WINDOW_W, constants.WINDOW_H), pygame.FULLSCREEN)
        else:
            constants.WINDOW_W, constants.WINDOW_H = 1280, 800
            self.screen = pygame.display.set_mode((1280, 800))
        self._refresh_layout()

    def _refresh_layout(self):
        self._rebuild_mixer()
        self.editor_view.update_view_rect()
        self.builder_view.update_view_rect()
        self.main_menu.rect = pygame.Rect(0, 0, WINDOW_W, WINDOW_H)

    def _quit_app(self):
        self.audio.cleanup()
        pygame.quit(); sys.exit()

if __name__ == "__main__":
    Blooper4().run()
```

## File: models.py
```python
# Blooper4/models.py
from constants import TPQN, NUM_TRACKS, DRUM_NOTE_START, DRUM_NOTE_END, SAMPLER_DEFAULT_START

class Note:
    """Represents a single MIDI note event in the 4.0 schema."""
    def __init__(self, tick, pitch, duration, velocity=100):
        self.tick = tick
        self.pitch = pitch
        self.duration = duration
        self.velocity = velocity

    def to_dict(self):
        """Standardized compact dictionary for JSON export."""
        return {"t": self.tick, "p": self.pitch, "d": self.duration, "v": self.velocity}

    @classmethod
    def from_dict(cls, data):
        """Factory method to recreate a note from a dictionary."""
        return cls(data['t'], data['p'], data['d'], data['v'])

class Track:
    """A 4.1 Mixer Channel. Can operate as a single Synth or a Multi-Instrument Sampler.

    OPERATING MODES:
    ----------------
    - "SYNTH": Single source engine plays all notes (traditional synthesizer)
      Uses: source_type, source_params
      Example: DUAL_OSC plugin with saw + sine waves

    - "SAMPLER": Each MIDI pitch has independent engine (workstation/drum machine)
      Uses: sampler_map[0-127]
      Example: Kick on C1, Snare on D1, Hi-hat on F#1

    IMPORTANT - Mode Switching:
    ---------------------------
    When switching modes, ALWAYS update ALL three fields atomically:
      track.mode = "SYNTH" or "SAMPLER"  # Primary field - checked by builder_view
      track.is_drum = True/False          # Legacy field - kept for compatibility
      track.source_type = "PLUGIN_ID"     # Which plugin to display

    The 'mode' field is the authoritative source of truth for track behavior.
    """
    def __init__(self, channel, is_drum=False):
        self.channel = channel
        self.name = "Sampler" if is_drum else f"Track {channel}"

        # ===== OPERATING MODE (AUTHORITATIVE FIELD) =====
        # This is the PRIMARY field that determines track behavior
        # builder_view.py checks this at line 71 to determine which UI to show
        # audio_engine/manager.py checks this to route note playback
        self.mode = "SAMPLER" if is_drum else "SYNTH"

        # Legacy compatibility field (deprecated in 4.1, use 'mode' instead)
        self.is_drum = is_drum

        # UI State for Builder
        self.active_pad = SAMPLER_DEFAULT_START
        self.sampler_base_note = SAMPLER_DEFAULT_START

        # ===== SYNTH MODE DATA =====
        # Used ONLY when mode == "SYNTH"
        # Defines which single plugin handles ALL notes on this track
        self.source_type = "DUAL_OSC"  # Current source plugin
        self.last_synth_source = "DUAL_OSC"  # Memory: last synth used in SYNTH mode
        self.source_params = {         # Parameters for that plugin
            "osc1_type": "SAW",
            "osc2_type": "SINE",
            "osc2_detune": 10,
            "volume": 0.8
        }

        # Piano roll settings (used in SYNTH mode)
        self.piano_roll_scale = "CHROMATIC"  # "CHROMATIC", "MODAL", or "MICROTONAL"

        # ===== SAMPLER MODE DATA (NEW 4.1 ARCHITECTURE) =====
        # Used ONLY when mode == "SAMPLER"
        # Each MIDI pitch [0-127] has its own independent engine + parameters
        self.sampler_map = {}  # Populated by _init_sampler_map()
        self._init_sampler_map()

        # ===== MIXER PARAMS (ALWAYS USED) =====
        # Applied regardless of mode (final stage of signal chain)
        self.params = {
            "volume": 0.8,
            "pan": 0.5,
            "mute": False,
            "solo": False,
        }

        # ===== LEGACY DRUM DATA (BACKWARD COMPATIBILITY) =====
        # DEPRECATED: The old noise_drum.py plugin still reads from this
        # New code should use sampler_map instead
        # Keep this populated for backward compatibility with existing .bloop files
        # TODO: Eventually migrate noise_drum.py to use sampler_map directly
        from constants import DRUM_NOTE_START, DRUM_NOTE_END
        self.drum_pads = {
            p: {"type": "DRUM", "pitch": 60, "length": 0.3}
            for p in range(DRUM_NOTE_START, DRUM_NOTE_END + 1)
        }

        self.effects = [] 
        self.notes = []

    def _init_sampler_map(self):
        """Initializes all 128 pads with default Noise Drum settings."""
        for p in range(0, 128):
            self.sampler_map[p] = {
                "engine": "NOISE_DRUM",
                "params": {"pitch": 60, "length": 0.3, "type": "DRUM", "gain": 1.0, "color": "WHITE"},
                "label": "" # User override label
            }

    def to_dict(self):
        """Standardized 4.1 serialization."""
        return {
            "name": self.name,
            "is_drum": self.is_drum,
            "mode": self.mode,
            "source_type": self.source_type,
            "last_synth_source": getattr(self, 'last_synth_source', self.source_type),  # Backward compat
            "source_params": self.source_params,
            "piano_roll_scale": getattr(self, 'piano_roll_scale', 'CHROMATIC'),
            "sampler_map": {str(k): v for k, v in self.sampler_map.items()},
            "params": self.params,
            "effects": self.effects,
            "notes": [n.to_dict() for n in self.notes]
        }
    
    def from_dict(self, data):
        """Reconstructs track state from dictionary."""
        self.name = data.get('name', self.name)
        self.is_drum = data.get('is_drum', self.is_drum)
        self.mode = data.get('mode', self.mode)
        self.source_type = data.get('source_type', self.source_type)
        self.last_synth_source = data.get('last_synth_source', self.source_type)  # Backward compat
        self.piano_roll_scale = data.get('piano_roll_scale', 'CHROMATIC')

        # Merge dictionaries to preserve default keys if the save file is from an older version
        self.source_params.update(data.get('source_params', {}))
        self.params.update(data.get('params', {}))
        self.effects = data.get('effects', [])
        
        if 'sampler_map' in data:
            s_map = data['sampler_map']
            self.sampler_map = {int(k): v for k, v in s_map.items()}
            
        self.notes = [Note.from_dict(n) for n in data.get('notes', [])]
        self.notes.sort(key=lambda x: x.tick)
        
    def add_effect(self, effect_type):
        if len(self.effects) < 8:
            defaults = {"EQ": {f"band_{i}": 1.0 for i in range(8)}, "REVERB": {"mix": 0.1, "size": 0.5}}
            self.effects.append({"type": effect_type, "params": defaults.get(effect_type, {}), "active": True})

    def add_note(self, tick, pitch, duration, velocity=100):
        new_note = Note(tick, pitch, duration, velocity)
        self.notes.append(new_note)
        self.notes.sort(key=lambda x: x.tick)
        return new_note

class Song:
    """The Root container for a Blooper 4.0 Project."""
    def __init__(self):
        self.bpm = 120
        self.length_ticks = TPQN * 4
        self.tracks = [Track(i+1, is_drum=(i==9)) for i in range(NUM_TRACKS)]
        self.is_dirty = False
        self.file_path = None
    
    def to_dict(self):
        """Master serialization for .bloop file saving."""
        return {
            "version": "4.1.0",
            "bpm": self.bpm,
            "length_ticks": self.length_ticks,
            "tracks": [t.to_dict() for t in self.tracks]
        }

    def from_dict(self, data):
        self.bpm = data.get('bpm', 120)
        self.length_ticks = data.get('length_ticks', TPQN * 4)
        for i, t_data in enumerate(data.get('tracks', [])):
            if i < len(self.tracks):
                self.tracks[i].from_dict(t_data)
```

## File: project_to_md.py
```python
import os

# --- CONFIGURATION ---
OUTPUT_FILE = "project_context.md"
# Folders to skip entirely
IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', 'dist', 'build', '.vscode', 'venv', 'env'}
# Extensions to skip (binaries, images, etc.)
IGNORE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.pyc', '.exe', '.dll', '.so', '.pdf'}
# Mapping extensions to markdown language tags
LANG_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.jsx': 'jsx',
    '.html': 'html',
    '.css': 'css',
    '.json': 'json',
    '.md': 'markdown',
    '.sh': 'bash',
    '.yml': 'yaml',
    '.yaml': 'yaml'
}

def generate_markdown():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# Project Source Code Context\n\n")
        
        # Optional: Add a directory tree at the top
        outfile.write("## Project Structure\n```text\n")
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            level = root.replace('.', '').count(os.sep)
            indent = ' ' * 4 * level
            outfile.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                if not any(f.endswith(ext) for ext in IGNORE_EXTS):
                    outfile.write(f"{sub_indent}{f}\n")
        outfile.write("```\n\n---\n\n")

        # Process and write file contents
        for root, dirs, files in os.walk('.'):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in IGNORE_EXTS or file == OUTPUT_FILE:
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        
                        relative_path = os.path.relpath(file_path, '.')
                        lang = LANG_MAP.get(ext, '')
                        
                        outfile.write(f"## File: {relative_path}\n")
                        outfile.write(f"```{lang}\n")
                        outfile.write(content)
                        outfile.write(f"\n```\n\n")
                        print(f"Included: {relative_path}")
                except Exception as e:
                    print(f"Skipped {file_path} due to error: {e}")

if __name__ == "__main__":
    generate_markdown()
    print(f"\nDone! Project saved to {OUTPUT_FILE}")
```

## File: READ_ME.md
```markdown
# BLOOPER 4.0 - MODULAR DAW ARCHITECTURE
## 1. PROJECT STRUCTURE MAP
Blooper4/
├── main.py                  # System Orchestrator & Focus Guard
├── constants.py             # Global Math, Scaling (UI_SCALE), & UI Registry
├── models.py                # Data Schema & Recursive JSON Serialization
├── ui_components.py         # UI Primitives (Scale-Aware Sliders/Buttons)
├── requirements.txt         # Dependency Manifest
├── audio_engine/
│   ├── __init__.py          # Python Package Marker
│   ├── bridge.py            # Ctypes wrapper for C++ Logic
│   ├── manager.py           # Signal Chain Orchestrator & Voice Manager
│   ├── base_processor.py    # Parent class for Audio Math (The Contract)
│   ├── plugin_factory.py    # Dynamic Loader (The "Middleman")
│   └── src/
│       └── synthesizer.cpp  # Machine Code Oscillator Math (DLL Source)
├── components/
│   ├── __init__.py          # Python Package Marker
│   ├── base_element.py      # Parent for UI Widgets (Anchors/Scaling)
│   ├── mixer_strip.py       # Vertical Channel UI (Faders/Pan/Mute)
│   ├── mixer_panel.py       # Horizontal Container for 16 mixer_strips
│   ├── piano_roll.py        # Melodic Grid Logic & Clipping
│   ├── drum_roll.py         # Percussion Grid Logic (34-52)
│   ├── note_type_toolbar.py # Editor-specific tools (Quantize/Bars)
│   └── builder_plugins/     # Modular Plugin files (Processor + UI classes)
│       ├── __init__.py      # Package Marker for Factory Loading
│       ├── dual_osc.py      # Synth Source Plugin
│       ├── noise_drum.py    # Drum Source Plugin
│       ├── eq.py            # 8-Band EQ Effect Plugin
│       └── reverb.py        # Feedback-Delay Reverb Plugin
├── containers/
│   ├── __init__.py          # Python Package Marker
│   ├── base_view.py         # Layout Template (Header/Mixer logic)
│   ├── main_menu.py         # Settings & Video Hub
│   ├── editor_view.py       # Sequencing Workspace
│   └── builder_view.py      # Plugin Rack Workspace
└── utils/
    ├── __init__.py          # Python Package Marker
    └── requirements_check.py # Environment Self-Healer

## 2. FILE DEFINITIONS
**main.py**: The master dispatcher that handles the high-resolution clock and routes events to active containers.

**constants.py**: The central source of truth for math, colors, and the UI_SCALE factor used for dynamic resizing.

**models.py**: Defines the data structures for the Song, Tracks, and Notes, handling all recursive JSON saving/loading logic.

**ui_components.py**: Provides the "Atoms" of the interface (Buttons, Sliders) with built-in collision math and scaling support.

**audio_engine/bridge.py**: Manages communication with the synth.dll, passing Python data to Machine Code for low-latency math.

**audio_engine/manager.py**: Orchestrates 64-voice polyphony and runs the serial FX loop for every triggered note.

**audio_engine/plugin_factory.py**: Uses dynamic imports to extract Processor and UI classes from plugin files without hard-coding.

**components/base_element.py**: The foundation for all visuals; establishes the 4-corner Anchor system for relative docking.

**components/mixer_panel.py**: A layout-aware container that manages the arrangement of 16 Mixer Strips at the bottom of the screen.

**components/note_type_toolbar.py**: A specialized widget for the Editor view that handles quantization and song length logic.

**components/piano_roll.py**: A coordinate-aware grid that translates pixels into MIDI data relative to its docked screen area.

**containers/builder_view.py**: A horizontal rack manager that automatically snaps plugin modules together using the Anchor system.

**utils/requirements_check.py**: A self-healing script that verifies and installs missing libraries on DAW startup.


## 3. DATA FLOW & CLASS COMPLIANCE
Blooper 4.0 utilizes a **Serial Pipeline Architecture**. 
Data starts in the `models.py` as a `Note` object. 
The `main.py` clock identifies a note's `tick` and sends it to the `AudioManager`. 
The manager retrieves the `Source` buffer (C++), processes it through a list of `Effect` objects, and applies `Mixer` modifiers. 
The resulting buffer is stacked into a stereo PCM array and handed to a Pygame Mixer Channel.

### Plugin Compliance:
All plugins must be a single file in `builder_plugins/` containing:
- **class Processor(BaseProcessor)**: Must implement `.generate()` (Sources) or `.process()` (Effects).
- **class UI(BaseUIElement)**: Must implement `.draw()` and `.handle_event()`.

### Widget Compliance:
All UI widgets must inherit from `BaseUIElement`. 
They must use `self.rect` for collision and `self.anchors` for positioning. 
They must implement `global_release()` to reset internal interactive states (like grabbed sliders).

## 4. FUTURE ARCHITECTURAL NOTES
**Dynamic Registry**: The system is designed to allow new plugins to be added simply by dropping a .py file into the plugins folder and adding one line to the Factory.

**Node-Based Signal Path**: The Anchor system (TL, TR, BL, BR) is prepped to support non-linear routing, allowing signals to split and rejoin.

**Resolution Independence**: By avoiding hard-coded pixel coordinates in favor of `scale()` and `dock_to()`, the DAW can eventually support arbitrary window sizes and 4K displays.

**Process Isolation**: The architecture is ready to move the `AudioManager` into a completely separate CPU process to achieve 0% note-dropping in complex songs.
```

## File: requirements.txt
```
pygame==2.6.1
numpy>=1.26.0
scipy>=1.11.0

```

## File: ui_components.py
```python
# Blooper4/ui_components.py
import pygame
from constants import *

class Button:
    """
    A clickable UI box.
    Inputs:
        x, y (int): Top-left corner position.
        w, h (int): Width and Height.
        text (str): String label displayed in center.
        color (tuple): RGB tuple for background.
        border_radius (int): Optional corner rounding.
    """
    def __init__(self, x, y, w, h, text, color, border_radius=5):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.radius = border_radius
        self.enabled = True 

    def draw(self, screen, font):
        draw_color = self.color if self.enabled else (40, 40, 45)
        text_color = WHITE if self.enabled else (80, 80, 85)
        
        pygame.draw.rect(screen, draw_color, self.rect, border_radius=self.radius)
        # Subtle top-lighting highlight
        if self.enabled:
            pygame.draw.line(screen, (255, 255, 255, 30), (self.rect.x, self.rect.y), (self.rect.right, self.rect.y))
        
        # Draw the standardized border
        pygame.draw.rect(screen, (255, 255, 255, 20), self.rect, 1, border_radius=self.radius)
        
        txt = font.render(self.text, True, text_color)
        screen.blit(txt, (self.rect.centerx - txt.get_width()//2, self.rect.centery - txt.get_height()//2))

    def is_clicked(self, pos):
        """Returns True only if enabled and position is inside bounds."""
        return self.enabled and self.rect.collidepoint(pos)

    def move_to(self, x, y, w=None, h=None):
        """Updates position and optionally resizes for scaling."""
        self.rect.x = x
        self.rect.y = y
        # FIX: Ensure width and height are updated for collision detection!
        if w is not None: self.rect.width = w
        if h is not None: self.rect.height = h

class RadioGroup:
    """
    A set of mutually exclusive toggle buttons.
    Inputs:
        x, y (int): Top-left corner of the button group area.
        options (list): List of strings for labels.
        font (pygame.font): Font object for labels.
        cols (int): Buttons per row before wrapping.
        default_idx (int): Which index starts selected.
    """
    def __init__(self, x, y, options, font, cols=5, default_idx=0):
        self.options = options
        self.selected = options[default_idx] if default_idx < len(options) else (options[0] if options else "")
        self.buttons = []
        self.cols = cols
        
        # Initial construction (default sizes)
        #self.move_to(x, y, 55, 22)
        self.move_to(x, y)

    def draw(self, screen, font):
        for btn in self.buttons:
            is_sel = btn['text'] == self.selected
            color = COLOR_ACCENT if is_sel else (60, 60, 65)
            pygame.draw.rect(screen, color, btn['rect'], border_radius=3)
            
            txt_color = BLACK if is_sel else WHITE
            txt = font.render(btn['text'], True, txt_color)
            screen.blit(txt, (btn['rect'].centerx - txt.get_width()//2, btn['rect'].centery - txt.get_height()//2))

    def handle_event(self, event):
        """Checks for clicks and updates the internal selection state."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn['rect'].collidepoint(event.pos):
                    self.selected = btn['text']
                    return self.selected
        return None
    
    def move_to(self, x, y, btn_w=55, btn_h=22):
        """Re-calculates button grid layout."""
        self.buttons = []
        # Use scale() from constants to ensure button size matches theme
        from constants import scale
        sw, sh = scale(btn_w), scale(btn_h)
        gap = scale(5)
        for i, opt in enumerate(self.options):
            bx = x + (i % self.cols) * (sw + gap)
            by = y + (i // self.cols) * (sh + gap)
            self.buttons.append({'rect': pygame.Rect(bx, by, sw, sh), 'text': opt})

class MenuButton:
    """
    A square 'Hamburger' icon button used for global navigation.
    Inputs:
        x, y (int): Screen coordinates.
        size (int): Width and height of the button.
    """
    def __init__(self, x, y, size=40):
        self.rect = pygame.Rect(x, y, size, size)

    def draw(self, screen):
        # Draw background container
        pygame.draw.rect(screen, (45, 45, 50), self.rect, border_radius=3)
        pygame.draw.rect(screen, (70, 70, 75), self.rect, 1, border_radius=3)
        
        # Draw 3 horizontal lines (proportionally)
        line_w = self.rect.width * 0.6
        start_x = self.rect.x + (self.rect.width - line_w) // 2
        for i in range(3):
            ly = self.rect.y + (self.rect.height * 0.3) + (i * (self.rect.height * 0.2))
            pygame.draw.line(screen, WHITE, (start_x, ly), (start_x + line_w, ly), 2)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

class Slider:
    """
    A generic value controller.
    Inputs:
        x, y, w, h: Rect bounds.
        min_val, max_val: Floating point range.
        start_val: Initial position.
        label: Text displayed above or near slider.
        vertical: Boolean orientation.
    """
    def __init__(self, x, y, w, h, min_val, max_val, start_val, label, vertical=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = start_val
        self.label = label
        self.vertical = vertical
        self.grabbed = False

    def draw(self, screen, font):
        # Track Background
        pygame.draw.rect(screen, (20, 20, 25), self.rect, border_radius=3)
        
        # Handle position calculation
        range_val = self.max_val - self.min_val
        ratio = (self.val - self.min_val) / range_val if range_val != 0 else 0
        
        if self.vertical:
            handle_y = self.rect.bottom - (ratio * self.rect.height) - 5
            handle_rect = pygame.Rect(self.rect.x - 5, handle_y, self.rect.width + 10, 10)
        else:
            handle_x = self.rect.x + (ratio * self.rect.width) - 5
            handle_rect = pygame.Rect(handle_x, self.rect.y - 5, 10, self.rect.height + 10)
            
        pygame.draw.rect(screen, COLOR_ACCENT, handle_rect, border_radius=2)
        
        if self.label:
            # High precision for small ranges (mix/gain), integers for MIDI ranges
            display_val = f"{self.val:.2f}" if range_val <= 2 else f"{int(self.val)}"
            txt = font.render(f"{self.label}: {display_val}", True, WHITE)
            screen.blit(txt, (self.rect.x, self.rect.y - 20))

    def handle_event(self, event):
        # Increased hitbox for easier grabbing
        hitbox = self.rect.inflate(20, 20)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hitbox.collidepoint(event.pos):
                self.grabbed = True
        
        if event.type == pygame.MOUSEBUTTONUP:
            self.grabbed = False

        if self.grabbed:
            m_pos = pygame.mouse.get_pos()
            # SAFETY: Clamp mouse coordinates to window bounds to prevent offscreen crashes
            from constants import WINDOW_W, WINDOW_H
            clamped_x = max(0, min(m_pos[0], WINDOW_W - 1))
            clamped_y = max(0, min(m_pos[1], WINDOW_H - 1))

            if self.vertical:
                rel = 1.0 - (max(0, min(clamped_y - self.rect.y, self.rect.height)) / self.rect.height)
            else:
                rel = (max(0, min(clamped_x - self.rect.x, self.rect.width)) / self.rect.width)
            self.val = self.min_val + rel * (self.max_val - self.min_val)
            return self.val
        return None
    
    def move_to(self, x, y, w=None, h=None):
        """Adjusts placement and size dynamically."""
        self.rect.x = x
        self.rect.y = y
        if w: self.rect.width = w
        if h: self.rect.height = h

class Dropdown:
    """
    A dropdown menu that displays a list of options when opened.
    Inputs:
        x, y (int): Position of the dropdown trigger button
        w, h (int): Size of the trigger button
        options (list): List of string options to display
        label (str): Text to show on the trigger button
    """
    def __init__(self, x, y, w, h, options, label="SELECT"):
        self.rect = pygame.Rect(x, y, w, h)  # Trigger button area
        self.options = options
        self.label = label
        self.is_open = False
        self.selected_option = None
        self.dropdown_rect = None  # Calculated in draw()

    def draw(self, screen, font):
        """Draw the trigger button and dropdown menu if open."""
        # Draw trigger button
        pygame.draw.rect(screen, COLOR_PANEL, self.rect, border_radius=scale(5))

        # Display label
        txt_surf = font.render(self.label, True, WHITE)
        screen.blit(txt_surf, (self.rect.x + scale(10),
                              self.rect.centery - txt_surf.get_height()//2))

        # Dropdown arrow
        arrow = font.render("▼", True, WHITE)
        screen.blit(arrow, (self.rect.right - scale(30),
                           self.rect.centery - arrow.get_height()//2))

        # Draw dropdown menu if open
        if self.is_open:
            # Position dropdown below trigger
            self.dropdown_rect = pygame.Rect(
                self.rect.x,
                self.rect.bottom + scale(5),
                self.rect.width,
                scale(30 * len(self.options))
            )

            # Draw background
            pygame.draw.rect(screen, COLOR_PANEL, self.dropdown_rect, border_radius=scale(5))
            pygame.draw.rect(screen, COLOR_ACCENT, self.dropdown_rect, width=2, border_radius=scale(5))

            # Draw options
            mouse_pos = pygame.mouse.get_pos()
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(
                    self.dropdown_rect.x + scale(5),
                    self.dropdown_rect.y + scale(5) + i * scale(30),
                    self.dropdown_rect.width - scale(10),
                    scale(25)
                )

                # Highlight on hover
                if option_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, (60, 60, 70), option_rect, border_radius=scale(3))

                txt_surf = font.render(option, True, WHITE)
                screen.blit(txt_surf, (option_rect.x + scale(5), option_rect.y + scale(5)))

    def handle_event(self, event):
        """
        Handle click events.
        Returns:
            - Selected option string if user clicked an option
            - "TOGGLE" if user clicked the trigger button
            - None otherwise
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if clicked on trigger button
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return "TOGGLE"

            # Check if clicked on dropdown option (when open)
            if self.is_open and self.dropdown_rect and self.dropdown_rect.collidepoint(event.pos):
                idx = (event.pos[1] - self.dropdown_rect.y - scale(5)) // scale(30)
                if 0 <= idx < len(self.options):
                    self.selected_option = self.options[idx]
                    self.is_open = False
                    return self.selected_option

            # Click outside dropdown - close it
            if self.is_open:
                self.is_open = False

        return None

    def move_to(self, x, y, w=None, h=None):
        """Updates position and optionally resizes."""
        self.rect.x = x
        self.rect.y = y
        if w is not None: self.rect.width = w
        if h is not None: self.rect.height = h

    def set_label(self, label):
        """Update the trigger button label."""
        self.label = label
```

## File: .claude\agents\daw-code-architect.md
```markdown
---
name: daw-code-architect
description: Use this agent when the user needs assistance writing code for their Digital Audio Workstation (DAW) project. This includes:\n\n<example>\nContext: User is building a DAW and needs help implementing audio processing features.\nuser: "I need to implement a low-pass filter for the audio engine"\nassistant: "I'm going to use the Task tool to launch the daw-code-architect agent to help design and implement the low-pass filter."\n<commentary>\nSince the user needs DAW-specific code implementation, use the daw-code-architect agent to provide expert guidance on audio processing implementation.\n</commentary>\n</example>\n\n<example>\nContext: User is working on the DAW's UI components.\nuser: "Can you help me create a waveform visualization component?"\nassistant: "Let me use the daw-code-architect agent to help build the waveform visualization component."\n<commentary>\nThe user needs DAW-specific UI code, so delegate to the daw-code-architect agent who understands both audio processing and visualization requirements.\n</commentary>\n</example>\n\n<example>\nContext: User just implemented a MIDI sequencer module.\nuser: "I've finished the basic MIDI sequencer implementation"\nassistant: "Great work! Now let me use the daw-code-architect agent to review the MIDI sequencer code and suggest improvements."\n<commentary>\nAfter completing a logical chunk of DAW code, proactively use the agent to review for audio-specific considerations like timing accuracy, thread safety, and performance.\n</commentary>\n</example>\n\n<example>\nContext: User is structuring their DAW project architecture.\nuser: "I'm not sure how to organize the audio engine, plugins, and UI layers"\nassistant: "I'll use the daw-code-architect agent to help design the architectural structure for your DAW."\n<commentary>\nArchitectural decisions for DAWs require specialized knowledge of audio processing patterns, so delegate to the expert agent.\n</commentary>\n</example>
model: sonnet
color: cyan
---

You are an elite Digital Audio Workstation (DAW) software architect with deep expertise in audio programming, real-time systems, and music production software development. Your mission is to help build robust, performant, and professional-grade DAW code.

## Core Competencies

You have expert knowledge in:
- **Audio Processing**: DSP algorithms, filters, effects, synthesis, sample-accurate processing
- **Real-Time Systems**: Low-latency audio, buffer management, thread safety, lock-free programming
- **Audio APIs**: Web Audio API, Core Audio, ASIO, JACK, PortAudio, WASAPI
- **MIDI**: MIDI protocol, sequencing, timing, MPE (MIDI Polyphonic Expression)
- **Audio Formats**: WAV, MP3, FLAC, OGG, sample rate conversion, bit depth handling
- **DAW Architecture**: Plugin systems (VST, AU, LV2), routing, mixing, automation
- **UI/UX**: Waveform visualization, timeline editing, mixer interfaces, keyboard shortcuts
- **Performance**: Memory management, CPU optimization, SIMD, multithreading strategies

## Operational Guidelines

### Code Quality Standards
1. **Real-Time Safety**: Always prioritize code that runs in the audio thread without blocking
   - Avoid allocations, locks, system calls, or file I/O in audio callbacks
   - Use lock-free data structures for cross-thread communication
   - Preallocate buffers and resources during initialization

2. **Sample Accuracy**: Ensure timing-critical operations are sample-accurate
   - Handle automation and parameter changes at sample boundaries
   - Account for buffer boundaries in effect processing
   - Maintain precise MIDI timing

3. **Numerical Stability**: Apply audio-specific numerical techniques
   - Use appropriate data types (float vs double for audio)
   - Implement denormal handling to prevent CPU spikes
   - Apply dithering when reducing bit depth
   - Prevent DC offset accumulation

4. **Modularity**: Design loosely-coupled, reusable audio components
   - Separate audio processing from UI logic
   - Create clear interfaces for plugins and effects
   - Enable easy unit testing of audio algorithms

### Development Workflow

When writing DAW code:

1. **Understand Context First**
   - Identify which layer you're working in (audio engine, UI, plugin host, file I/O)
   - Determine real-time vs non-real-time requirements
   - Consider the broader architectural impact

2. **Design Before Coding**
   - Sketch out data flow and threading model
   - Identify potential performance bottlenecks
   - Plan for extensibility and plugin integration

3. **Implement with Best Practices**
   - Follow the project's existing coding standards from CLAUDE.md if available
   - Add clear comments for complex DSP or threading logic
   - Include assertions for invariants and preconditions
   - Handle edge cases (silence, clipping, underruns)

4. **Validate Thoroughly**
   - Suggest test cases for audio correctness (impulse response, frequency response)
   - Recommend performance profiling for critical paths
   - Check for common issues: clicks/pops, drift, memory leaks, race conditions

### Specific Guidance Areas

**Audio Engine**:
- Implement robust buffer management with configurable sizes
- Handle sample rate and buffer size changes gracefully
- Provide clear separation between processing and I/O threads
- Include overflow/underflow detection and recovery

**Effects & Processing**:
- Use established DSP formulas and cite sources when relevant
- Implement smooth parameter interpolation to avoid zipper noise
- Consider mono, stereo, and multichannel scenarios
- Optimize inner loops for SIMD when beneficial

**MIDI Handling**:
- Process MIDI events in timestamp order
- Handle note-on/off pairing correctly
- Support all MIDI message types appropriately
- Implement accurate tempo and time signature tracking

**File I/O & Project Management**:
- Use background threads for file operations
- Implement proper error handling and recovery
- Support undo/redo for all editable operations
- Design efficient project save/load formats

**UI Components**:
- Decouple UI from audio thread completely
- Implement efficient waveform rendering (LOD, caching)
- Provide responsive visual feedback (<16ms updates)
- Follow platform-specific UI guidelines

**Plugin System**:
- Design a clear plugin API with versioning
- Handle plugin crashes gracefully
- Implement proper plugin scanning and validation
- Support plugin state serialization

## Communication Style

- **Be Precise**: Use exact technical terminology for audio concepts
- **Explain Trade-offs**: When multiple approaches exist, explain pros/cons
- **Provide Context**: Explain *why* certain patterns are used in DAW development
- **Flag Risks**: Proactively identify potential issues (latency, artifacts, instability)
- **Suggest Testing**: Recommend specific ways to verify audio correctness
- **Stay Current**: Reference modern best practices and APIs

## Quality Assurance

Before presenting code:
1. Verify it won't cause audio glitches or crashes
2. Confirm it follows real-time programming principles if applicable
3. Check for proper resource cleanup
4. Ensure it integrates well with typical DAW architectures
5. Consider cross-platform compatibility unless platform-specific

When you need more information to provide the best solution, ask targeted questions about:
- Target platform and audio APIs
- Performance requirements (latency, CPU budget)
- Supported audio formats and sample rates
- Plugin architecture preferences
- Existing codebase patterns

Your goal is to help create a professional, stable, and performant DAW that musicians will love to use.

```

## File: audio_engine\base_processor.py
```python
# Blooper4/audio_engine/base_processor.py

class BaseProcessor:
    """
    The Parent class for all Blooper 4.0 Audio Engines.
    Establishes the 'Contract' that allows the AudioManager to be generic.
    """
    def __init__(self):
        # Universal state for all audio math
        self.active = True

    def generate(self, track_model, note_model, bpm):
        """
        SOURCES (Synths/Drums) override this method.
        Input: 
            track_model: Access to track.source_params
            note_model: Access to note.pitch, note.velocity, note.duration
            bpm: Current project tempo
        Output: 
            A numpy float32 buffer of raw audio.
        """
        # Default behavior: silence
        return None

    def generate_modular(self, params, note, bpm): 
        """Standardized 4.1 entry point for both Synth and Sampler modes."""
        # Plugins will implement this to handle a simple parameter dictionary
        return None

    def process(self, buffer, params):
        """
        EFFECTS (EQ/Reverb) override this method.
        Input:
            buffer: The numpy float32 audio data from the previous stage
            params: Access to effect-specific parameters (e.g. fx['params'])
        Output:
            The modified numpy float32 buffer.
        """
        # Default behavior: pass-through (bypass)
        return buffer

    def toggle_power(self):
        """Standard method to enable/disable the module."""
        self.active = not self.active
```

## File: audio_engine\bridge.py
```python
# Blooper4/audio_engine/bridge.py
import ctypes
import numpy as np
import os
import sys

class CPPSynthBridge:
    """
    4.0 Bridge: The low-level interface to the C++ Machine Code.
    Acts as a wrapper for synth.dll, providing high-speed oscillator math.
    """
    def __init__(self, sample_rate=44100):
        self.sample_rate = float(sample_rate)
        self.lib = self._load_library()
        self._setup_functions()

    def _load_library(self):
        """Locates and loads the compiled C++ DLL."""
        # Get absolute path to the DLL in the same folder as this script
        dir_path = os.path.dirname(os.path.abspath(__file__))
        lib_path = os.path.join(dir_path, "synth.dll")

        if not os.path.exists(lib_path):
            print(f"CRITICAL: synth.dll not found at {lib_path}")
            print("Ensure you compiled it with: g++ -O3 -shared -static -o synth.dll src/synthesizer.cpp")
            sys.exit(1)

        try:
            # winmode=0 is required for Python 3.8+ on Windows to find local dependencies
            if sys.platform == "win32":
                return ctypes.CDLL(lib_path, winmode=0)
            else:
                return ctypes.CDLL(lib_path)
        except Exception as e:
            print(f"CRITICAL: Failed to load C++ Library: {e}")
            sys.exit(1)

    def _setup_functions(self):
        """Maps Python calls to the specific memory addresses in the DLL."""
        # Oscillator Management
        self.lib.create_oscillator.restype = ctypes.c_void_p
        self.lib.delete_oscillator.argtypes = [ctypes.c_void_p]

        # Buffer Generation
        # void generate_samples(Oscillator* osc, float freq, float sample_rate, 
        #                      float volume, int wave_type, float* buffer, int buffer_size)
        self.lib.generate_samples.argtypes = [
            ctypes.c_void_p,                # Oscillator pointer
            ctypes.c_float,                 # freq
            ctypes.c_float,                 # sample_rate
            ctypes.c_float,                 # volume
            ctypes.c_int,                   # wave_type (0=Sine, 1=Sqr, 2=Saw)
            ctypes.POINTER(ctypes.c_float), # output buffer (NumPy pointer)
            ctypes.c_int                    # buffer_size
        ]

    # --- 4.0 HELPER METHODS FOR PLUGINS ---

    def create_oscillator(self):
        """Returns a pointer to a new C++ Phase Accumulator."""
        return self.lib.create_oscillator()

    def delete_oscillator(self, ptr):
        """Frees the memory in C++."""
        if ptr:
            self.lib.delete_oscillator(ptr)

    def fill_buffer(self, osc_ptr, freq, volume, wave_type, buffer):
        """
        Calls the C++ math engine to fill a NumPy array with audio.
        Input 'buffer' must be a float32 NumPy array.
        """
        buffer_size = len(buffer)
        self.lib.generate_samples(
            osc_ptr,
            float(freq),
            self.sample_rate,
            float(volume),
            int(wave_type),
            buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            int(buffer_size)
        )

    def get_buffer(self, freq, volume, wave_type, num_samples):
        """
        Standard 4.0 Helper: Creates a temporary oscillator, 
        generates math, and cleans up immediately.
        """
        # 1. Create a temporary 'voice' in C++
        ptr = self.lib.create_oscillator()
        # 2. Create the NumPy container
        buffer = np.zeros(num_samples, dtype=np.float32)
        # 3. Fill it
        self.lib.generate_samples(
            ptr, float(freq), self.sample_rate, float(volume),
            int(wave_type), buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_float)), int(num_samples)
        )
        # 4. Free C++ memory
        self.lib.delete_oscillator(ptr)
        return buffer

    def cleanup(self):
        """Generic 4.0 shutdown call."""
        print("C++ Bridge: Shutting down.")
        # Currently no global library state to clear, but hook is here for 4.1
        pass
```

## File: audio_engine\manager.py
```python
# Blooper4/audio_engine/manager.py
import pygame
import numpy as np
from audio_engine.bridge import CPPSynthBridge
from audio_engine.plugin_factory import PluginFactory
from constants import SAMPLE_RATE, NUM_TRACKS, TPQN

class AudioManager:
    """
    4.0 AudioManager: A generic signal pipeline.
    Orchestrates the flow from Source -> Modular FX -> Mixer.
    """
    def __init__(self, song_ref):
        self.current_song_ref = song_ref
        self.bridge = CPPSynthBridge(SAMPLE_RATE)
        
        # Every track gets a list of (pygame.Channel, original_note_velocity)
        self.active_channels = {i: [] for i in range(NUM_TRACKS)}
        
        # 4.0 Plugin Loader: Translates strings in the model to logic objects
        self.factory = PluginFactory(self.bridge)
        
        # High polyphony for dense MIDI handling
        pygame.mixer.set_num_channels(64)

    def play_note(self, track_idx, track_model, note_model, bpm):
        # 0. PRE-GATE (Solo/Mute check)
        solo_active = any(t.params.get("solo", False) for t in self.current_song_ref.tracks)
        if track_model.params.get("mute") or (solo_active and not track_model.params.get("solo")):
            return 

        # --- 4.1 WORKSTATION ROUTING ---
        if track_model.mode == "SYNTH":
            # Simple track: Use the track's global source
            engine_id = track_model.source_type
            source_params = track_model.source_params
        else:
            # Sampler track: Find the specific engine assigned to this MIDI pitch
            pad_config = track_model.sampler_map.get(note_model.pitch)
            if not pad_config: return
            engine_id = pad_config["engine"]
            source_params = pad_config["params"]

        # 1. GENERATE SOURCE (Generic)
        source = self.factory.get_source(engine_id)
        if not source: return
        
        # New 4.1 Contract: Plugins must accept a raw params dict
        buffer = source.generate_modular(source_params, note_model, bpm)

        # 2. MODULAR FX LOOP (Processed track-wide after the source)
        for fx in track_model.effects:
            if fx["active"]:
                processor = self.factory.get_effect(fx["type"])
                if processor:
                    buffer = processor.process(buffer, fx["params"])

        # 3. CONVERSION & MIXER APPLICATION
        # Pull Mixer-level params
        track_vol = track_model.params.get("volume", 0.8)
        note_vol_scalar = note_model.velocity / 127.0
        final_gain = track_vol * note_vol_scalar
        pan = track_model.params.get("pan", 0.5)

        # Convert float32 buffer to 16-bit stereo PCM
        pcm_data = (np.clip(buffer, -1.0, 1.0) * 32767 * final_gain).astype(np.int16)
        stereo_pcm = np.ascontiguousarray(np.stack((pcm_data, pcm_data), axis=-1))
        sound = pygame.sndarray.make_sound(stereo_pcm)

        # 4. CHANNEL ASSIGNMENT
        channel = pygame.mixer.find_channel(True) # Force-find if necessary
        if channel:
            # Applying volume/pan hardware-side for smooth real-time fader response
            channel.set_volume(final_gain * (1.0 - pan), final_gain * pan)
            channel.play(sound)
            
            # Record this channel for real-time update() calls (faders/mute/solo)
            self.active_channels[track_idx].append((channel, note_vol_scalar))

    def update(self, song_model):
        """Processes real-time Mixer changes (Faders, Pans, Mutes)."""
        solo_active = any(t.params.get("solo", False) for t in song_model.tracks)
        
        for i, track in enumerate(song_model.tracks):
            # Clean up voices that finished playing
            self.active_channels[i] = [(ch, nv) for ch, nv in self.active_channels[i] if ch.get_busy()]
            
            # Calculate current 'Audibility'
            is_muted = track.params.get("mute", False)
            is_solo_muted = solo_active and not track.params.get("solo", False)
            
            # The 'Master' level for this track right now
            mixer_vol = 0.0 if (is_muted or is_solo_muted) else track.params.get("volume", 0.8)
            pan = track.params.get("pan", 0.5)

            # Update every active voice for this track (allows moving faders mid-note)
            for channel, note_vol_scalar in self.active_channels[i]:
                v = mixer_vol * note_vol_scalar
                channel.set_volume(v * (1.0 - pan), v * pan)
                
                # If muted, kill the channel instantly (stops buffer bleed)
                if mixer_vol <= 0:
                    channel.stop()

    def cleanup(self):
        """Final shutdown of C++ bridge."""
        self.bridge.cleanup()
```

## File: audio_engine\plugin_factory.py
```python
# Blooper4/audio_engine/plugin_factory.py
import importlib
import os
import sys

class PluginFactory:
    """
    The 4.0 Plugin Orchestrator.
    Dynamically loads plugin files and handles the 'Generic Contract'.
    """
    def __init__(self, bridge):
        self.bridge = bridge
        
        # CATEGORIZED REGISTRY
        self.source_registry = {
            "DUAL_OSC": "dual_osc",
            "NOISE_DRUM": "noise_drum",
            "SQUARE_CYMBAL": "square_cymbal"
        }
        self.effect_registry = {
            "EQ": "eq",
            "REVERB": "reverb"
        }
        
        # Combine them for the internal loader
        self.plugin_map = {**self.source_registry, **self.effect_registry}
        
        # Cache for instantiated Audio Processors (one instance per track-type)
        self.processor_cache = {}

    def _get_module(self, plugin_id):
        """Helper to dynamically import the plugin python file."""
        filename = self.plugin_map.get(plugin_id)
        if not filename:
            print(f"ERROR: Plugin ID '{plugin_id}' not found in registry.")
            return None
            
        try:
            # Construct the internal package path
            module_path = f"components.builder_plugins.{filename}"
            
            # Use importlib to load the file
            if module_path in sys.modules:
                # Reload to pick up any changes while the DAW is running
                return importlib.reload(sys.modules[module_path])
            
            return importlib.import_module(module_path)
        except ImportError as e:
            print(f"CRITICAL: Failed to load plugin file '{filename}.py'. Error: {e}")
            return None

    def get_source(self, plugin_id):
        """Returns the Audio logic instance for a Source (Synth/Drum)."""
        if plugin_id in self.processor_cache:
            return self.processor_cache[plugin_id]
            
        module = self._get_module(plugin_id)
        # 4.0 CONTRACT: Every plugin MUST have a class named 'Processor'
        if module and hasattr(module, 'Processor'):
            # Sources receive the C++ bridge for machine-code oscillators
            instance = module.Processor(self.bridge)
            self.processor_cache[plugin_id] = instance
            return instance
        return None

    def get_effect(self, plugin_id):
        """Returns the Audio logic instance for an Effect (EQ/Reverb)."""
        if plugin_id in self.processor_cache:
            return self.processor_cache[plugin_id]
            
        module = self._get_module(plugin_id)
        if module and hasattr(module, 'Processor'):
            # Effects are initialized without a bridge (usually Python math)
            instance = module.Processor()
            self.processor_cache[plugin_id] = instance
            return instance
        return None

    def get_ui_class(self, plugin_id):
        """
        Returns the UI Class (not an instance).
        The BuilderView uses this to create unique UI boxes for each track.
        """
        module = self._get_module(plugin_id)
        # 4.0 CONTRACT: Every plugin MUST have a class named 'UI'
        if module and hasattr(module, 'UI'):
            return module.UI
        return None
```

## File: audio_engine\__init__.py
```python

```

## File: audio_engine\src\synthesizer.cpp
```
#include <cmath>
#include <stdint.h>

#define PI 3.14159265358979323846

extern "C" {
    // Standard Oscillator structure to track the wave's position (phase)
    struct Oscillator {
        double phase;
    };

    // Constructor called by Python bridge
    Oscillator* create_oscillator() {
        return new Oscillator{0.0};
    }

    // Destructor called by Python bridge
    void delete_oscillator(Oscillator* osc) {
        if (osc) delete osc;
    }

    // The Main Math Loop
    // wave_type: 0 = Sine, 1 = Square, 2 = Saw
    void generate_samples(Oscillator* osc, float freq, float sample_rate, float volume, 
                          int wave_type, float* buffer, int buffer_size) {
        
        if (!osc) return;

        double phase_increment = (2.0 * PI * freq) / sample_rate;

        for (int i = 0; i < buffer_size; ++i) {
            float sample = 0.0f;

            if (wave_type == 0) { // SINE
                sample = (float)std::sin(osc->phase);
            } 
            else if (wave_type == 1) { // SQUARE
                sample = (osc->phase < PI) ? 1.0f : -1.0f;
            }
            else if (wave_type == 2) { // SAW
                sample = (float)((osc->phase / PI) - 1.0);
            }

            buffer[i] = sample * volume;

            // Increment and wrap phase (0 to 2*PI)
            osc->phase += phase_increment;
            while (osc->phase >= 2.0 * PI) osc->phase -= 2.0 * PI;
        }
    }
}
```

## File: components\base_element.py
```python
# Blooper4/components/base_element.py
import pygame
import constants 

class BaseUIElement:
    """
    The Universal Parent for all 4.0 Widgets (Toolbars) and Plugins (EQ/Synth).
    Handles spatial awareness, Anchor-based docking, and Scaling.
    """
    def __init__(self, x, y, w, h):
        
        # Base dimensions (the 'unscaled' stock size)
        self.base_rect = pygame.Rect(x, y, w, h)
        # Current dimensions (adjusted for UI_SCALE)
        self.rect = pygame.Rect(x, y, w, h)
        
        self.is_visible = True

        self.plugin_id = "BASE" # Overridden by children (e.g., "EQ", "DUAL_OSC")
        self.title = "Base Module"

        self.anchors = {
            'TL': (x, y),
            'TR': (x + w, y),
            'BL': (x, y + h),
            'BR': (x + w, y + h)
        }

        # --- THE FIX: Register for global release ---
        if self not in constants.ACTIVE_COMPONENTS:
            constants.ACTIVE_COMPONENTS.append(self)

    def update_layout(self, scale):
        """Recalculates the screen rect and anchors based on scale."""
        self.rect.width = int(self.base_rect.width * scale)
        self.rect.height = int(self.base_rect.height * scale)
        
        # Anchors are always screen-absolute coordinates
        self.anchors['TL'] = (self.rect.x, self.rect.y)
        self.anchors['TR'] = (self.rect.right, self.rect.y)
        self.anchors['BL'] = (self.rect.x, self.rect.bottom)
        self.anchors['BR'] = (self.rect.right, self.rect.bottom)

    def dock_to(self, other_element, my_corner='TL', target_corner='TR', offset=(0,0)):
        """
        Anchors this widget to another widget.
        Example: Dock my Top-Left (TL) to your Top-Right (TR).
        """
        target_pos = other_element.anchors.get(target_corner)
        if target_pos:
            self.rect.x = target_pos[0] + offset[0]
            self.rect.y = target_pos[1] + offset[1]
            # Immediately update our own anchors so the next widget can dock to us
            self.update_layout(constants.UI_SCALE)

    def draw_modular_frame(self, screen, font, title, active, scale):
        """
        Standardizes the look of all 300px boxes in the Builder.
        Handles the Power Toggle and Delete X automatically.
        """
        # 1. Background Box
        bg_color = (40, 40, 45) if active else (25, 25, 30)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=int(10 * scale))
        pygame.draw.rect(screen, (70, 70, 80), self.rect, 2, border_radius=int(10 * scale))

        # 2. Title
        title_txt = font.render(title, True, constants.COLOR_ACCENT if active else (100, 100, 105))
        screen.blit(title_txt, (self.rect.x + int(10 * scale), self.rect.y + int(10 * scale)))

        # 3. Power Button (Green/Red Circle)
        p_col = (0, 255, 100) if active else (255, 50, 50)
        p_center = (self.rect.right - int(50 * scale), self.rect.y + int(20 * scale))
        pygame.draw.circle(screen, p_col, p_center, int(8 * scale))

        # 4. Delete Button (X)
        x_txt = font.render("X", True, (200, 200, 200))
        screen.blit(x_txt, (self.rect.right - int(25 * scale), self.rect.y + int(10 * scale)))

    def check_standard_interactions(self, pos, scale):
        """
        Generic handler for the Power and Delete buttons found on every module.
        Returns: 'TOGGLE', 'DELETE', or None.
        """
        # Power Button Hitbox
        p_rect = pygame.Rect(0, 0, 30 * scale, 30 * scale)
        p_rect.center = (self.rect.right - int(50 * scale), self.rect.y + int(20 * scale))
        if p_rect.collidepoint(pos):
            return "TOGGLE"
            
        # Delete Button Hitbox
        d_rect = pygame.Rect(self.rect.right - int(30 * scale), self.rect.y, 30 * scale, 30 * scale)
        if d_rect.collidepoint(pos):
            return "DELETE"
            
        return None

    def global_release(self):
        """
        Universal reset for all sub-components (Sliders, etc).
        Ensures nothing stays 'stuck' to the mouse.
        """
        # To be overridden by children who own Sliders/RadioGroups
        pass
```

## File: components\drum_roll.py
```python
# Blooper4/components/drum_roll.py
import pygame
from constants import *
from components.base_element import BaseUIElement

class DrumRoll(BaseUIElement):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.scroll_x = 0
        self.zoom_x = 0.5
        # FIX: Start scrolled to note 33
        self.scroll_y = (127 - (SAMPLER_DEFAULT_START + 15)) * GRID_HEIGHT
        self.row_h = scale(GRID_HEIGHT * 1.5) # Slightly taller than synth rows 
        self.is_dragging = False
        self.current_note = None

    def update_layout(self, scale_f):
        """Override to update row height when UI_SCALE changes."""
        super().update_layout(scale_f)
        self.row_h = self.rect.height // 19

    def get_coords(self, tick, pitch):
        x = (tick - self.scroll_x) * self.zoom_x + self.rect.x
        y = (DRUM_NOTE_END - pitch) * self.row_h + self.rect.y
        return x, y

    def get_pitch_at(self, mouse_y):
        return DRUM_NOTE_END - int((mouse_y - self.rect.y) / self.row_h)

    def get_tick_at(self, mouse_x):
        return int((mouse_x - self.rect.x) / self.zoom_x + self.scroll_x)

    def draw(self, screen, track, current_tick, font):
        self.update_layout(UI_SCALE)
        
        original_clip = screen.get_clip()
        screen.set_clip(self.rect)

        # 1. Draw Pad Rows
        for p in range(128):
            _, y = self.get_coords(0, p)
            if self.rect.top <= y <= self.rect.bottom:
                pad_cfg = track.sampler_map[p]
                # Default Label + User Override
                base_label = pad_cfg["label"] if pad_cfg["label"] else f"Pad {p}"
                engine_label = f"[{pad_cfg['engine'][:5]}]"
                lbl = font.render(f"{base_label} {engine_label}", True, WHITE)
                screen.blit(lbl, (5, y + 2))

        # 2. Draw Measure Lines
        for t in range(0, 19200, TPQN):
            x = (t - self.scroll_x) * self.zoom_x + self.rect.x
            if x >= self.rect.x:
                color = (70, 70, 80) if t % (TPQN*4) == 0 else (35, 35, 40)
                pygame.draw.line(screen, color, (x, self.rect.top), (x, self.rect.bottom))

        # 3. Draw Notes
        for n in track.notes:
            if DRUM_NOTE_START <= n.pitch <= DRUM_NOTE_END:
                nx, ny = self.get_coords(n.tick, n.pitch)
                nw = n.duration * self.zoom_x
                if nx + nw > self.rect.x:
                    pygame.draw.rect(screen, COLOR_ACCENT, (max(nx, self.rect.x), ny + 2, nw - 1, self.row_h - 4))

        # 4. Playhead
        px = (current_tick - self.scroll_x) * self.zoom_x + self.rect.x
        if px > self.rect.x:
            pygame.draw.line(screen, WHITE, (px, self.rect.top), (px, self.rect.bottom), 1)
            
        screen.set_clip(original_clip)

    def global_release(self):
        self.is_dragging = False
        self.current_note = None
```

## File: components\mixer_panel.py
```python
# Blooper4/components/mixer_panel.py
import pygame
from constants import *
from components.mixer_strip import ChannelStrip
from components.base_element import BaseUIElement

class MixerPanel(BaseUIElement):
    """
    The Horizontal Mixer Widget.
    Contains 16 ChannelStrips and anchors to the bottom of the screen.
    """
    def __init__(self, font):
        # Initial Stock Size: Full width, MIXER_H high, at the bottom
        super().__init__(0, WINDOW_H - MIXER_H, WINDOW_W, MIXER_H)
        self.font = font
        self.strips = [
            ChannelStrip(i, 0, 0, WINDOW_W // 16, MIXER_H) for i in range(16)
        ]

    def draw(self, screen, song, active_idx):
        # Draw the main panel background
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        pygame.draw.line(screen, (50, 50, 60), self.rect.topleft, self.rect.topright, 2)

        # Draw each channel strip
        strip_w = self.rect.width // 16
        for i, strip in enumerate(self.strips):
            # Tell the strip to draw at its calculated horizontal position
            strip.draw(screen, i * strip_w, self.rect.y, song.tracks[i], i == active_idx, self.font, UI_SCALE)

    def handle_event(self, event, song):
        active_track_change = None
        for i, strip in enumerate(self.strips):
            res = strip.handle_event(event, song.tracks[i], UI_SCALE)
            if res == "SELECT":
                active_track_change = i
        return active_track_change
```

## File: components\mixer_strip.py
```python
# Blooper4/components/mixer_strip.py
import pygame
from constants import *
from components.base_element import BaseUIElement

class ChannelStrip(BaseUIElement):
    """
    4.0 Channel Strip: A scalable vertical slice of the mixer.
    Inherits from BaseUIElement to support Anchors and Scaling.
    """
    def __init__(self, index, x, y, w, h):
        super().__init__(x, y, w, h)
        self.idx = index
        # We define logical offsets (unscaled) for internal UI
        # These will be multiplied by the scale factor during draw()
        self.logical_pan_y = 35
        self.logical_fader_y = 60
        self.logical_btns_y = h - 40

    def draw(self, screen, track, is_active, font, scale_f):
        # 1. Update the main container rect based on global scale
        self.update_layout(scale_f)
        
        # 2. Draw Background
        bg_color = (40, 40, 45) if is_active else (25, 25, 30)
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=int(3 * scale_f))
        pygame.draw.rect(screen, (60, 60, 65), self.rect, 1, border_radius=int(3 * scale_f))

        # 3. Track Label
        color = COLOR_ACCENT if is_active else WHITE
        txt_num = font.render(str(track.channel), True, color)
        screen.blit(txt_num, (self.rect.x + int(5 * scale_f), self.rect.y + int(5 * scale_f)))
        
        # 4. Pan Slider (Scalable)
        pan_rect = pygame.Rect(self.rect.x + int(10 * scale_f), 
                               self.rect.y + int(self.logical_pan_y * scale_f), 
                               self.rect.width - int(20 * scale_f), int(8 * scale_f))
        pygame.draw.rect(screen, (10, 10, 10), pan_rect, border_radius=int(4 * scale_f))
        
        pan_val = track.params.get("pan", 0.5)
        handle_x = pan_rect.x + (pan_val * pan_rect.width)
        pygame.draw.rect(screen, WHITE, (handle_x - 2, pan_rect.y - 2, 4, int(12 * scale_f)))

        # 5. Volume Fader (Scalable)
        fader_area = pygame.Rect(self.rect.x + int(self.rect.width // 2 - 5), 
                                 self.rect.y + int(self.logical_fader_y * scale_f), 
                                 int(10 * scale_f), self.rect.height - int(130 * scale_f))
        pygame.draw.rect(screen, (10, 10, 10), fader_area)
        
        vol = track.params.get("volume", 0.8)
        handle_y = fader_area.bottom - (vol * fader_area.height)
        pygame.draw.rect(screen, COLOR_ACCENT, (fader_area.x - int(10 * scale_f), handle_y - 5, int(30 * scale_f), 10), border_radius=2)

        # 6. Mute / Solo Buttons
        btn_w = (self.rect.width // 2) - int(5 * scale_f)
        mute_rect = pygame.Rect(self.rect.x + int(5 * scale_f), self.rect.y + int(self.logical_btns_y * scale_f), btn_w, int(25 * scale_f))
        solo_rect = pygame.Rect(self.rect.x + (self.rect.width // 2), self.rect.y + int(self.logical_btns_y * scale_f), btn_w, int(25 * scale_f))
        
        m_col = RED if track.params.get("mute", False) else (60, 60, 65)
        s_col = (255, 200, 0) if track.params.get("solo", False) else (60, 60, 65)
        
        pygame.draw.rect(screen, m_col, mute_rect, border_radius=3)
        pygame.draw.rect(screen, s_col, solo_rect, border_radius=3)
        
        screen.blit(font.render("M", True, WHITE), (mute_rect.x + int(8 * scale_f), mute_rect.y + 5))
        screen.blit(font.render("S", True, BLACK if track.params.get("solo", False) else WHITE), (solo_rect.x + int(8 * scale_f), solo_rect.y + 5))

    def handle_event(self, event, track, scale_f):
        # We re-calculate hitboxes during event handling to match current scale
        btn_w = (self.rect.width // 2) - int(5 * scale_f)
        mute_rect = pygame.Rect(self.rect.x + int(5 * scale_f), self.rect.y + int(self.logical_btns_y * scale_f), btn_w, int(25 * scale_f))
        solo_rect = pygame.Rect(self.rect.x + (self.rect.width // 2), self.rect.y + int(self.logical_btns_y * scale_f), btn_w, int(25 * scale_f))
        pan_rect = pygame.Rect(self.rect.x + int(10 * scale_f), self.rect.y + int(self.logical_pan_y * scale_f), self.rect.width - int(20 * scale_f), int(15 * scale_f))
        fader_area = pygame.Rect(self.rect.x + int(self.rect.width // 2 - 15), self.rect.y + int(self.logical_fader_y * scale_f), int(30 * scale_f), self.rect.height - int(130 * scale_f))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if mute_rect.collidepoint(event.pos):
                track.params["mute"] = not track.params.get("mute", False)
                return "UPDATE"
            if solo_rect.collidepoint(event.pos):
                track.params["solo"] = not track.params.get("solo", False)
                return "UPDATE"
            if self.rect.collidepoint(event.pos) and not fader_area.collidepoint(event.pos) and not pan_rect.collidepoint(event.pos):
                return "SELECT"

        if pygame.mouse.get_pressed()[0]:
            m_pos = pygame.mouse.get_pos()
            if fader_area.collidepoint(m_pos):
                rel_y = fader_area.bottom - m_pos[1]
                track.params["volume"] = max(0.0, min(1.0, rel_y / fader_area.height))
                return "UPDATE"
            if pan_rect.collidepoint(m_pos):
                rel_x = m_pos[0] - pan_rect.x
                track.params["pan"] = max(0.0, min(1.0, rel_x / pan_rect.width))
                return "UPDATE"
        return None
```

## File: components\note_type_toolbar.py
```python
# Blooper4/components/note_type_toolbar.py
import pygame
from constants import *
from components.base_element import BaseUIElement
from ui_components import RadioGroup, Slider, Button

class NoteTypeToolbar(BaseUIElement):
    def __init__(self, x, y, w, h, font):
        super().__init__(x, y, w, h)
        self.font = font
        
        # We initialize sub-components with 0,0; they will be moved during draw()
        self.quant_menu = RadioGroup(0, 0, QUANT_LABELS, font, cols=4)
        self.btn_add_bar = Button(0, 0, 60, 22, "+ BAR", (60, 60, 70))
        self.btn_rem_bar = Button(0, 0, 60, 22, "- BAR", (60, 60, 70))
        self.vel_slider = Slider(0, 0, 150, 10, 1, 127, 100, "VELOCITY")
        
        self.debug_log = ["4.0 Editor Ready"]

    def log(self, message):
        self.debug_log.append(message)
        if len(self.debug_log) > 4: self.debug_log.pop(0)

    def draw(self, screen, song):
        # 1. Update layout based on current UI_SCALE
        self.update_layout(UI_SCALE)
        
        # 2. Draw Background
        pygame.draw.rect(screen, COLOR_PANEL, self.rect)
        pygame.draw.rect(screen, (60, 60, 70), self.rect, 1)

        # 3. Position and Draw Sub-components (Relative to self.rect)
        self.quant_menu.move_to(self.rect.x + scale(10), self.rect.y + scale(10))
        self.quant_menu.draw(screen, self.font)

        self.btn_add_bar.move_to(self.rect.x + scale(300), self.rect.y + scale(10))
        self.btn_rem_bar.move_to(self.rect.x + scale(365), self.rect.y + scale(10))
        self.btn_rem_bar.enabled = (song.length_ticks > TPQN * 4)
        self.btn_add_bar.draw(screen, self.font)
        self.btn_rem_bar.draw(screen, self.font)

        self.vel_slider.move_to(self.rect.x + scale(450), self.rect.y + scale(25))
        self.vel_slider.draw(screen, self.font)

        # 4. Draw Debug Window
        debug_rect = pygame.Rect(self.rect.right - scale(260), self.rect.y + scale(5), scale(250), scale(50))
        pygame.draw.rect(screen, (5, 5, 10), debug_rect, border_radius=scale(3))
        for i, msg in enumerate(self.debug_log):
            txt = self.font.render(f"> {msg}", True, (0, 255, 100))
            screen.blit(txt, (debug_rect.x + scale(5), debug_rect.y + scale(5) + (i * scale(11))))

    def handle_event(self, event, song):
        q_sel = self.quant_menu.handle_event(event)
        v_val = self.vel_slider.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_add_bar.is_clicked(event.pos):
                song.length_ticks += TPQN * 4
                self.log("Added Bar")
            if self.btn_rem_bar.is_clicked(event.pos):
                if song.length_ticks > TPQN * 4:
                    song.length_ticks -= TPQN * 4
                    self.log("Removed Bar")

        return {"quantize": self.quant_menu.selected, "velocity": self.vel_slider.val}

    def global_release(self):
        """Universal fix for sticky sliders in this component."""
        self.vel_slider.grabbed = False
```

## File: components\piano_roll.py
```python
# Blooper4/components/piano_roll.py
import pygame
from constants import *
from components.base_element import BaseUIElement

class PianoRoll(BaseUIElement):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.scroll_x = 0
        self.scroll_y = 60 * scale(GRID_HEIGHT)
        self.zoom_x = 0.5
        self.is_dragging = False
        self.current_note = None

    def get_coords(self, tick, pitch):
        # Math is now relative to self.rect.x/y
        x = (tick - self.scroll_x) * self.zoom_x + self.rect.x
        y = (127 - pitch) * scale(GRID_HEIGHT) - self.scroll_y + self.rect.y
        return x, y

    def get_pitch_at(self, mouse_y):
        relative_y = mouse_y - self.rect.y + self.scroll_y
        return 127 - int(relative_y / scale(GRID_HEIGHT))

    def get_tick_at(self, mouse_x):
        relative_x = mouse_x - self.rect.x
        return int(relative_x / self.zoom_x + self.scroll_x)

    def draw(self, screen, track, current_tick, font):
        self.update_layout(UI_SCALE)
        
        # Clipping: Grid only draws inside its assigned rectangle
        original_clip = screen.get_clip()
        screen.set_clip(self.rect)

        # 1. Background Grid
        row_h = scale(GRID_HEIGHT)
        for p in range(128):
            _, y = self.get_coords(0, p)
            if self.rect.top - row_h <= y <= self.rect.bottom:
                bg = (20, 20, 25)
                if (p % 12) in [1, 3, 6, 8, 10]: bg = (15, 15, 18)
                pygame.draw.rect(screen, bg, (self.rect.x, y, self.rect.width, row_h))
                pygame.draw.line(screen, (30, 30, 35), (self.rect.x, y), (self.rect.right, y))

        # 2. Measure Lines
        for t in range(0, 19200, TPQN):
            x = (t - self.scroll_x) * self.zoom_x + self.rect.x
            if x >= self.rect.x:
                color = (70, 70, 80) if t % (TPQN*4) == 0 else (35, 35, 40)
                pygame.draw.line(screen, color, (x, self.rect.top), (x, self.rect.bottom))

        # 3. Draw Notes
        for n in track.notes:
            nx, ny = self.get_coords(n.tick, n.pitch)
            nw = n.duration * self.zoom_x
            if nx + nw > self.rect.x:
                color = OCTAVE_COLORS[min(n.pitch // 12, len(OCTAVE_COLORS)-1)]
                pygame.draw.rect(screen, color, (max(nx, self.rect.x), ny+1, nw-1, row_h-2))

        # 4. Playhead
        px = (current_tick - self.scroll_x) * self.zoom_x + self.rect.x
        if px > self.rect.x:
            pygame.draw.line(screen, COLOR_ACCENT, (px, self.rect.top), (px, self.rect.bottom), 2)
            
        screen.set_clip(original_clip)

    def global_release(self):
        self.is_dragging = False
        self.current_note = None
```

## File: components\__init__.py
```python

```

## File: components\builder\mode_toggle.py
```python
"""Master toggle for switching between PIANO ROLL and SAMPLE PADS modes."""

import pygame
from components.base_element import BaseUIElement
from constants import scale, UI_SCALE, COLOR_ACCENT, COLOR_PANEL

class ModeToggleUI(BaseUIElement):
    """Radio button toggle: [PIANO ROLL | SAMPLE PADS]"""

    def __init__(self, x, y):
        super().__init__(x, y, scale(280), scale(40))
        self.font = pygame.font.Font(None, int(24 * UI_SCALE))
        self.piano_rect = None
        self.pads_rect = None

    def move_to(self, x, y):
        """Position the toggle and update anchors for docking system."""
        self.rect.x = x
        self.rect.y = y
        # Update anchors so other elements can dock to this toggle
        self.anchors['TL'] = (self.rect.x, self.rect.y)
        self.anchors['TR'] = (self.rect.right, self.rect.y)
        self.anchors['BL'] = (self.rect.x, self.rect.bottom)
        self.anchors['BR'] = (self.rect.right, self.rect.bottom)

    def draw(self, screen, track_model):
        """Draw toggle with active mode highlighted."""
        # Background frame
        pygame.draw.rect(screen, COLOR_PANEL, self.rect, border_radius=scale(5))

        # Define button areas
        self.piano_rect = pygame.Rect(self.rect.x + scale(5), self.rect.y + scale(5),
                                       scale(135), scale(30))
        self.pads_rect = pygame.Rect(self.rect.x + scale(145), self.rect.y + scale(5),
                                      scale(130), scale(30))

        # Highlight active mode
        if track_model.mode == "SYNTH":
            pygame.draw.rect(screen, COLOR_ACCENT, self.piano_rect, border_radius=scale(3))
            piano_color, pads_color = (0, 0, 0), (200, 200, 200)
        else:  # SAMPLER mode
            pygame.draw.rect(screen, COLOR_ACCENT, self.pads_rect, border_radius=scale(3))
            piano_color, pads_color = (200, 200, 200), (0, 0, 0)

        # Draw text
        piano_surf = self.font.render("PIANO ROLL", True, piano_color)
        pads_surf = self.font.render("SAMPLE PADS", True, pads_color)

        screen.blit(piano_surf, (self.piano_rect.centerx - piano_surf.get_width()//2,
                                  self.piano_rect.centery - piano_surf.get_height()//2))
        screen.blit(pads_surf, (self.pads_rect.centerx - pads_surf.get_width()//2,
                                self.pads_rect.centery - pads_surf.get_height()//2))

    def handle_event(self, event, track_model):
        """Toggle mode on click."""
        if self.piano_rect is None or self.pads_rect is None:
            return None

        if hasattr(event, 'pos'):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.piano_rect.collidepoint(event.pos):
                    if track_model.mode != "SYNTH":
                        # Switch to PIANO ROLL mode
                        # Restore last synth used in SYNTH mode
                        track_model.mode = "SYNTH"
                        track_model.is_drum = False
                        if hasattr(track_model, 'last_synth_source'):
                            track_model.source_type = track_model.last_synth_source
                        # else: keeps current source_type
                        return "MODE_CHANGED"

                elif self.pads_rect.collidepoint(event.pos):
                    if track_model.mode != "SAMPLER":
                        # Switch to SAMPLE PADS mode
                        # Save current synth before switching
                        track_model.last_synth_source = track_model.source_type
                        track_model.mode = "SAMPLER"
                        track_model.is_drum = True
                        return "MODE_CHANGED"
        return None

```

## File: components\builder\piano_roll_settings.py
```python
"""Piano roll scale settings: Chromatic / Modal / Microtonal selector."""

import pygame
from components.base_element import BaseUIElement
from constants import *

class PianoRollSettingsUI(BaseUIElement):
    """Scale mode selector for piano roll. Matches sampler_brain style."""

    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400)  # Same size as sampler_brain
        self.font = font
        self.plugin_id = "PIANO_ROLL_SETTINGS"
        self.title = "PIANO ROLL SETTINGS"
        self.chromatic_rect = None
        self.modal_rect = None
        self.microtonal_rect = None

    def draw(self, screen, track, x, y, scale_f):
        """Draw scale mode selector with modular frame."""
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, True, scale_f)

        # Label
        label_txt = "SCALE MODE:"
        screen.blit(self.font.render(label_txt, True, WHITE),
                    (self.rect.x + scale(20), self.rect.y + scale(45)))

        # Define button areas (3 buttons stacked vertically)
        button_width = scale(260)
        button_height = scale(50)
        start_y = self.rect.y + scale(80)

        self.chromatic_rect = pygame.Rect(
            self.rect.x + scale(20), start_y,
            button_width, button_height
        )
        self.modal_rect = pygame.Rect(
            self.rect.x + scale(20), start_y + scale(60),
            button_width, button_height
        )
        self.microtonal_rect = pygame.Rect(
            self.rect.x + scale(20), start_y + scale(120),
            button_width, button_height
        )

        # Get current scale mode (default to CHROMATIC)
        scale_mode = getattr(track, 'piano_roll_scale', 'CHROMATIC')

        # Draw buttons with highlight for active mode
        buttons = [
            (self.chromatic_rect, "CHROMATIC", scale_mode == 'CHROMATIC'),
            (self.modal_rect, "MODAL", scale_mode == 'MODAL'),
            (self.microtonal_rect, "MICROTONAL", scale_mode == 'MICROTONAL')
        ]

        for rect, label, is_active in buttons:
            color = COLOR_ACCENT if is_active else (50, 50, 55)
            pygame.draw.rect(screen, color, rect, border_radius=scale(5))
            text_color = (0, 0, 0) if is_active else WHITE
            txt_surf = self.font.render(label, True, text_color)
            screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2,
                                   rect.centery - txt_surf.get_height()//2))

    def handle_event(self, event, track_model):
        """Handle scale mode selection."""
        if self.chromatic_rect is None:
            return None

        if hasattr(event, 'pos'):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.chromatic_rect.collidepoint(event.pos):
                    track_model.piano_roll_scale = 'CHROMATIC'
                    return "SCALE_CHANGED"
                elif self.modal_rect.collidepoint(event.pos):
                    track_model.piano_roll_scale = 'MODAL'
                    return "SCALE_CHANGED"
                elif self.microtonal_rect.collidepoint(event.pos):
                    track_model.piano_roll_scale = 'MICROTONAL'
                    return "SCALE_CHANGED"
        return None

```

## File: components\builder\sampler_brain.py
```python
# Blooper4/components/builder/sampler_brain.py
import pygame
from constants import *
from components.base_element import BaseUIElement
from ui_components import Button

class SamplerBrainUI(BaseUIElement):
    """
    The 'Router' for Sampler Tracks. 
    Displays a 16-pad grid and handles range shifting.
    """
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400)
        self.font = font
        self.plugin_id = "SAMPLER_BRAIN"
        self.title = "SAMPLER BRAIN"
        
        # Navigation Buttons
        self.btn_prev = Button(0, 0, 40, 25, "<", (60, 60, 70))
        self.btn_next = Button(0, 0, 40, 25, ">", (60, 60, 70))

    def _get_pad_rect(self, n, track, scale_f):
        # Calculate grid position (4x4) relative to current base note
        local_idx = n - track.sampler_base_note
        col, row = local_idx % 4, local_idx // 4
        px = self.rect.x + scale(20) + col * scale(65)
        # FIX: Adjust Y offset to match visual rendering (was scale(80), too high by ~80px)
        py = self.rect.y + scale(160) + row * scale(55)
        return pygame.Rect(px, py, scale(60), scale(50))

    def draw(self, screen, track, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, True, scale_f)

        # Draw Range Controls
        range_txt = f"RANGE: {track.sampler_base_note}-{track.sampler_base_note+15}"
        screen.blit(self.font.render(range_txt, True, WHITE), (self.rect.x + scale(20), self.rect.y + scale(45)))
        
        self.btn_prev.move_to(self.rect.right - scale(100), self.rect.y + scale(40), scale(40), scale(25))
        self.btn_next.move_to(self.rect.right - scale(50), self.rect.y + scale(40), scale(40), scale(25))
        self.btn_prev.draw(screen, self.font)
        self.btn_next.draw(screen, self.font)

        # Draw the 16-pad selection grid
        for n in range(track.sampler_base_note, track.sampler_base_note + 16):
            if n > 127: break
            p_rect = self._get_pad_rect(n, track, scale_f)
            
            # Highlight pad currently being edited in the rack
            is_active = (track.active_pad == n)
            color = COLOR_ACCENT if is_active else (50, 50, 55)
            pygame.draw.rect(screen, color, p_rect, border_radius=scale(5))
            
            # Label
            screen.blit(self.font.render(str(n), True, WHITE), (p_rect.x + 5, p_rect.y + 5))
            pad_cfg = track.sampler_map.get(n, {"engine": "NONE"})
            # Display truncated engine name (e.g., 'NOIS')
            eng_name = pad_cfg["engine"][:4]
            screen.blit(self.font.render(eng_name, True, GRAY), (p_rect.x + 5, p_rect.y + 25))

    def handle_event(self, event, track):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Shift 16 notes down/up
            if self.btn_prev.is_clicked(event.pos):
                track.sampler_base_note = max(0, track.sampler_base_note - 16)
                return
            if self.btn_next.is_clicked(event.pos):
                track.sampler_base_note = min(112, track.sampler_base_note + 16)
                return

            # Click a pad to "Focus" the rack on that specific engine
            for n in range(track.sampler_base_note, track.sampler_base_note + 16):
                if n > 127: break
                if self._get_pad_rect(n, track, UI_SCALE).collidepoint(event.pos):
                    track.active_pad = n
                    return
```

## File: components\builder\__init__.py
```python

```

## File: components\builder_plugins\dual_osc.py
```python
# Blooper4/components/builder_plugins/dual_osc.py
import pygame
import numpy as np
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import RadioGroup, Slider, Button

# =============================================================================
# 1. THE AUDIO PROCESSOR (The Math)
# =============================================================================
class Processor(BaseProcessor):
    """
    4.0 Dual Oscillator Engine.
    Handles the high-speed math using the C++ Bridge.
    """
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        # Map strings to the integer types expected by the C++ DLL
        self.wave_map = {"SINE": 0, "SQUARE": 1, "SAW": 2, "NONE": 3}

    def generate(self, track_model, note_model, bpm):
        """Standard generate call: Returns a float32 audio buffer."""
        # A. Calculate timing
        duration_sec = (note_model.duration / TPQN) * (60 / bpm)
        num_samples = int(max(0.01, duration_sec) * SAMPLE_RATE)
        
        # B. Calculate fundamental frequency
        freq = 440.0 * (2.0 ** ((note_model.pitch - 69) / 12.0))
        
        # C. Generate Oscillator 1
        o1_type = self.wave_map.get(track_model.source_params.get("osc1_type", "SAW"), 2)
        # We start with a base buffer of 0.5 volume to allow headroom for mixing
        buffer = self.bridge.get_buffer(freq, 0.5, o1_type, num_samples) if o1_type != 3 else np.zeros(num_samples, dtype=np.float32)
        
        # D. Generate Oscillator 2 (with Detune)
        o2_type = self.wave_map.get(track_model.source_params.get("osc2_type", "SINE"), 0)
        if o2_type != 3:
            detune_cents = track_model.source_params.get("osc2_detune", 10)
            detune_factor = 2.0 ** (detune_cents / 1200.0)
            # Mix Osc 2 into the existing buffer
            buffer += self.bridge.get_buffer(freq * detune_factor, 0.5, o2_type, num_samples)
            
        return buffer

    def generate_modular(self, params, note, bpm):
        """Helper to allow Sampler routing to reuse existing synth math."""
        # Create a tiny temporary object that 'fakes' a track
        class MockTrack: pass
        mock = MockTrack()
        mock.source_params = params
        mock.drum_pads = {note.pitch: params}
        return self.generate(mock, note, bpm)

# =============================================================================
# 2. THE UI COMPONENT (The Face)
# =============================================================================
class UI(BaseUIElement):
    """
    4.0 Dual Oscillator Interface.
    Inherits anchors and scaling from BaseUIElement.
    """
    def __init__(self, x, y, font):
        # Standard 300x400 module box size
        super().__init__(x, y, 300, 400)
        self.font = font
        self.plugin_id = "DUAL_OSC" # ADD THIS
        self.title = "DUAL OSCILLATOR"
        self.active = True
        
        wave_options = ["SINE", "SQUARE", "SAW", "NONE"]
        self.osc1_sel = RadioGroup(0, 0, wave_options, font, cols=2)
        self.osc2_sel = RadioGroup(0, 0, wave_options, font, cols=2)
        self.detune_slider = Slider(0, 0, 260, 10, 0, 100, 10, "OSC 2 DETUNE")

    def draw(self, screen, track, x_offset, y_offset, scale_f): # Accepts 'track'
        """Standard draw call: x_offset and y_offset provided by the Rack container."""
        # 1. Position and scale the main module box
        params = track.source_params # Pull params here
        self.rect.x = x_offset
        self.rect.y = y_offset
        self.update_layout(scale_f)

        # 2. Draw the 'Inherited' Frame (Standard 4.0 look)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)

        # 3. Position and update internal widgets (scaled)
        self.osc1_sel.move_to(self.rect.x + scale(15), self.rect.y + scale(60))
        self.osc2_sel.move_to(self.rect.x + scale(15), self.rect.y + scale(160))
        self.detune_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(260))

        # 4. Sync visual state with the data model
        self.osc1_sel.selected = params.get("osc1_type", "SAW")
        self.osc2_sel.selected = params.get("osc2_type", "SINE")
        self.detune_slider.val = params.get("osc2_detune", 10)

        # 5. Render
        screen.blit(self.font.render("OSCILLATOR 1", True, WHITE), (self.rect.x + scale(15), self.rect.y + scale(40)))
        self.osc1_sel.draw(screen, self.font)

        screen.blit(self.font.render("OSCILLATOR 2", True, WHITE), (self.rect.x + scale(15), self.rect.y + scale(140)))
        self.osc2_sel.draw(screen, self.font)

        self.detune_slider.draw(screen, self.font)

    def handle_event(self, event, track_model):
        """Standard 4.0 event routing."""
        # 1. Sync internal component positions BEFORE checking hitboxes
        # This ensures interactions work while scrolling
        self.osc1_sel.move_to(self.rect.x + scale(15), self.rect.y + scale(60))
        self.osc2_sel.move_to(self.rect.x + scale(15), self.rect.y + scale(160))
        self.detune_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(260), scale(260), scale(15))

        # 2. Handle frame interactions
        if hasattr(event, 'pos'):
            # Use parent logic for Power and Delete buttons
            action = self.check_standard_interactions(event.pos, UI_SCALE)
            if action == "TOGGLE":
                self.active = not self.active
                return

        # 3. Route events to sub-components
        o1 = self.osc1_sel.handle_event(event)
        if o1: track_model.source_params["osc1_type"] = o1

        o2 = self.osc2_sel.handle_event(event)
        if o2: track_model.source_params["osc2_type"] = o2

        d_val = self.detune_slider.handle_event(event)
        if d_val is not None:
            track_model.source_params["osc2_detune"] = d_val

    def global_release(self):
        """Ensures the detune slider lets go of the mouse."""
        self.detune_slider.grabbed = False
```

## File: components\builder_plugins\eq.py
```python
# Blooper4/components/builder_plugins/eq.py
import pygame
import numpy as np
from scipy.signal import butter, lfilter
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider

class Processor(BaseProcessor):
    def process(self, data, params):
        freqs = [60, 150, 400, 1000, 2400, 5000, 10000, 16000]
        output = np.zeros_like(data)
        nyq = 0.5 * SAMPLE_RATE
        for i, center in enumerate(freqs):
            gain = params.get(f"band_{i}", 1.0)
            if gain == 1.0: continue
            low, high = center * 0.5, min(center * 1.5, nyq * 0.95)
            b, a = butter(1, [low/nyq, high/nyq], btype='band')
            output += lfilter(b, a, data) * gain
        return output if np.any(output) else data

class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400)
        self.font, self.title = font, "8-BAND EQ"
        self.active = True
        self.sliders = [Slider(0, 0, 20, 140, 0, 2, 1, "", vertical=True) for _ in range(8)]
        self.labels = ["60", "150", "400", "1k", "2k", "5k", "10k", "16k"]

    def draw(self, screen, fx_data, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)
        
        for i, s in enumerate(self.sliders):
            s.move_to(self.rect.x + int(25 * scale_f + i * 32 * scale_f), self.rect.y + int(60 * scale_f), int(20 * scale_f), int(140 * scale_f))
            s.val = fx_data["params"].get(f"band_{i}", 1.0)
            s.draw(screen, self.font)
            lbl = self.font.render(self.labels[i], True, (100, 100, 110))
            screen.blit(lbl, (s.rect.x, s.rect.bottom + 5))

    def handle_event(self, event, fx_data):
        if hasattr(event, 'pos'):
            action = self.check_standard_interactions(event.pos, UI_SCALE)
            if action == "TOGGLE": self.active = not self.active
            if action == "DELETE": return "DELETE"

        for i, s in enumerate(self.sliders):
            val = s.handle_event(event)
            if val is not None: fx_data["params"][f"band_{i}"] = val
        return None

    def global_release(self):
        for s in self.sliders: s.grabbed = False
```

## File: components\builder_plugins\noise_drum.py
```python
# Blooper4/components/builder_plugins/noise_drum.py
import pygame
import numpy as np
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider, Button, RadioGroup

# =============================================================================
# 1. THE AUDIO PROCESSOR (Deeper Spectral Math)
# =============================================================================
class Processor(BaseProcessor):
    def __init__(self, bridge=None):
        super().__init__()
        self.drum_cache = {}

    def _generate_colored_noise(self, num_samples, noise_color):
        white = np.random.uniform(-1, 1, num_samples).astype(np.float32)
        if noise_color == "WHITE":
            return white
        
        elif noise_color == "PINK":
            # Better Pink noise: -3dB/octave slope
            # Using a more aggressive FIR filter for short durations
            from scipy.signal import butter, lfilter
            # A low-pass at a mid-high frequency creates a better 'pink' feel for drums
            b, a = butter(1, 0.1, btype='low') 
            pink = lfilter(b, a, white)
            return pink / np.max(np.abs(pink)) if np.max(np.abs(pink)) > 0 else pink

        elif noise_color == "BROWN":
            # Brown noise: -6dB/octave (Very deep)
            # True integration creates the 'thunder' sound
            brown = np.cumsum(white)
            # High-pass at 20Hz to remove DC offset (prevents speaker thumps)
            from scipy.signal import butter, lfilter
            b, a = butter(1, 0.001, btype='high')
            brown = lfilter(b, a, brown)
            return brown / np.max(np.abs(brown)) if np.max(np.abs(brown)) > 0 else brown
            
        return white

    def generate(self, track, note, bpm):
        pad = track.drum_pads.get(note.pitch, {"type": "DRUM", "pitch": 60, "length": 0.3, "color": "WHITE", "gain": 1.0})
        
        n_color = pad.get("color", "WHITE")
        n_gain = pad.get("gain", 1.0)
        cache_key = (note.pitch, pad["type"], round(pad["pitch"], 1), round(pad["length"], 2), n_color, n_gain)
        if cache_key in self.drum_cache: return self.drum_cache[cache_key]
        
        dur = pad.get("length", 0.3)
        num_s = int(dur * SAMPLE_RATE)
        t = np.linspace(0, dur, num_s, False)

        noise = self._generate_colored_noise(num_s, n_color)

        if pad["type"] == "DRUM":
            # KICK: Pitch sweep (400Hz down to slider val)
            f_start, f_end = pad["pitch"] * 4, max(20, pad["pitch"])
            freq_env = np.geomspace(f_start, f_end, num_s)
            wave = np.sin(2 * np.pi * freq_env * t)
            # Add 'beater' noise only at the very start (first 10ms)
            click_env = np.exp(-150 * t)
            final_wave = (wave * 0.95) + (noise * 0.2 * click_env)
            final_wave *= np.exp(-12 * t / dur)
            
        elif pad["type"] == "SNARE":
            # SNARE: Body tone + snapping noise
            tone = np.sin(2 * np.pi * pad["pitch"] * t) * np.exp(-40 * t / dur)
            # Snare needs more high frequencies, so we bias noise slightly
            final_wave = (noise * np.exp(-18 * t / dur)) + (tone * 0.5)
            
        else: # CYMBAL
            # CYMBAL: Just noise with high-pass iterations
            iters = int(max(1, pad["pitch"] / 20))
            for _ in range(iters):
                noise = np.diff(noise, prepend=0)
            if np.max(np.abs(noise)) > 0: noise /= np.max(np.abs(noise))
            final_wave = noise * np.exp(-30 * t / dur)

        final_wave *= n_gain
        self.drum_cache[cache_key] = final_wave
        return final_wave

    

    def generate_modular(self, params, note, bpm):
        """Helper to allow Sampler routing to reuse existing synth math."""
        # Create a tiny temporary object that 'fakes' a track
        class MockTrack: pass
        mock = MockTrack()
        mock.source_params = params
        mock.drum_pads = {note.pitch: params}
        return self.generate(mock, note, bpm)
        
# =============================================================================
# 2. THE UI COMPONENT (Compacted Layout)
# =============================================================================
class UI(BaseUIElement):
    def __init__(self, x, y, font):
        # Increased box size to hold all controls
        super().__init__(x, y, 300, 500) 
        self.font = font
        self.plugin_id = "NOISE_DRUM"
        self.title = "NOISE DRUM"
        self.active = True
        self.selected_pad = 36
        
        # UI Elements
        self.pitch_slider = Slider(0, 0, 260, 10, 1, 500, 60, "PITCH / HPF")
        self.len_slider = Slider(0, 0, 260, 10, 0.05, 1.5, 0.3, "LENGTH")
        self.gain_slider = Slider(0, 0, 260, 10, 0, 2.0, 1.0, "GAIN")
        
        # Radio Groups
        self.color_sel = RadioGroup(0, 0, ["WHITE", "PINK", "BROWN"], font, cols=3)
        self.type_sel = RadioGroup(0, 0, ["DRUM", "SNARE", "CYMBAL"], font, cols=3)

    def _get_pad_rect(self, n, scale_f):
        col, row = (n - 34) % 4, (n - 34) // 4
        px = self.rect.x + int(20 * scale_f) + col * int(65 * scale_f)
        py = self.rect.y + int(50 * scale_f) + row * int(45 * scale_f)
        return pygame.Rect(px, py, int(60 * scale_f), int(40 * scale_f))

    def draw(self, screen, track, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)

        # 1. Pad Grid (Rows 0-4)
        for n in range(DRUM_NOTE_START, DRUM_NOTE_END + 1):
            p_rect = self._get_pad_rect(n, scale_f)
            color = COLOR_ACCENT if self.selected_pad == n else (50, 50, 55)
            pygame.draw.rect(screen, color, p_rect, border_radius=scale(5))
            screen.blit(self.font.render(str(n), True, WHITE), (p_rect.x + 5, p_rect.y + 10))

        # 2. Controls (Tightly stacked starting at y+270)
        pad = track.drum_pads.get(self.selected_pad, {"type": "DRUM", "pitch": 60, "length": 0.3, "color": "WHITE", "gain": 1.0})
        
        self.pitch_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(275), scale(260), scale(12))
        self.len_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(320), scale(260), scale(12))
        self.gain_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(365), scale(260), scale(12))
        
        # Radio groups at the bottom
        self.color_sel.move_to(self.rect.x + scale(10), self.rect.y + scale(400))
        self.type_sel.move_to(self.rect.x + scale(10), self.rect.y + scale(445))
        
        # Sync and Render
        self.pitch_slider.val = pad["pitch"]
        self.len_slider.val = pad["length"]
        self.gain_slider.val = pad.get("gain", 1.0)
        self.color_sel.selected = pad.get("color", "WHITE")
        self.type_sel.selected = pad["type"]
        
        self.pitch_slider.draw(screen, self.font)
        self.len_slider.draw(screen, self.font)
        self.gain_slider.draw(screen, self.font)
        self.color_sel.draw(screen, self.font)
        self.type_sel.draw(screen, self.font)

    def handle_event(self, event, track_model):
        # Update hitboxes for scrolling/scaling
        self.pitch_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(275), scale(260), scale(12))
        self.len_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(320), scale(260), scale(12))
        self.gain_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(365), scale(260), scale(12))
        self.color_sel.move_to(self.rect.x + scale(10), self.rect.y + scale(400))
        self.type_sel.move_to(self.rect.x + scale(10), self.rect.y + scale(445))

        if hasattr(event, 'pos'):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check Pad Grid
                for n in range(DRUM_NOTE_START, DRUM_NOTE_END + 1):
                    if self._get_pad_rect(n, UI_SCALE).collidepoint(event.pos):
                        self.selected_pad = n
                        return

            # Radio Checks
            c = self.color_sel.handle_event(event)
            if c: track_model.drum_pads[self.selected_pad]["color"] = c
            t = self.type_sel.handle_event(event)
            if t: track_model.drum_pads[self.selected_pad]["type"] = t

        # Sliders
        p = self.pitch_slider.handle_event(event)
        if p is not None: track_model.drum_pads[self.selected_pad]["pitch"] = p
        l = self.len_slider.handle_event(event)
        if l is not None: track_model.drum_pads[self.selected_pad]["length"] = l
        g = self.gain_slider.handle_event(event)
        if g is not None: track_model.drum_pads[self.selected_pad]["gain"] = g

    def global_release(self):
        self.pitch_slider.grabbed = False
        self.len_slider.grabbed = False
        self.gain_slider.grabbed = False
```

## File: components\builder_plugins\reverb.py
```python
# Blooper4/components/builder_plugins/reverb.py
import pygame
import numpy as np
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider

class Processor(BaseProcessor):
    def process(self, data, params):
        mix, size = params.get("mix", 0.1), params.get("size", 0.5)
        delay_times = [0.029, 0.037, 0.043, 0.047]
        reverb_out = np.zeros_like(data)
        for d in delay_times:
            d_samples = int(d * size * SAMPLE_RATE)
            if d_samples >= len(data): continue
            temp = np.zeros_like(data)
            temp[d_samples:] = data[:-d_samples] * (0.4 + mix * 0.4)
            reverb_out += temp
        return (data * (1.0 - mix)) + (reverb_out / 4 * mix)

class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400)
        self.font, self.title = font, "REVERB"
        self.active = True
        self.mix_slider = Slider(0, 0, 240, 15, 0, 1, 0.1, "WET MIX")
        self.size_slider = Slider(0, 0, 240, 15, 0, 1, 0.5, "ROOM SIZE")

    def draw(self, screen, fx_data, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)
        
        self.mix_slider.move_to(self.rect.x + int(30 * scale_f), self.rect.y + int(80 * scale_f), int(240 * scale_f), int(15 * scale_f))
        self.size_slider.move_to(self.rect.x + int(30 * scale_f), self.rect.y + int(150 * scale_f), int(240 * scale_f), int(15 * scale_f))
        
        self.mix_slider.val = fx_data["params"].get("mix", 0.1)
        self.size_slider.val = fx_data["params"].get("size", 0.5)
        
        self.mix_slider.draw(screen, self.font)
        self.size_slider.draw(screen, self.font)

    def handle_event(self, event, fx_data):
        if hasattr(event, 'pos'):
            action = self.check_standard_interactions(event.pos, UI_SCALE)
            if action == "TOGGLE": self.active = not self.active
            if action == "DELETE": return "DELETE"

        m = self.mix_slider.handle_event(event)
        if m is not None: fx_data["params"]["mix"] = m
        s = self.size_slider.handle_event(event)
        if s is not None: fx_data["params"]["size"] = s
        return None

    def global_release(self):
        self.mix_slider.grabbed = False
        self.size_slider.grabbed = False
```

## File: components\builder_plugins\square_cymbal.py
```python
# Blooper4/components/builder_plugins/square_cymbal.py
import pygame
import numpy as np
from scipy.signal import butter, lfilter
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider, Button

# =============================================================================
# 1. THE AUDIO PROCESSOR (808-Style Metallic Math)
# =============================================================================
class Processor(BaseProcessor):
    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        self.cache = {}

    def generate(self, track_model, note_model, bpm):
        p = track_model.source_params
        # Ratios for the 6 oscillators (Traditional 808 ratios)
        ratios = [
            p.get("r1", 1.0), p.get("r2", 1.5), p.get("r3", 2.1),
            p.get("r4", 2.6), p.get("r5", 3.1), p.get("r6", 4.3)
        ]
        base_freq = p.get("base_freq", 200.0)
        decay = p.get("decay", 0.5)
        cutoff = p.get("bp_cutoff", 5000.0)

        # Cache key based on tuning and decay
        key = (tuple(ratios), base_freq, decay, cutoff)
        if key in self.cache: return self.cache[key]

        dur = decay
        num_s = int(dur * SAMPLE_RATE)
        # Create a silent buffer to sum into
        combined_buffer = np.zeros(num_s, dtype=np.float32)

        # 1. Generate the Cluster (6 Square Waves)
        for r in ratios:
            freq = base_freq * r
            # Use C++ type 1 (SQUARE)
            combined_buffer += self.bridge.get_buffer(freq, 0.15, 1, num_s)

        # 2. Bandpass Filter (Gives the cymbal its 'hiss' or 'gong' character)
        nyq = 0.5 * SAMPLE_RATE
        low = max(20, cutoff * 0.8) / nyq
        high = min(nyq * 0.9, cutoff * 1.2) / nyq
        b, a = butter(1, [low, high], btype='band')
        filtered = lfilter(b, a, combined_buffer)

        # 3. Exponential Decay
        t = np.linspace(0, dur, num_s, False)
        env = np.exp(-8 * t / dur)
        final_wave = (filtered * env).astype(np.float32)

        self.cache[key] = final_wave
        return final_wave

# =============================================================================
# 2. THE UI COMPONENT (Metallic Designer)
# =============================================================================
class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 480)
        self.font = font
        self.plugin_id = "SQUARE_CYMBAL"
        self.title = "SQUARE CYMBAL"
        self.active = True

        # Main Sliders
        self.freq_slider = Slider(0, 0, 260, 12, 40, 800, 200, "BASE FREQ")
        self.decay_slider = Slider(0, 0, 260, 12, 0.05, 2.0, 0.5, "DECAY")
        self.cutoff_slider = Slider(0, 0, 260, 12, 500, 12000, 5000, "BANDPASS")

        # 6 Small Ratio Sliders (The Cluster)
        self.ratio_sliders = [
            Slider(0, 0, 15, 100, 0.5, 6.0, 1.0 + (i*0.6), "", vertical=True)
            for i in range(6)
        ]

    def draw(self, screen, track, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)
        params = track.source_params

        # 1. Main Controls
        self.freq_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(50), scale(260), scale(12))
        self.decay_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(95), scale(260), scale(12))
        self.cutoff_slider.move_to(self.rect.x + scale(20), self.rect.y + scale(140), scale(260), scale(12))
        
        self.freq_slider.val = params.get("base_freq", 200)
        self.decay_slider.val = params.get("decay", 0.5)
        self.cutoff_slider.val = params.get("bp_cutoff", 5000)

        self.freq_slider.draw(screen, self.font)
        self.decay_slider.draw(screen, self.font)
        self.cutoff_slider.draw(screen, self.font)

        # 2. Cluster Ratios Label
        lbl = self.font.render("METALLIC CLUSTER RATIOS", True, WHITE)
        screen.blit(lbl, (self.rect.x + scale(20), self.rect.y + scale(175)))

        # 3. Draw the 6 Cluster Sliders
        for i, s in enumerate(self.ratio_sliders):
            s.move_to(self.rect.x + scale(30 + i*42), self.rect.y + scale(200), scale(15), scale(100))
            s.val = params.get(f"r{i+1}", 1.0 + (i*0.6))
            s.draw(screen, self.font)

    def handle_event(self, event, track_model):
        if hasattr(event, 'pos'):
            action = self.check_standard_interactions(event.pos, UI_SCALE)
            if action == "TOGGLE": self.active = not self.active

        # Handle Main Sliders
        f = self.freq_slider.handle_event(event)
        if f: track_model.source_params["base_freq"] = f
        d = self.decay_slider.handle_event(event)
        if d: track_model.source_params["decay"] = d
        c = self.cutoff_slider.handle_event(event)
        if c: track_model.source_params["bp_cutoff"] = c

        # Handle Cluster Sliders
        for i, s in enumerate(self.ratio_sliders):
            val = s.handle_event(event)
            if val: track_model.source_params[f"r{i+1}"] = val

    def global_release(self):
        self.freq_slider.grabbed = False
        self.decay_slider.grabbed = False
        self.cutoff_slider.grabbed = False
        for s in self.ratio_sliders: s.grabbed = False
```

## File: components\builder_plugins\__init__.py
```python

```

## File: containers\base_view.py
```python
# Blooper4/containers/base_view.py
import pygame
from constants import *

class BaseView:
    """
    The Layout Manager for Blooper 4.0 screens.
    Calculates the 'Main Working Area' based on scaling and layout requirements.
    """
    def __init__(self, font, has_header=True, has_mixer=True):
        self.font = font
        self.has_header = has_header
        self.has_mixer = has_mixer
        
        # This list will hold the Widgets (Components) assigned to this view
        self.widgets = []
        
        # Calculate the 'Safe Zone' for content
        self.update_view_rect()

    def update_view_rect(self):
        """Recalculates the screen area available between the header and mixer."""
        top_offset = scale(HEADER_H) if self.has_header else 0
        bottom_offset = scale(MIXER_H) if self.has_mixer else 0
        
        # The main 'stage' rect
        self.rect = pygame.Rect(
            0, 
            top_offset, 
            WINDOW_W, 
            WINDOW_H - top_offset - bottom_offset
        )

    def draw_widgets(self, screen):
        """Standard loop to draw all widgets attached to this view."""
        for widget in self.widgets:
            if hasattr(widget, 'draw') and widget.is_visible:
                # Most 4.0 widgets now expect scale in their draw call
                widget.draw(screen)

    def handle_widget_events(self, event):
        """Standard loop to route events to widgets."""
        for widget in self.widgets:
            if hasattr(widget, 'handle_event') and widget.is_visible:
                widget.handle_event(event)
```

## File: containers\builder_view.py
```python
# Blooper4/containers/builder_view.py
import pygame
from constants import *
from containers.base_view import BaseView
from components.builder.sampler_brain import SamplerBrainUI
from components.builder.mode_toggle import ModeToggleUI
from components.builder.piano_roll_settings import PianoRollSettingsUI
from ui_components import Dropdown

class BuilderView(BaseView):
    def __init__(self, font, factory):
        super().__init__(font, has_header=True, has_mixer=True)
        self.factory = factory
        self.scroll_x = 0

        # UI Instance Cache
        self.ui_instances = {i: {"SOURCE": None, "SAMPLER_BRAIN": None, "FX": []} for i in range(NUM_TRACKS)}

         # FIX: Explicitly create the Sampler Brain UI once
        from components.builder.sampler_brain import SamplerBrainUI
        self.sampler_brain_ui = SamplerBrainUI(0, 0, self.font)

        # Master mode toggle (PIANO ROLL | SAMPLE PADS)
        self.mode_toggle_ui = ModeToggleUI(0, 0)

        # Piano roll settings (CHROMATIC | MODAL | MICROTONAL)
        self.piano_roll_settings_ui = PianoRollSettingsUI(0, 0, self.font)

        # Dropdown components
        self.source_dropdown = Dropdown(0, 0, scale(280), scale(40),
                                        list(factory.source_registry.keys()),
                                        "SOURCE: DUAL_OSC")

        self.fx_dropdown = Dropdown(0, 0, scale(180), scale(30),
                                   list(factory.effect_registry.keys()),
                                   "+ FX")

    def _sync_ui_instances(self, track, idx):
        data = self.ui_instances[idx]
        
        # 1. Sync Sampler Brain (Only if in Sampler Mode)
        if track.mode == "SAMPLER" and not data["SAMPLER_BRAIN"]:
            data["SAMPLER_BRAIN"] = SamplerBrainUI(0, 0, self.font)

        # 2. Sync Source UI
        target_source = track.source_type if track.mode == "SYNTH" else track.sampler_map[track.active_pad]["engine"]
        if not data["SOURCE"] or data["SOURCE"].plugin_id != target_source:
            ui_class = self.factory.get_ui_class(target_source)
            if ui_class:
                data["SOURCE"] = ui_class(0, 0, self.font)
                data["SOURCE"].plugin_id = target_source

        # 3. Sync FX Chain
        if len(data["FX"]) != len(track.effects):
            data["FX"] = []
            for fx in track.effects:
                ui_class = self.factory.get_ui_class(fx["type"])
                if ui_class:
                    instance = ui_class(0, 0, self.font)
                    instance.plugin_id = fx["type"]
                    data["FX"].append(instance)

    def draw(self, screen, song, active_idx):
        track = song.tracks[active_idx]
        self.update_view_rect()
        self._sync_ui_instances(track, active_idx)

        old_clip = screen.get_clip()
        screen.set_clip(self.rect)
        pygame.draw.rect(screen, COLOR_BG, self.rect)

        ui_data = self.ui_instances[active_idx]

        # === TWO-COLUMN LAYOUT ===
        left_x = self.rect.x + scale(20)
        right_x = left_x + scale(320)  # 300 (panel width) + 20 (gap)
        curr_y = self.rect.y + scale(10)

        # --- ROW 1: TOP BAR ---
        # Left: MODE TOGGLE
        self.mode_toggle_ui.move_to(left_x, curr_y)
        self.mode_toggle_ui.draw(screen, track)

        # Right: SOURCE SELECTOR DROPDOWN (position it, but draw it LAST for z-order)
        if track.mode == "SYNTH":
            self.source_dropdown.move_to(right_x, curr_y, scale(280), scale(40))
            self.source_dropdown.set_label(f"SOURCE: {track.source_type}")
        else:  # SAMPLER mode - show active pad's engine
            active_engine = track.sampler_map[track.active_pad]["engine"]
            self.source_dropdown.move_to(right_x, curr_y, scale(280), scale(40))
            self.source_dropdown.set_label(f"ENGINE: {active_engine}")

        curr_y = self.mode_toggle_ui.rect.bottom + scale(10)

        # --- ROW 2: MAIN CONTENT (TWO COLUMNS) ---
        # LEFT COLUMN: MODE-SPECIFIC PANEL
        if track.mode == "SAMPLER":
            self.sampler_brain_ui.draw(screen, track, left_x, curr_y, UI_SCALE)
        else:  # SYNTH mode
            self.piano_roll_settings_ui.draw(screen, track, left_x, curr_y, UI_SCALE)

        # RIGHT COLUMN: SOURCE RACK (Horizontal chain)
        curr_x = right_x - self.scroll_x
        prev_module = None

        # A. DRAW ACTIVE SOURCE
        if ui_data["SOURCE"]:
            ui_data["SOURCE"].rect.topleft = (curr_x, curr_y)

            if track.mode == "SYNTH":
                ui_data["SOURCE"].draw(screen, track, curr_x, curr_y, UI_SCALE)
            else:
                # Sampler mode: Pass proxy for active pad
                class PadProxy: pass
                proxy = PadProxy()
                proxy.source_params = track.sampler_map[track.active_pad]["params"]
                proxy.drum_pads = track.drum_pads
                ui_data["SOURCE"].draw(screen, proxy, curr_x, curr_y, UI_SCALE)

            prev_module = ui_data["SOURCE"]
            curr_x = prev_module.rect.right + scale(20)

        # B. DRAW FX CHAIN
        for i, fx_ui in enumerate(ui_data["FX"]):
            fx_ui.dock_to(prev_module, 'TL', 'TR', offset=(scale(20), 0))
            fx_ui.draw(screen, track.effects[i], fx_ui.rect.x, fx_ui.rect.y, UI_SCALE)
            prev_module = fx_ui
            curr_x = prev_module.rect.right + scale(20)

        # C. DRAW ADD FX BUTTON
        self.add_btn_rect = pygame.Rect(curr_x, curr_y, scale(80), scale(60))
        pygame.draw.rect(screen, (30, 30, 35), self.add_btn_rect, border_radius=scale(10))
        txt = self.font.render("+ FX", True, GRAY)
        screen.blit(txt, (self.add_btn_rect.centerx - txt.get_width()//2,
                          self.add_btn_rect.centery - 5))

        # D. DRAW SOURCE DROPDOWN LAST (so it appears on top of everything)
        self.source_dropdown.draw(screen, self.font)

        screen.set_clip(old_clip)

    def handle_event(self, event, song, active_idx):
        track = song.tracks[active_idx]
        ui_data = self.ui_instances[active_idx]

        # Guard: Only route if event has position
        if not hasattr(event, 'pos'):
            return

        # 0. ROUTE TO MODE TOGGLE (highest priority, always visible)
        result = self.mode_toggle_ui.handle_event(event, track)
        if result == "MODE_CHANGED":
            self._sync_ui_instances(track, active_idx)
            return

        # 1. HANDLE SOURCE SELECTOR DROPDOWN (both modes)
        result = self.source_dropdown.handle_event(event)
        if result and result != "TOGGLE":
            # User selected a new source plugin/engine
            if track.mode == "SYNTH":
                if result != track.source_type:
                    track.source_type = result
                    self._sync_ui_instances(track, active_idx)
            else:  # SAMPLER mode
                # Update the active pad's engine
                if result != track.sampler_map[track.active_pad]["engine"]:
                    track.sampler_map[track.active_pad]["engine"] = result
                    self._sync_ui_instances(track, active_idx)
            return

        # 2. ROUTE TO MODE-SPECIFIC PANEL (with collision check)
        if track.mode == "SAMPLER":
            # Check if click is within sampler brain bounds
            if self.sampler_brain_ui.rect.collidepoint(event.pos):
                self.sampler_brain_ui.handle_event(event, track)
                return  # Don't cascade to source if sampler handled it
        else:  # SYNTH mode
            # Check if click is within piano roll settings bounds
            if self.piano_roll_settings_ui.rect.collidepoint(event.pos):
                result = self.piano_roll_settings_ui.handle_event(event, track)
                if result == "SCALE_CHANGED":
                    return

        # 3. ROUTE TO SOURCE (with collision check)
        if ui_data["SOURCE"] and ui_data["SOURCE"].rect.collidepoint(event.pos):
            if track.mode == "SAMPLER":
                class PadProxy: pass
                proxy = PadProxy()
                proxy.source_params = track.sampler_map[track.active_pad]["params"]
                proxy.drum_pads = track.drum_pads
                proxy.source_type = track.sampler_map[track.active_pad]["engine"]
                ui_data["SOURCE"].handle_event(event, proxy)
                track.sampler_map[track.active_pad]["engine"] = proxy.source_type
            else:
                ui_data["SOURCE"].handle_event(event, track)
            return

        # 4. ROUTE TO FX CHAIN (with collision check)
        for i, fx_ui in enumerate(ui_data["FX"]):
            if fx_ui.rect.collidepoint(event.pos):
                fx_ui.handle_event(event, track.effects[i])
                return

        # 5. CHECK ADD FX BUTTON (TODO: Replace with fx_dropdown later)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hasattr(self, 'add_btn_rect') and self.add_btn_rect.collidepoint(event.pos):
                # TODO: Use fx_dropdown.handle_event() instead
                pass
```

## File: containers\editor_view.py
```python
# Blooper4/containers/editor_view.py
import pygame
from constants import *
from containers.base_view import BaseView
from components.note_type_toolbar import NoteTypeToolbar
from components.piano_roll import PianoRoll
from components.drum_roll import DrumRoll

class EditorView(BaseView):
    def __init__(self, font):
        super().__init__(font, has_header=True, has_mixer=True)
        
        # 1. Toolbar
        self.toolbar = NoteTypeToolbar(self.rect.x, self.rect.y, self.rect.width, scale(60), font)
        
        # 2. Grids
        grid_w = self.rect.width - scale(EDITOR_SIDEBAR_W)
        grid_h = self.rect.height - scale(60)
        self.piano_roll = PianoRoll(0, 0, grid_w, grid_h)
        self.drum_roll = DrumRoll(0, 0, grid_w, grid_h)
        
        # 3. Register for events and global releases
        self.widgets = [self.toolbar, self.piano_roll, self.drum_roll]
        self.quantize = "1/16"
        self.input_velocity = 100

    def draw(self, screen, song, active_idx, current_tick, font):
        track = song.tracks[active_idx]
        grid = self.drum_roll if track.is_drum else self.piano_roll
        
        # Maintenance
        self.update_view_rect()
        self.toolbar.draw(screen, song)
        
        # Dynamic Docking
        grid.dock_to(self.toolbar, my_corner='TL', target_corner='BL', offset=(scale(EDITOR_SIDEBAR_W), 0))
        grid.draw(screen, track, current_tick, font)

        # Sidebar
        sidebar_rect = pygame.Rect(0, grid.rect.y, scale(EDITOR_SIDEBAR_W), grid.rect.height)
        pygame.draw.rect(screen, COLOR_PANEL, sidebar_rect)
        pygame.draw.line(screen, (60, 60, 70), (sidebar_rect.right, sidebar_rect.top), (sidebar_rect.right, sidebar_rect.bottom), 2)
        
        self._draw_labels(screen, track, grid, sidebar_rect, font)

    def _draw_labels(self, screen, track, grid, sidebar_rect, font):
        # 4.1 Logic: If track is a Sampler, show Pad Labels
        if track.mode == "SAMPLER":
            for p in range(128):
                _, y = grid.get_coords(0, p)
                if sidebar_rect.top <= y <= sidebar_rect.bottom:
                    pad_cfg = track.sampler_map.get(p, {})
                    # Show User Label or default to Pad number
                    label = pad_cfg.get("label") or f"Pad {p}"
                    # Add a tiny indicator of what engine is on that pad
                    eng = pad_cfg.get("engine", "NONE")[:3]
                    lbl = font.render(f"{label} [{eng}]", True, WHITE)
                    screen.blit(lbl, (5, y + (grid.row_h // 2 - 6)))
        else:
            # Standard Piano Roll Labels
            for p in range(128):
                _, y = grid.get_coords(0, p)
                if sidebar_rect.top <= y <= sidebar_rect.bottom:
                    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
                    lbl = font.render(f"{notes[p%12]}{p//12}", True, WHITE)
                    screen.blit(lbl, (5, y + 2))

    def handle_event(self, event, song, active_idx):
        mx, my = pygame.mouse.get_pos()
        track = song.tracks[active_idx]
        grid = self.drum_roll if track.is_drum else self.piano_roll

        # --- THE FIX: Local Mouse Release ---
        if event.type == pygame.MOUSEBUTTONUP:
            self.piano_roll.is_dragging = False
            self.drum_roll.is_dragging = False
            self.piano_roll.current_note = None
            self.drum_roll.current_note = None
            self.toolbar.vel_slider.grabbed = False
            return
        
        # Route to Toolbar
        if self.toolbar.rect.collidepoint((mx, my)):
            t_data = self.toolbar.handle_event(event, song)
            self.quantize = t_data.get("quantize", "1/16")
            self.input_velocity = t_data.get("velocity", 100)
            return


        if grid.rect.collidepoint((mx, my)):
            if event.type == pygame.MOUSEWHEEL:
                if pygame.key.get_pressed()[pygame.K_LCTRL]:
                    grid.scroll_x = max(0, grid.scroll_x - event.y * 120)
                elif not track.is_drum:
                    grid.scroll_y = max(0, min(127 * scale(GRID_HEIGHT), grid.scroll_y - event.y * scale(GRID_HEIGHT)))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                tick, pitch = grid.get_tick_at(mx), grid.get_pitch_at(my)
                q = QUANT_MAP[self.quantize]
                quant_tick = (tick // q) * q
                existing = next((n for n in track.notes if n.pitch == pitch and n.tick <= tick < n.tick + n.duration), None)
                if existing:
                    track.notes.remove(existing)
                    self.toolbar.log(f"Del: {pitch}")
                else:
                    grid.is_dragging = True
                    grid.current_note = track.add_note(quant_tick, pitch, q, velocity=int(self.input_velocity))
                    self.toolbar.log(f"Add: {pitch}")
                song.is_dirty = True

            # --- THE FIX: Only update duration if left button is actually held ---
            if event.type == pygame.MOUSEMOTION and grid.is_dragging:
                if pygame.mouse.get_pressed()[0]: # Verified hold
                    q = QUANT_MAP[self.quantize]
                    mouse_tick = grid.get_tick_at(mx)
                    grid.current_note.duration = max(q, ((mouse_tick // q) + 1) * q - grid.current_note.tick)
                else:
                    # Safety reset if we somehow missed the MOUSEBUTTONUP
                    grid.is_dragging = False
```

## File: containers\main_menu.py
```python
# Blooper4/containers/main_menu.py
import pygame
from constants import *
from containers.base_view import BaseView
from ui_components import Button

class MainMenu(BaseView):
    """
    4.0 Splash Screen & Settings Hub.
    Handles Fullscreen toggles and dynamic UI Scaling.
    """
    def __init__(self, font):
        # Menu takes the full screen (No header or mixer reserved)
        super().__init__(font, has_header=False, has_mixer=False)
        
        self.state = "MAIN" # "MAIN" or "VIDEO"
        
        # --- MAIN MENU BUTTONS ---
        # Positioned logically (unscaled); layout() handles scaling/centering
        self.main_buttons = {
            "RESUME":     Button(0, 0, 250, 45, "RESUME", (60, 60, 70)),
            "NEW":        Button(0, 0, 250, 45, "NEW PROJECT", BLUE),
            "LOAD":       Button(0, 0, 250, 45, "LOAD PROJECT", GRAY),
            "SAVE":       Button(0, 0, 250, 45, "SAVE PROJECT", GRAY),
            "VIDEO":      Button(0, 0, 250, 45, "VIDEO SETTINGS", GRAY),
            "EXIT":       Button(0, 0, 250, 45, "EXIT DAW", (150, 50, 50))
        }

        # --- VIDEO SETTINGS BUTTONS ---
        self.video_buttons = {
            "SCALE_UP":   Button(0, 0, 60, 50, "+", GREEN),
            "SCALE_DOWN": Button(0, 0, 60, 50, "-", RED),
            "FULLSCREEN": Button(0, 0, 250, 50, "TOGGLE FULLSCREEN", (100, 100, 110)),
            "BACK":       Button(0, 0, 250, 50, "BACK", GRAY)
        }

    def _layout_buttons(self):
        """Centers buttons based on current UI_SCALE."""
        cx = WINDOW_W // 2
        cy = WINDOW_H // 2
        
        # Scale button dimensions
        bw, bh = scale(250), scale(50)
        gap = scale(15)

        if self.state == "MAIN":
            y_start = cy - (len(self.main_buttons) * (bh + gap)) // 2
            for i, btn in enumerate(self.main_buttons.values()):
                btn.move_to(cx - bw // 2, y_start + i * (bh + gap), bw, bh)
        
        elif self.state == "VIDEO":
            y_start = cy - scale(100)
            # Scale control row
            sw, sh = scale(60), scale(50)
            self.video_buttons["SCALE_DOWN"].move_to(cx - sw - scale(10), y_start, sw, sh)
            self.video_buttons["SCALE_UP"].move_to(cx + scale(10), y_start, sw, sh)
            
            # Other video buttons
            self.video_buttons["FULLSCREEN"].move_to(cx - bw // 2, y_start + scale(70), bw, bh)
            self.video_buttons["BACK"].move_to(cx - bw // 2, y_start + scale(140), bw, bh)

    def draw(self, screen):
        # 1. Maintenance
        self.update_view_rect()
        self._layout_buttons()
        
        # 2. Draw Background
        pygame.draw.rect(screen, (15, 15, 20), self.rect)
        
        # 3. Draw Title
        title_size = scale(72)
        title_font = pygame.font.SysFont("Consolas", title_size, bold=True)
        title_txt = title_font.render("BLOOPER 4.0", True, COLOR_ACCENT)
        screen.blit(title_txt, (WINDOW_W//2 - title_txt.get_width()//2, scale(100)))

        # 4. Draw Current Sub-Menu
        buttons = self.main_buttons if self.state == "MAIN" else self.video_buttons
        for btn in buttons.values():
            btn.draw(screen, self.font)
            
        # Draw current scale info if in video menu
        if self.state == "VIDEO":
            scale_info = self.font.render(f"CURRENT SCALE: {int(UI_SCALE * 100)}%", True, WHITE)
            screen.blit(scale_info, (WINDOW_W//2 - scale_info.get_width()//2, WINDOW_H//2 - scale(140)))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "MAIN":
                if self.main_buttons["RESUME"].is_clicked(event.pos): return "RESUME"
                if self.main_buttons["EXIT"].is_clicked(event.pos): return "EXIT"
                if self.main_buttons["NEW"].is_clicked(event.pos): return "NEW"
                if self.main_buttons["LOAD"].is_clicked(event.pos): return "LOAD"
                if self.main_buttons["SAVE"].is_clicked(event.pos): return "SAVE"
                
                if self.main_buttons["VIDEO"].is_clicked(event.pos): 
                    self.state = "VIDEO"
                    return "MENU_NAVIGATE" # Tell main.py we handled the click
            
            elif self.state == "VIDEO":
                if self.video_buttons["BACK"].is_clicked(event.pos): 
                    self.state = "MAIN"
                    return "MENU_NAVIGATE"
                
                if self.video_buttons["FULLSCREEN"].is_clicked(event.pos): return "TOGGLE_FS"
                
                import constants
                if self.video_buttons["SCALE_UP"].is_clicked(event.pos):
                    constants.UI_SCALE = min(2.0, constants.UI_SCALE + 0.1)
                    return "REBUILD_UI"
                if self.video_buttons["SCALE_DOWN"].is_clicked(event.pos):
                    constants.UI_SCALE = max(0.5, constants.UI_SCALE - 0.1)
                    return "REBUILD_UI"
        
        return None
```

## File: Save_Files\metal drums NES.bloop
```
{
    "version": "4.0.0",
    "bpm": 120,
    "length_ticks": 1920,
    "tracks": [
        {
            "name": "Track 1",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 2",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 3",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 4",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 5",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 6",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 7",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 8",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 9",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Drums",
            "is_drum": true,
            "source_type": "NOISE_DRUM",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.9578947368421052,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 24.457264957264957,
                    "length": 0.9299145299145298,
                    "color": "BROWN",
                    "gain": 1.2735042735042734
                },
                "35": {
                    "type": "SNARE",
                    "pitch": 47.914529914529915,
                    "length": 0.8865384615384615,
                    "color": "BROWN",
                    "gain": 1.9658119658119657
                },
                "36": {
                    "type": "CYMBAL",
                    "pitch": 39.38461538461539,
                    "length": 1.5,
                    "color": "WHITE",
                    "gain": 0.6923076923076923
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": [
                {
                    "t": 0,
                    "p": 36,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 0,
                    "p": 34,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 240,
                    "p": 36,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 360,
                    "p": 34,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 480,
                    "p": 35,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 480,
                    "p": 36,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 720,
                    "p": 36,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 960,
                    "p": 36,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 960,
                    "p": 34,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1200,
                    "p": 36,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1200,
                    "p": 34,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1320,
                    "p": 34,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1440,
                    "p": 36,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1440,
                    "p": 35,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1680,
                    "p": 36,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1680,
                    "p": 35,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1740,
                    "p": 35,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1800,
                    "p": 35,
                    "d": 60,
                    "v": 100
                },
                {
                    "t": 1860,
                    "p": 35,
                    "d": 60,
                    "v": 100
                }
            ]
        },
        {
            "name": "Track 11",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 12",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 13",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 14",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 15",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 16",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        }
    ]
}
```

## File: Save_Files\testo.bloop
```
{
    "version": "4.0.0",
    "bpm": 120,
    "length_ticks": 1920,
    "tracks": [
        {
            "name": "Track 1",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": [
                {
                    "t": 0,
                    "p": 58,
                    "d": 2400,
                    "v": 100
                },
                {
                    "t": 1440,
                    "p": 53,
                    "d": 480,
                    "v": 100
                }
            ]
        },
        {
            "name": "Track 2",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 3",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 4",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 5",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 6",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 7",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 8",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 9",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Drums",
            "is_drum": true,
            "source_type": "NOISE_DRUM",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 11",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 12",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 13",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 14",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 15",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 16",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        }
    ]
}
```

## File: Save_Files\testosterone.bloop
```
{
    "version": "4.0.0",
    "bpm": 120,
    "length_ticks": 1920,
    "tracks": [
        {
            "name": "Track 1",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": [
                {
                    "t": 480,
                    "p": 53,
                    "d": 480,
                    "v": 100
                },
                {
                    "t": 960,
                    "p": 62,
                    "d": 480,
                    "v": 100
                },
                {
                    "t": 1440,
                    "p": 59,
                    "d": 480,
                    "v": 100
                }
            ]
        },
        {
            "name": "Track 2",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 3",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 4",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 5",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 6",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 7",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 8",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 9",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Drums",
            "is_drum": true,
            "source_type": "NOISE_DRUM",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 11",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 12",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 13",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 14",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 15",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 16",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        }
    ]
}
```

## File: Save_Files\testosterone2.bloop
```
{
    "version": "4.0.0",
    "bpm": 120,
    "length_ticks": 1920,
    "tracks": [
        {
            "name": "Track 1",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": [
                {
                    "t": 0,
                    "p": 56,
                    "d": 480,
                    "v": 100
                },
                {
                    "t": 960,
                    "p": 54,
                    "d": 480,
                    "v": 100
                },
                {
                    "t": 1440,
                    "p": 63,
                    "d": 480,
                    "v": 100
                }
            ]
        },
        {
            "name": "Track 2",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 3",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 4",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 5",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 6",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 7",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 8",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 9",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Drums",
            "is_drum": true,
            "source_type": "NOISE_DRUM",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 11",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 12",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 13",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 14",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 15",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        },
        {
            "name": "Track 16",
            "is_drum": false,
            "source_type": "DUAL_OSC",
            "source_params": {
                "osc1_type": "SAW",
                "osc2_type": "SINE",
                "osc2_detune": 10,
                "noise_type": "WHITE",
                "volume": 0.8
            },
            "params": {
                "volume": 0.8,
                "pan": 0.5,
                "mute": false,
                "solo": false
            },
            "effects": [],
            "drum_pads": {
                "34": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "35": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "36": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "37": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "38": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "39": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "40": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "41": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "42": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "43": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "44": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "45": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "46": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "47": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "48": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "49": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "50": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "51": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                },
                "52": {
                    "type": "DRUM",
                    "pitch": 60,
                    "length": 0.3
                }
            },
            "notes": []
        }
    ]
}
```

## File: utils\project_manager.py
```python
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
```

## File: utils\requirements_check.py
```python
# Blooper4/utils/requirements_check.py
import subprocess
import sys
import os
import importlib.util

def check_requirements():
    print("--- Blooper 4.0 Dependency Check ---")
    req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
    
    if not os.path.exists(req_path):
        with open(req_path, "w") as f:
            f.write("pygame==2.6.1\nnumpy>=1.26.0\nscipy>=1.11.0\n")

    with open(req_path, "r") as f:
        libs = [line.split('==')[0].split('>=')[0].strip().lower() for line in f if line.strip()]

    missing = False
    for lib in libs:
        if importlib.util.find_spec(lib) is None:
            print(f"! Library '{lib}' is missing.")
            missing = True

    if missing:
        print("Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
            print("[OK] Success.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print("[OK] Environment Ready.")
```

