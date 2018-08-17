import wx
from datetime import *
from constants import Config, Colors


class ProjectorWindow(wx.Frame):
    def __init__(self, parent, screen=None):
        self.main_window = parent

        run_windowed = wx.Display.GetCount() <= screen or wx.Display.GetCount() < 2
        if screen is None or run_windowed:
            screen = wx.Display.GetFromWindow(self.main_window)
        origin_x, origin_y, self.w, self.h = wx.Display(screen).GetGeometry().Get()

        wx.Frame.__init__(self, parent, pos=(origin_x + 60, origin_y + 60), size=(self.w - 120, self.h - 120),
                          title='Projector Window',
                          style=wx.DEFAULT_FRAME_STYLE | (0 if run_windowed else wx.STAY_ON_TOP))
        self.SetBackgroundColour(wx.BLACK)

        self.sizer = wx.BoxSizer()

        self.video_panel = wx.Panel(self)
        self.video_panel.SetBackgroundColour(wx.BLACK)
        self.video_panel.Hide()

        class ImagesPanel(wx.Panel):
            def __init__(self, parent):
                wx.Panel.__init__(self, parent)
                self.proj_window = parent

                self.SetBackgroundColour(wx.BLACK)
                self.drawable_bitmap = wx.Bitmap(wx.Image(self.proj_window.w, self.proj_window.h))
                self.SetBackgroundStyle(wx.BG_STYLE_ERASE)

                self.Bind(wx.EVT_SIZE, self.on_size)
                self.Bind(wx.EVT_PAINT, self.on_paint)
                self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)

            def on_size(self, e):
                self.Layout()
                self.Refresh()

            def on_erase_background(self, e):
                pass  # https://github.com/Himura2la/FestEngine/issues/30

            def on_paint(self, e):
                dc = wx.BufferedPaintDC(self)
                w, h = self.GetClientSize()
                if not w or not h:
                    return
                dc.Clear()
                drw_w = self.drawable_bitmap.GetWidth()
                dc.DrawBitmap(self.drawable_bitmap, w//2 - drw_w//2, 0)

        self.images_panel = ImagesPanel(self)

        class CountdownPanel(wx.Panel):
            def __init__(self, parent):
                wx.Panel.__init__(self, parent)
                self.proj_window = parent
                self.main_window = self.proj_window.main_window
                self.timer = wx.Timer()
                self.timer.Bind(wx.EVT_TIMER, self.update_time)
                self.time_left = timedelta()
                self.time_started = None
                self.time_end = None

                self.SetBackgroundColour(wx.BLACK)

                self.info_text = wx.StaticText(self, style=wx.ALIGN_CENTER_HORIZONTAL)
                self.countdown_text = wx.StaticText(self, style=wx.ALIGN_CENTER_HORIZONTAL)
                self.time_text = wx.StaticText(self, style=wx.ALIGN_CENTER_HORIZONTAL)

                self.countdown_text.SetForegroundColour(Colors.COUNTDOWN_TEXT_COLOR)
                self.info_text.SetForegroundColour(Colors.COUNTDOWN_TEXT_COLOR)
                self.time_text.SetForegroundColour(Colors.COUNTDOWN_TEXT_COLOR)

                sizer = wx.BoxSizer(wx.VERTICAL)

                sizer.AddStretchSpacer()
                sizer.Add(self.info_text, 0, wx.CENTER)
                sizer.Add(self.countdown_text, 0, wx.CENTER)
                sizer.Add(self.time_text, 0, wx.CENTER)
                sizer.AddStretchSpacer()

                self.SetSizer(sizer)
                self.Layout()

                self.Bind(wx.EVT_SIZE, self._recalculate_font_size)
                self._recalculate_font_size()

            def _recalculate_font_size(self, e=None):
                width, height = self.GetSize()
                width *= 3/4  # Assuming 4:3
                base_size = height if height < width else width
                font_height = base_size / 3

                font = self.countdown_text.GetFont()
                font.SetPixelSize(wx.Size(0, font_height))
                self.countdown_text.SetFont(font)

                font.SetPixelSize(wx.Size(0, font_height / 3))
                self.info_text.SetFont(font)
                self.time_text.SetFont(font)
                if e:
                    e.Skip()

            def start_timer(self, minutes, text):
                if not self.timer.IsRunning():
                    self.timer.Start(100)

                self.time_started = datetime.now() + timedelta(seconds=1)
                self.time_end = self.time_started + timedelta(minutes=minutes)

                self.info_text.SetLabel(text)
                self.time_text.SetLabel(self.main_window.config[Config.COUNTDOWN_TIME_FMT] %
                                        self.time_end.strftime("%H:%M"))
                self.update_time()

            def update_time(self, e=None):
                self.time_left = self.time_end - datetime.now()

                if self.time_left < timedelta(seconds=1):
                    def ui_upd():
                        self.proj_window.switch_to_images()
                        self.main_window.clear_zad(status=u"Poehali !!!")
                    wx.CallAfter(ui_upd)
                    return

                string_time = str(self.time_left)

                def ui_upd():
                    self.countdown_text.SetLabel(string_time[:string_time.find('.')])
                    self.Layout()
                    self.main_window.image_status("Countdown: %s" % string_time)
                wx.CallAfter(ui_upd)

        self.countdown_panel = CountdownPanel(self)
        self.countdown_panel.Hide()
        self.countdown_panel.SetDoubleBuffered(True)  # Fixes flickering

        self.sizer.Add(self.images_panel, 1, wx.EXPAND)
        self.sizer.Add(self.video_panel, 1, wx.EXPAND)  # TODO: Align top
        self.sizer.Add(self.countdown_panel, 1, wx.EXPAND)

        self.SetSizer(self.sizer)

        if not run_windowed:
            self.ShowFullScreen(True, wx.FULLSCREEN_ALL)

        self.Bind(wx.EVT_CLOSE, self.main_window.on_proj_win_close)

    def load_zad(self, file_path, fit=True):
        img = wx.Image(file_path, wx.BITMAP_TYPE_ANY)
        if fit:
            w, h = img.GetWidth(), img.GetHeight()
            max_w, max_h = self.images_panel.GetSize()
            target_ratio = min(max_w / float(w), max_h / float(h))
            new_w, new_h = [int(x * target_ratio) for x in (w, h)]
            img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
        self.images_panel.drawable_bitmap = wx.Bitmap(img)
        self.images_panel.Refresh()

    def switch_to_video(self, e=None):
        if self.countdown_panel.IsShown():
            self.countdown_panel.timer.Stop()
            self.countdown_panel.Hide()
        self.video_panel.Show()
        self.images_panel.Hide()

    def switch_to_images(self, e=None):
        if self.countdown_panel.IsShown():
            self.countdown_panel.timer.Stop()
            self.countdown_panel.Hide()
        self.video_panel.Hide()
        self.images_panel.Show()

    def launch_timer(self, time, text):
        self.video_panel.Hide()
        self.images_panel.Hide()
        self.countdown_panel.Show()
        self.Layout()

        if time[-1] == 'm':  # Assuming duration
            try:
                minutes = float(time[:-1])
            except:
                return False
        elif ':' in time:  # Assuming time
            try:
                time = datetime.strptime(time, '%H:%M')
                now = datetime.now()
                time = now.replace(hour=time.hour, minute=time.minute + 1, second=0, microsecond=0)
                minutes = (time - now).seconds // 60
            except:
                return False
        self.countdown_panel.start_timer(minutes, text)
        return True

    def no_show(self):
        self.images_panel.drawable_bitmap = \
            wx.Bitmap(wx.Image(*self.images_panel.drawable_bitmap.GetSize()))
        self.images_panel.Refresh()


