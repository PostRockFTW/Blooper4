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
        self.source_params = {
            "osc1_type": "|/",
            "osc2_type": "~",
            "osc_mix": 0.5,
            "osc2_interval": 0,
            "osc2_detune": 15,
            "filter_cutoff": 5000,
            "transpose": 0,
            "gain": 1.0,
            "attack": 0.01,
            "length": 0.5,
            "root_note": 60
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
                "params": {
                    "pitch_hpf": 60, 
                    "length": 0.3, 
                    "type": "DRUM", 
                    "gain": 1.0, 
                    "transpose": 0,
                    "color": "WHITE",
                    "root_note": p  # CRITICAL: Neutral is the Pad number itself
                },
                "label": "" 
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
            defaults = {
                "EQ": {f"band_{i}": 1.0 for i in range(8)},
                "REVERB": {"mix": 0.1, "size": 0.5},
                "PLATE_REVERB": {"mix": 0.2, "decay": 0.6, "damping": 0.7, "predelay": 0.01}
            }
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