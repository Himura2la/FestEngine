import wx


class ProjectorPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, name='Projector Panel')

        self.SetBackgroundColour(wx.BLACK)
        self.main_sizer = wx.BoxSizer()
        self.image_ctrl = wx.StaticBitmap(self, wx.ID_ANY,
                                          wx.BitmapFromImage(wx.EmptyImage(parent.w, parent.h)))
        self.main_sizer.Add(self.image_ctrl, 1, wx.EXPAND)
        self.SetSizerAndFit(self.main_sizer)
        self.main_sizer.Layout()


class ProjectorWindow(wx.Frame):
    def __init__(self, parent, screen=None):
        if screen is None:
            screen = wx.Display.GetCount() - 1
        origin_x, origin_y, self.w, self.h = wx.Display(screen).GetGeometry().Get()
        wx.Frame.__init__(self, parent, pos=(origin_x + 60, origin_y + 60), size=(self.w - 120, self.h - 120),
                          title='Projector Window', style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)

        self.panel = ProjectorPanel(self)  # Obligatory

        self.ShowFullScreen(True, wx.FULLSCREEN_ALL)

    def load_zad(self, file_path, fit=True):
        img = wx.Image(file_path, wx.BITMAP_TYPE_ANY)
        if fit:
            w, h = img.GetWidth(), img.GetHeight()
            max_w, max_h = self.panel.image_ctrl.GetSize()
            target_ratio = min(max_w / float(w), max_h / float(h))
            new_w, new_h = [int(x * target_ratio) for x in (w, h)]
            img = img.Scale(new_w, new_h)
        self.panel.image_ctrl.SetBitmap(wx.BitmapFromImage(img))
        self.panel.main_sizer.Layout()

    def no_show(self):
        self.panel.image_ctrl.SetBitmap(wx.BitmapFromImage(wx.EmptyImage(*self.panel.image_ctrl.GetSize())))
        self.panel.main_sizer.Layout()
