import sys
import unittest
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import wx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from projector import ProjectorWindow
from constants import Config
from os_tools import path


@unittest.skipUnless(wx.App.IsDisplayAvailable(), 'requires a display')
class ProjectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = wx.GetApp() or wx.App(False)

    def test_create_loads_and_refits_session_background(self):
        main_window = runpy.run_path(str(Path(path.work_dir) / 'main.pyw'))['MainWindow']
        class PreviewHost(main_window):
            def __init__(self):
                wx.Frame.__init__(self, None)
                self.config = {Config.PROJECTOR_SCREEN: 0, Config.BG_ZAD_PATH: 'background.png'}
                self.proj_win = None
                self.vid_btn, self.zad_btn, self.blk_btn = [wx.ToggleButton(self) for _ in range(3)]
                self.destroy_proj_win_item = Mock()
                self.status_bar = self.CreateStatusBar(2)

        with TemporaryDirectory() as directory:
            session = Path(directory) / 'preview.fest'
            session.touch()
            image = wx.Image(4, 2)
            image.SetRGB(wx.Rect(0, 0, 4, 2), 230, 40, 10)
            image.SaveFile(str(session.with_name('background.png')), wx.BITMAP_TYPE_PNG)
            with patch.object(path, '_fest_file', str(session)):
                host = PreviewHost()
                self.addCleanup(host.Destroy)
                host.ensure_proj_win()
                self.app.Yield()
                panel = host.proj_win.images_panel
                for size in [(400, 300), (300, 100)]:
                    host.proj_win.SetClientSize(size)
                    host.proj_win.Layout()
                    self.app.Yield()
                    bitmap = panel.drawable_bitmap
                    self.assertEqual(bitmap.ConvertToImage().GetRed(0, 0), 230)
                    width = min(panel.ClientSize.width, panel.ClientSize.height * 2)
                    self.assertEqual(bitmap.GetSize(), (width, width // 2))
                host.clear_zad(no_show=True)
                host.ensure_proj_win()
                self.app.Yield()
                self.assertTrue(host.blk_btn.GetValue())

    def test_countdown_font_scales_on_resize(self):
        app = wx.GetApp() or wx.App(False)
        parent = wx.Frame(None)
        self.addCleanup(parent.Destroy)
        parent.on_proj_win_close = lambda event: event.Skip()
        panel = ProjectorWindow(parent, 0).countdown_panel

        for size in [(321, 240), (640, 481)]:
            panel.SetSize(size)
            panel._recalculate_font_size()
            countdown = panel.countdown_text.GetFont().GetPixelSize().height
            caption = panel.info_text.GetFont().GetPixelSize().height
            self.assertGreater(countdown, caption)
            self.assertGreater(caption, 0)