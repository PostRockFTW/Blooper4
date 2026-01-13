# Blooper4/components/builder_plugins/reverb.py
import pygame
import numpy as np
from constants import *
from audio_engine.base_processor import BaseProcessor
from components.base_element import BaseUIElement
from ui_components import Slider

class Processor(BaseProcessor):
    def process(self, data, params):
        mix, size = params.get("mix", 0.1), params.get("size", 0.5)
        delay_times = [0.029, 0.037, 0.043, 0.047]
        reverb_out = np.zeros_like(data)
        for d in delay_times:
            d_samples = int(d * size * SAMPLE_RATE)
            if d_samples >= len(data): continue
            temp = np.zeros_like(data)
            temp[d_samples:] = data[:-d_samples] * (0.4 + mix * 0.4)
            reverb_out += temp
        return (data * (1.0 - mix)) + (reverb_out / 4 * mix)

class UI(BaseUIElement):
    def __init__(self, x, y, font):
        super().__init__(x, y, 300, 400)
        self.font, self.title = font, "REVERB"
        self.active = True
        self.mix_slider = Slider(0, 0, 240, 15, 0, 1, 0.1, "WET MIX")
        self.size_slider = Slider(0, 0, 240, 15, 0, 1, 0.5, "ROOM SIZE")

    def draw(self, screen, fx_data, x, y, scale_f):
        self.rect.topleft = (x, y)
        self.update_layout(scale_f)
        self.draw_modular_frame(screen, self.font, self.title, self.active, scale_f)
        
        self.mix_slider.move_to(self.rect.x + int(30 * scale_f), self.rect.y + int(80 * scale_f), int(240 * scale_f), int(15 * scale_f))
        self.size_slider.move_to(self.rect.x + int(30 * scale_f), self.rect.y + int(150 * scale_f), int(240 * scale_f), int(15 * scale_f))
        
        self.mix_slider.val = fx_data["params"].get("mix", 0.1)
        self.size_slider.val = fx_data["params"].get("size", 0.5)
        
        self.mix_slider.draw(screen, self.font)
        self.size_slider.draw(screen, self.font)

    def handle_event(self, event, fx_data):
        if hasattr(event, 'pos'):
            action = self.check_standard_interactions(event.pos, UI_SCALE)
            if action == "TOGGLE": self.active = not self.active
            if action == "DELETE": return "DELETE"

        m = self.mix_slider.handle_event(event)
        if m is not None: fx_data["params"]["mix"] = m
        s = self.size_slider.handle_event(event)
        if s is not None: fx_data["params"]["size"] = s
        return None

    def global_release(self):
        self.mix_slider.grabbed = False
        self.size_slider.grabbed = False