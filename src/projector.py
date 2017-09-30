from datetime import *
import wx


class ProjectorWindow(wx.Frame):
    def __init__(self, parent, screen=None):
        if screen is None:
            screen = wx.Display.GetCount() - 1
        origin_x, origin_y, self.w, self.h = wx.Display(screen).GetGeometry().Get()
        single_screen = wx.Display.GetCount() < 2

        wx.Frame.__init__(self, parent, pos=(origin_x + 60, origin_y + 60), size=(self.w - 120, self.h - 120),
                          title='Projector Window',
                          style=wx.DEFAULT_FRAME_STYLE | (0 if single_screen else wx.STAY_ON_TOP))
        self.SetBackgroundColour(wx.BLACK)

        self.sizer = wx.BoxSizer()

        self.video_panel = wx.Panel(self)
        self.video_panel.SetBackgroundColour(wx.BLACK)
        self.video_panel.Hide()

        class ImagesPanel(wx.Panel):
            def __init__(self, parent):
                wx.Panel.__init__(self, parent)

                self.SetBackgroundColour(wx.BLACK)
                self.drawable_bitmap = wx.Bitmap(wx.Image(parent.w, parent.h))
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
                self.parent = parent
                self.timer = wx.Timer()
                self.timer.Bind(wx.EVT_TIMER, self.update_time)
                self.time_remain = timedelta()
                self.time_started = None
                self.time_end = None

                self.label = wx.StaticText(self, label="00:00")
                self.label.SetForegroundColour((255, 255, 255, 255))  # To settings!

                h_sizer = wx.BoxSizer(wx.HORIZONTAL)
                v_sizer = wx.BoxSizer(wx.VERTICAL)

                h_sizer.AddStretchSpacer()
                h_sizer.Add(v_sizer, 0)
                h_sizer.AddStretchSpacer()

                v_sizer.AddStretchSpacer()
                v_sizer.Add(self.label, 1)
                v_sizer.AddStretchSpacer()

                self.SetSizer(h_sizer)
                self.Layout()

                self.Bind(wx.EVT_SIZE, self._recalculate_font_size)
                self._recalculate_font_size()

            def _recalculate_font_size(self, e=None):
                font = self.label.GetFont()
                font_height = self.GetSize().height / 4
                font.SetPixelSize(wx.Size(0, font_height))
                self.label.SetFont(font)
                if e:
                    e.Skip()

            def start_timer(self, minutes):
                if not self.timer.IsRunning():
                    self.timer.Start(300)

                self.time_started = datetime.now()
                self.time_end = self.time_started + timedelta(minutes=minutes)
                self.update_time()

            def update_time(self, e=None):
                self.time_remain = self.time_end - datetime.now()
                string_time = str(self.time_remain)

                def update_ui():
                    self.label.SetLabel(string_time[:string_time.find('.')])
                    self.Layout()
                wx.CallAfter(update_ui)

        self.countdown_panel = CountdownPanel(self)
        self.countdown_panel.Hide()
        self.countdown_panel.SetDoubleBuffered(True)  # Fixes flickering

        self.sizer.Add(self.images_panel, 1, wx.EXPAND)
        self.sizer.Add(self.video_panel, 1, wx.EXPAND)  # TODO: Align top
        self.sizer.Add(self.countdown_panel, 1, wx.EXPAND)

        self.SetSizer(self.sizer)

        if not single_screen:
            self.ShowFullScreen(True, wx.FULLSCREEN_ALL)

        def on_close(e):
            self.countdown_panel.timer.Stop()
            self.Destroy()
        self.Bind(wx.EVT_CLOSE, on_close)

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
        self.countdown_panel.Hide()
        self.video_panel.Show()
        self.images_panel.Hide()

    def switch_to_images(self, e=None):
        self.countdown_panel.Hide()
        self.video_panel.Hide()
        self.images_panel.Show()

    def launch_timer(self, timedelta):
        self.video_panel.Hide()
        self.images_panel.Hide()
        self.countdown_panel.Show()
        self.Layout()
        self.countdown_panel.start_timer(timedelta)

    def on_timer_ranout(self, e):
        self.switch_to_images()
        self.no_show()

    def no_show(self):
        self.images_panel.drawable_bitmap = \
            wx.Bitmap(wx.Image(*self.images_panel.drawable_bitmap.GetSize()))
        self.images_panel.Refresh()


