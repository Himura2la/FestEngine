import os

import vlc
import wx
import wx.grid


class BackgroundMusicPlayer(object):
    def __init__(self, parent):
        self.parent = parent
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.player.audio_set_volume(50)
        self.player.audio_set_mute(False)
        self.window = BackgroundMusicFrame(self.parent)  # None
        self.playlist = None
        self._fade_in_out = True

    @property
    def fade_in_out(self):
        return self._fade_in_out

    @fade_in_out.setter
    def fade_in_out(self, value):
        self.window.fade_in_out_switch.SetValue(value)
        self._fade_in_out = value

    def show_window(self):
        if not isinstance(self.window, BackgroundMusicFrame):
            self.window = BackgroundMusicFrame(self.parent)
        self.window.Show()
        self.window.fade_in_out_switch.SetValue(self.fade_in_out)
        self.window.vol_slider.SetValue(self.player.audio_get_volume())
        self.window.set_volume_from_slider()

    def play(self):

        if self.fade_in_out:
            pass

    def pause(self):

        if self.fade_in_out:
            pass
        pass

    def load_files(self, dir):
        file_names = sorted(os.listdir(dir))
        self.playlist = [{'name': f.rsplit('.', 1)[0], 'path': os.path.join(dir, f)} for f in file_names]
        if self.window.grid.GetNumberRows() > 0:
            self.window.grid.DeleteRows(0, self.window.grid.GetNumberRows(), False)
        self.window.grid.AppendRows(len(self.playlist))
        for i in range(len(self.playlist)):
            self.window.grid.SetCellValue(i, 0, self.playlist[i]['name'])
            self.window.grid.SetReadOnly(i, 0)
        self.window.grid.AutoSize()
        self.window.Layout()


class BackgroundMusicFrame(wx.Frame):
    def __init__(self, parent):
        self.parent = parent
        wx.Frame.__init__(self, parent, title='Background Music Player', size=(400, 500))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.toolbar = wx.BoxSizer(wx.HORIZONTAL)
        toolbar_base_height = 20

        self.fade_in_out_switch = wx.CheckBox(self, label='FAD')
        self.toolbar.Add(self.fade_in_out_switch, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=3)

        self.play_btn = wx.Button(self, label="Play", size=(70, toolbar_base_height + 2))
        self.toolbar.Add(self.play_btn, 0)
        self.play_btn.Bind(wx.EVT_BUTTON, parent.background_play)
        # Forwarding events through the main window, because this frame is optional and may be absent.

        self.stop_btn = wx.Button(self, label="Stop", size=(70, toolbar_base_height + 2))
        self.toolbar.Add(self.stop_btn, 0)
        self.stop_btn.Bind(wx.EVT_BUTTON, parent.background_stop)

        self.vol_slider = wx.Slider(self, value=0, minValue=0, maxValue=150)
        self.toolbar.Add(self.vol_slider, 1, wx.EXPAND)
        self.vol_label = wx.StaticText(self, label='VOL', size=(50, -1), style=wx.ALIGN_LEFT)
        self.toolbar.Add(self.vol_label, 0, wx.ALIGN_CENTER_VERTICAL)

        self.vol_slider.Bind(wx.EVT_SLIDER, self.set_volume_from_slider)

        # --- Table ---
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 1)
        self.grid.HideColLabels()
        self.grid.DisableDragRowSize()
        self.grid.SetRowLabelSize(20)
        self.grid.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)

        def select_row(e):
            row = e.Row if hasattr(e, 'Row') else e.TopRow
            self.grid.Unbind(wx.grid.EVT_GRID_RANGE_SELECT)
            self.grid.SelectRow(row)
            self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)

        self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, select_row)
        self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)

        main_sizer.Add(self.toolbar, 0, wx.EXPAND)
        main_sizer.Add(self.grid, 1, wx.EXPAND | wx.TOP, border=1)

        self.SetSizer(main_sizer)
        self.Layout()

    def set_volume_from_slider(self, e=None):
        value = self.vol_slider.GetValue()
        self.parent.background_volume = value  # Forwards to player
        self.vol_label.SetLabel('VOL: %d' % self.parent.background_volume)  # Gets from player
