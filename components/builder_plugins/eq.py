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