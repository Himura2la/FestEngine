import os
from ctypes import CDLL, c_ulong, c_void_p
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
import unittest


def check_projector(clip):
    # Start exactly as the application does, before anything initializes GTK.
    src = Path(__file__).resolve().parents[1] / 'src'
    sys.path.insert(0, str(src))
    main = runpy.run_path(str(src / 'main.pyw'))
    wx = main['wx']
    app = wx.App(False)
    host = wx.Frame(None)
    host.on_proj_win_close = lambda event: event.Skip()
    host.proj_win = main['ProjectorWindow'](host, 0)
    host.proj_win.SetSize((320, 240))
    host.proj_win.Show()
    host.proj_win.switch_to_video()
    app.Yield()
    host.config = {main['Config'].VLC_ARGUMENTS: ''}
    host.vlc_instance = instance = main['vlc'].Instance('--no-audio')
    host.player = instance.media_player_new()
    try:
        panel = host.proj_win.video_panel
        assert 0 < panel.GetHandle() <= 0xffffffff, 'panel handle is not an X11 window ID'
        assert main['MainWindow'].set_vlc_video_panel(host)
        host.player.set_media(main['MainWindow'].projector_media(host, clip))
        host.player.video_set_deinterlace('blend')
        assert host.player.play() == 0
        # XWayland does not expose the compositor's desktop to wx.ScreenDC.
        # Read the panel's own drawable, including the embedded VLC child.
        x11 = CDLL('libX11.so.6')
        x11.XOpenDisplay.restype = x11.XGetImage.restype = c_void_p
        display = c_void_p(x11.XOpenDisplay(None))
        assert display
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            app.Yield()
            image = c_void_p(x11.XGetImage(display, c_ulong(panel.GetHandle()), panel.Size.width // 2,
                                           panel.Size.height // 2, 1, 1, c_ulong(-1), 2))
            assert image
            pixel = x11.XGetPixel(image, 0, 0)
            x11.XDestroyImage(image)
            if (pixel >> 16 & 255) > 180 and (pixel >> 8 & 255) < 60 and (pixel & 255) < 60:
                return
            time.sleep(0.05)
        raise AssertionError(f'Expected red video inside the projector; last pixel: {pixel}')
    finally:
        host.player.stop()
        host.player.release()
        instance.release()
        host.Destroy()


class LinuxVideoTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith('linux') and os.environ.get('DISPLAY')
                         and shutil.which('ffmpeg'), 'requires X11/XWayland and ffmpeg')
    def test_wayland_preference_still_embeds_video(self):
        with tempfile.TemporaryDirectory() as directory:
            clip = str(Path(directory) / 'red.mp4')
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'lavfi', '-i',
                            'color=red:size=160x120:duration=6', '-c:v', 'libx264', clip], check=True)
            result = subprocess.run([sys.executable, __file__, clip], timeout=20,
                                    env=dict(os.environ, GDK_BACKEND='wayland,x11'),
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    check_projector(sys.argv[1])