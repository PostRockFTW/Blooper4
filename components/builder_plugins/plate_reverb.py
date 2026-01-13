# Blooper4/components/builder_plugins/plate_reverb.py
import pygame
import numpy as np
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider

class Processor(BaseProcessor):
    """
    Plate Reverb - Models a mechanical plate reverb
    Characteristics: Bright, dense early reflections, metallic tone
    Uses multiple delay lines with diffusion and high-frequency damping
    """
    def process(self, data, params):
        mix = params.get("mix", 0.2)
        decay = params.get("decay", 0.6)
        damping = params.get("damping", 0.7)
        predelay = params.get("predelay", 0.01)

        # Pre-delay (time before reverb starts)
        predelay_samples = int(predelay * SAMPLE_RATE)
        if predelay_samples >= len(data):
            predelay_samples = 0

        # Plate reverb uses dense, short delay lines (brighter than room reverb)
        # These are prime numbers to avoid resonances
        delay_times = [0.011, 0.017, 0.023, 0.031, 0.037, 0.041, 0.043, 0.047]

        reverb_out = np.zeros_like(data)

        # Apply pre-delay
        delayed_input = np.zeros_like(data)
        if predelay_samples > 0 and predelay_samples < len(data):
            delayed_input[predelay_samples:] = data[:-predelay_samples]
        else:
            delayed_input = data.copy()

        # Process through delay network
        for i, d in enumerate(delay_times):
            d_samples = int(d * decay * 2.0 * SAMPLE_RATE)
            if d_samples <= 0 or d_samples >= len(data):
                continue

            temp = np.zeros_like(data)
            delayed_signal = delayed_input[:-d_samples]

            # Apply high-frequency damping (plates lose high frequencies faster)
            # Simple one-pole low-pass filter
            damped_signal = delayed_signal.copy()
            for j in range(1, len(damped_signal)):
                damped_signal[j] = damped_signal[j] * damping + damped_signal[j-1] * (1.0 - damping)

            # Apply feedback with decay
            feedback = 0.6 * decay
            temp[d_samples:] = damped_signal * feedback

            # Add to output with slight phase variation
            phase = (i % 2) * 2 - 1  # Alternates between -1 and 1
            reverb_out += temp * phase

        # Normalize and mix
        reverb_out = reverb_out / len(delay_times)

        # Plate reverbs are typically brighter, so boost high frequencies slightly
        # This is a simple approximation using differentiation
        if len(reverb_out) > 1:
            brightness = 1.2
            high_freq = np.diff(reverb_out, prepend=reverb_out[0]) * brightness
            reverb_out = reverb_out + high_freq * 0.3

        return (data * (1.0 - mix)) + (reverb_out * mix)

class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400)
        self.font, self.title = font, "PLATE REVERB"
        self.active = True
        self.mix_slider = Slider(0, 0, 240, 15, 0, 1, 0.2, "WET MIX")
        self.decay_slider = Slider(0, 0, 240, 15, 0, 1, 0.6, "DECAY")
        self.damping_slider = Slider(0, 0, 240, 15, 0, 1, 0.7, "DAMPING")
        self.predelay_slider = Slider(0, 0, 240, 15, 0, 0.1, 0.01, "PRE-DELAY")

    def draw(self, screen, fx_data, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)

        # Position sliders vertically
        y_offset = 80
        self.mix_slider.move_to(self.rect.x + int(30 * scale_f), self.rect.y + int(y_offset * scale_f), int(240 * scale_f), int(15 * scale_f))
        y_offset += 70
        self.decay_slider.move_to(self.rect.x + int(30 * scale_f), self.rect.y + int(y_offset * scale_f), int(240 * scale_f), int(15 * scale_f))
        y_offset += 70
        self.damping_slider.move_to(self.rect.x + int(30 * scale_f), self.rect.y + int(y_offset * scale_f), int(240 * scale_f), int(15 * scale_f))
        y_offset += 70
        self.predelay_slider.move_to(self.rect.x + int(30 * scale_f), self.rect.y + int(y_offset * scale_f), int(240 * scale_f), int(15 * scale_f))

        # Sync slider values from track data
        self.mix_slider.val = fx_data["params"].get("mix", 0.2)
        self.decay_slider.val = fx_data["params"].get("decay", 0.6)
        self.damping_slider.val = fx_data["params"].get("damping", 0.7)
        self.predelay_slider.val = fx_data["params"].get("predelay", 0.01)

        # Draw all sliders
        self.mix_slider.draw(screen, self.font)
        self.decay_slider.draw(screen, self.font)
        self.damping_slider.draw(screen, self.font)
        self.predelay_slider.draw(screen, self.font)

    def handle_event(self, event, fx_data):
        # Only check button interactions on actual clicks, not hover
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and hasattr(event, 'pos'):
            action = self.check_standard_interactions(event.pos, UI_SCALE)
            if action == "TOGGLE": self.active = not self.active
            if action == "DELETE": return "DELETE"

        # Handle slider events
        m = self.mix_slider.handle_event(event)
        if m is not None: fx_data["params"]["mix"] = m

        d = self.decay_slider.handle_event(event)
        if d is not None: fx_data["params"]["decay"] = d

        dmp = self.damping_slider.handle_event(event)
        if dmp is not None: fx_data["params"]["damping"] = dmp

        pre = self.predelay_slider.handle_event(event)
        if pre is not None: fx_data["params"]["predelay"] = pre

        return None

    def global_release(self):
        self.mix_slider.grabbed = False
        self.decay_slider.grabbed = False
        self.damping_slider.grabbed = False
        self.predelay_slider.grabbed = False
