import os
import wx


class Logger(object):
    def __init__(self, parent):
        self.parent = parent
        self.log_win = None
        self.log_text = "Init" + os.linesep

    def open_window(self, pre_close_func):
        self.log_win = LogWindow(self.parent)
        self.log_win.Show()
        self.log_win.append_message(self.log_text)

        def on_close(e):
            pre_close_func()
            self.log_win.Destroy()
            self.log_win = None
        self.log_win.Bind(wx.EVT_CLOSE, on_close)

    def log(self, msg):
        self.log_text += msg + os.linesep
        if self.log_win:
            self.log_win.append_message(msg + os.linesep)


class LogWindow(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title="FestEngine Log", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_ctrl = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE)
        main_sizer.Add(self.text_ctrl, 1, wx.EXPAND)

        self.pending_messages = list()
        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self.append_pending_messages)
        self.timer.Start(500)
        self.SetSizer(main_sizer)

    def append_pending_messages(self, e=None):
        if len(self.pending_messages) == 0:
            return
        for msg in self.pending_messages:
            self.text_ctrl.AppendText(msg)
        self.pending_messages = list()

    def append_message(self, msg):
        self.pending_messages.append(msg)
