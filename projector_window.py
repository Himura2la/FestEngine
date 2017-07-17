import wx


class ProjectorWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, None, size=(700, 500), title='Projector Window')
        self.control_window = parent
