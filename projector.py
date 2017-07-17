import wx


class ProjectorWindow(wx.Frame):
    def __init__(self, parent, screen=None):
        wx.Frame.__init__(self, parent, title='Projector Window',
                          style=wx.DEFAULT_MINIFRAME_STYLE | wx.CLOSE_BOX)
        if screen is None:
            screen = wx.Display.GetCount() - 1
        origin_x, origin_y, w, h = wx.Display(screen).GetGeometry().Get()

        self.SetPosition((origin_x + 55, origin_y + 55))

        self.SetBackgroundColour((0, 0, 0, 255))

        self.main_sizer = wx.BoxSizer()
        self.image_ctrl = wx.StaticBitmap(self, wx.ID_ANY,
                                          wx.BitmapFromImage(wx.EmptyImage(w, h)))
        self.main_sizer.Add(self.image_ctrl, 1, wx.EXPAND)
        self.SetSizer(self.main_sizer)

    def load_zad(self, file_path, fit=True):
        img = wx.Image(file_path, wx.BITMAP_TYPE_ANY)
        if fit:
            w, h = img.GetWidth(), img.GetHeight()
            max_w, max_h = self.image_ctrl.GetSize()
            target_ratio = min(max_w / float(w), max_h / float(h))
            new_w, new_h = [int(x * target_ratio) for x in (w, h)]
            img = img.Scale(new_w, new_h)
        self.image_ctrl.SetBitmap(wx.BitmapFromImage(img))
        self.main_sizer.Layout()
