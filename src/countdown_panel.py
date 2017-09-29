import wx
import wx.lib.newevent
import datetime
import time

CountdownPanelEvent, EVT_COUNTDOWN_RANOUT_EVENT = wx.lib.newevent.NewEvent()

class CountdownPanel(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(CountdownPanel, self).__init__(parent, id, pos, size, style, name)
        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self._on_timer)
        self.end_time = 0

        self.label = wx.StaticText(self, label="00:00:00", style=wx.ALIGN_CENTRE_HORIZONTAL)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add((0,0), 1, wx.EXPAND)
        sizer.Add(self.label, 0, wx.CENTER | wx.ALL)
        sizer.Add((0,0), 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_SIZE, self._on_resize)
        self._recalculate_font_size()

    def start_timer(self, timedelta):
        if self.timer.IsRunning():
            self.timer.Stop()
        self.timer.Start(1000)
        seconds = timedelta
        if (type(timedelta) is datetime.timedelta):
            seconds = timedelta.total_seconds()
        self.end_time = time.time() + seconds
        self._update_label()

    def _recalculate_font_size(self):
        font = self.label.GetFont()
        fontHeight = self.GetSize().height / 4
        font.SetPixelSize(wx.Size(0, fontHeight))
        self.label.SetFont(font)

    def _on_resize(self, e):
        self._recalculate_font_size()
        e.Skip()

    def _on_timer(self, e):
        self._update_label()

    def _update_label(self):
        seconds = int(round(self.end_time - time.time()))
        if seconds < 0:
            self.timer.Stop()
            wx.PostEvent(self.GetEventHandler(), CountdownPanelEvent())
            return
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        self.label.SetLabel( "{:0>2}:{:0>2}:{:0>2}".format(hours, minutes, seconds) )
