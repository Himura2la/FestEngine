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
        self.window = None

    def create_window(self):
        self.window = BackgroundMusicFrame(self.parent)
        self.window.Show()

    def play(self, fade_in=True):
        pass

    def pause(self, fade_out=True):
        pass


class BackgroundMusicFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title='Background Music Player', size=(700, 500))

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.toolbar = wx.BoxSizer(wx.HORIZONTAL)

        # --- Table ---
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(1, 1)
        self.grid.HideRowLabels()
        self.grid.DisableDragRowSize()
        self.grid.SetColLabelSize(20)
        self.grid.SetCellValue(0, 0, "Empty Playlist")
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

