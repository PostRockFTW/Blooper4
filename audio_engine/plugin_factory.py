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
            "SQUARE_CYMBAL": "square_cymbal",
            "WAVETABLE_SYNTH": "wavetable_synth",
            "FM_DRUM": "fm_drum",
            "PERIODIC_NOISE": "periodic_noise"
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