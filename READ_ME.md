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