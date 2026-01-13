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
