import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import wx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from grid_colors import grid_colors_for_theme


LIGHT = {'DUP_ROW': (128, 255, 255), 'COUNTDOWN_ROW': (128, 255, 200),
         'FILTERED_GRID': (255, 255, 200), 'ROW_PLAYING_NOW': (200, 200, 255),
         'ROW_PLAYED_TO_END': (200, 200, 200), 'ROW_SKIPPED': (255, 200, 200)}


def contrast(text, background):
    def luminance(rgb):
        channels = (v / 255 for v in rgb)
        linear = (v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels)
        return sum(weight * value for weight, value in zip((0.2126, 0.7152, 0.0722), linear))
    low, high = sorted((luminance(text), luminance(background)))
    return (high + 0.05) / (low + 0.05)


class GridColorsTests(unittest.TestCase):
    def test_status_colors_and_contrast(self):
        for dark, text in [(False, (46, 52, 54)), (True, (238, 238, 236))]:
            settings = SimpleNamespace(GetAppearance=lambda: SimpleNamespace(IsDark=lambda: dark))
            palette = grid_colors_for_theme(settings)
            backgrounds = {role: getattr(palette, role) for role in LIGHT}
            if not dark:
                self.assertEqual(backgrounds, LIGHT)
            self.assertEqual(len(set(backgrounds.values())), len(LIGHT))
            for role, bg in backgrounds.items():
                with self.subTest(dark=dark, role=role):
                    self.assertGreaterEqual(contrast(text, bg), 4.5)

    def test_legacy_wx_uses_window_background(self):
        for level, dark in [(40, True), (240, False)]:
            def window_color(which):
                self.assertEqual(which, wx.SYS_COLOUR_WINDOW)
                return wx.Colour(level, level, level)
            palette = grid_colors_for_theme(SimpleNamespace(GetColour=window_color))
            self.assertEqual(palette.FILTERED_GRID == LIGHT['FILTERED_GRID'], not dark)