import wx
import sys


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
                self.main_sizer = wx.BoxSizer()
                self.image_ctrl = wx.StaticBitmap(self, wx.ID_ANY,
                                                  wx.BitmapFromImage(wx.EmptyImage(parent.w, parent.h)))
                self.main_sizer.Add(self.image_ctrl, 1, wx.EXPAND)
                self.SetSizerAndFit(self.main_sizer)
                self.main_sizer.Layout()

        self.images_panel = ImagesPanel(self)
        self.sizer.Add(self.images_panel, 1, wx.EXPAND)
        self.sizer.Add(self.video_panel, 1, wx.EXPAND)  # TODO: Align top

        self.SetSizer(self.sizer)
        self.Layout()

        if not single_screen:
            self.ShowFullScreen(True, wx.FULLSCREEN_ALL)

        handle = self.video_panel.GetHandle()
        if sys.platform.startswith('linux'):  # for Linux using the X Server
            parent.player.set_xwindow(handle)
        elif sys.platform == "win32":  # for Windows
            parent.player.set_hwnd(handle)
        elif sys.platform == "darwin":  # for MacOS
            parent.player.set_nsobject(handle)

    def load_zad(self, file_path, fit=True):
        img = wx.Image(file_path, wx.BITMAP_TYPE_ANY)
        if fit:
            w, h = img.GetWidth(), img.GetHeight()
            max_w, max_h = self.images_panel.image_ctrl.GetSize()
            target_ratio = min(max_w / float(w), max_h / float(h))
            new_w, new_h = [int(x * target_ratio) for x in (w, h)]
            img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
        self.images_panel.image_ctrl.SetBitmap(wx.BitmapFromImage(img))
        self.images_panel.main_sizer.Layout()

    def switch_to_video(self, e=None):
        self.video_panel.Show()
        self.images_panel.Hide()

    def switch_to_images(self, e=None):
        self.video_panel.Hide()
        self.images_panel.Show()

    def no_show(self):
        self.images_panel.image_ctrl.SetBitmap(
            wx.BitmapFromImage(wx.EmptyImage(*self.images_panel.image_ctrl.GetSize())))
        self.images_panel.main_sizer.Layout()
