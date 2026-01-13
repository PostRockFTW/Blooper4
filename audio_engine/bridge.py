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