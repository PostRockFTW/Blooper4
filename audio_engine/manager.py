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

    def stop_all(self):
        """Instantly kills all active voices."""
        for track_idx in self.active_channels:
            for channel, _ in self.active_channels[track_idx]:
                channel.stop()
            self.active_channels[track_idx] = []
            
    def cleanup(self):
        """Final shutdown of C++ bridge."""
        self.bridge.cleanup()