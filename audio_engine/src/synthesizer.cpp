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
            else if (wave_type == 3) { // TRIANGLE (Added this)
                // Basic triangle math: linear ramp up, then linear ramp down
                if (osc->phase < PI) {
                    sample = (float)(-1.0 + 2.0 * (osc->phase / PI));
                } else {
                    sample = (float)(3.0 - 2.0 * (osc->phase / PI));
                }
            }    

            buffer[i] = sample * volume;

            // Increment and wrap phase (0 to 2*PI)
            osc->phase += phase_increment;
            while (osc->phase >= 2.0 * PI) osc->phase -= 2.0 * PI;
        }
    }
}