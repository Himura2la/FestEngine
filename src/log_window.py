import wx


class LogWindow(wx.Dialog):
    def __init__(self, parent, close_handler):
        wx.Dialog.__init__(self, parent, title="FestEngine Log", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.close_handler = close_handler
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE)
        main_sizer.Add(self.text_ctrl, 1, wx.EXPAND)

        self.SetSizer(main_sizer)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def append(self, text):
        self.text_ctrl.AppendText(text)

    def on_close(self, e):
        self.close_handler()
        self.Destroy()
