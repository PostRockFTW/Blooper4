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