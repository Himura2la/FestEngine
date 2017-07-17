#!python
import wx
import wx.grid
import webbrowser
import os
from projector import ProjectorWindow
from settings import SettingsDialog
from strings import Config

# TODO: Move this to settings or calculate
zad_path = "H:\ownCloud\DATA\Yuki no Odori 2016\Fest\zad_numbered"
mp3_path = "H:\ownCloud\DATA\Yuki no Odori 2016\Fest\mp3_numbered"
proj_window_shape = (700, 500)


class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(700, 500))
        accelerator_table = []
        self.proj_win = None
        self.settings = {Config.PROJECTOR_SCREEN: wx.Display.GetCount() - 1}  # The last one

        # ------------------ Menu ------------------
        menu_bar = wx.MenuBar()

        # --- File ---
        menu_file = wx.Menu()
        self.Bind(wx.EVT_MENU, self.load_data,
                  menu_file.Append(wx.ID_ANY, "&Load Data"))
        self.Bind(wx.EVT_MENU, self.on_settings,
                  menu_file.Append(wx.ID_ANY, "&Setings"))

        self.Bind(wx.EVT_MENU, lambda _: webbrowser.open('https://github.com/Himura2la'),
                  menu_file.Append(wx.ID_ABOUT, "&About"))
        self.Bind(wx.EVT_MENU, self.on_exit,
                  menu_file.Append(wx.ID_EXIT, "E&xit"))
        menu_bar.Append(menu_file, "&File")

        # --- Projector Window ---
        proj_win_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, self.create_proj_win,
                  proj_win_menu.Append(wx.ID_ANY, "&Create"))
        self.Bind(wx.EVT_MENU, self.destroy_proj_win,
                  proj_win_menu.Append(wx.ID_ANY, "&Destroy"))

        menu_bar.Append(proj_win_menu, "&Projector Window")

        # --- Play ---
        menu_play = wx.Menu()
        menu_play_zad = menu_play.Append(wx.ID_ANY, "&Show ZAD\tF1")
        self.Bind(wx.EVT_MENU, self.show_zad, menu_play_zad)
        accelerator_table.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F1, menu_play_zad.GetId()))
        menu_bar.Append(menu_play, "&Play")

        self.SetMenuBar(menu_bar)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Table ---
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(1, 1)
        self.grid.HideRowLabels()
        self.grid.HideColLabels()
        self.grid.SetCellValue(0, 0, "Hello")

        main_sizer.Add(self.grid, 1, wx.EXPAND)

        self.SetSizer(main_sizer)

        # ------------------ Status Bar ------------------
        self.status_bar = self.CreateStatusBar(3)

        self.status("Ready")

        self.SetAcceleratorTable(wx.AcceleratorTable(accelerator_table))
        self.Show(True)

    def status(self, text):
        self.status_bar.SetStatusText(text, 0)

    def on_exit(self, e):
        self.destroy_proj_win()
        self.Close(True)

    def on_settings(self, e):
        settings_dialog = SettingsDialog(self.settings, self)
        res = settings_dialog.ShowModal()
        if res == wx.ID_OK:
            self.settings = settings_dialog.get_settings()
        settings_dialog.Destroy()

    def grid_set_shape(self, new_rows, new_cols):
        current_rows, current_cols = self.grid.GetNumberRows(), self.grid.GetNumberCols()
        if new_rows < current_rows:
            self.grid.DeleteRows(0, current_rows - new_rows, True)
        elif new_rows > current_rows:
            self.grid.AppendRows(new_rows - current_rows)
        if new_cols < current_cols:
            self.grid.DeleteCols(0, current_cols - new_cols, True)
        elif new_cols > current_cols:
            self.grid.AppendCols(new_cols - current_cols)

    # ----------------------------------------------------

    def create_proj_win(self, e=None):
        if not isinstance(self.proj_win, ProjectorWindow):
            self.proj_win = ProjectorWindow(self, self.settings[Config.PROJECTOR_SCREEN])
        self.proj_win.Show()

    def destroy_proj_win(self, e=None):
        if isinstance(self.proj_win, ProjectorWindow):
            self.proj_win.Close(True)

    def load_data(self, e):
        self.read_zad()

    def read_zad(self):
        file_names = os.listdir(zad_path)
        self.grid_set_shape(len(file_names), 1)
        for i in range(len(file_names)):
            self.grid.SetCellValue(i, 0, file_names[i])
            self.grid.SetReadOnly(i, 0)
        self.grid.AutoSizeColumns()

    def show_zad(self, e):
        self.create_proj_win()

        row = self.grid.GetGridCursorRow()
        file_name = self.grid.GetCellValue(row, 0)
        file_path = os.path.join(zad_path, file_name)
        self.proj_win.load_zad(file_path, True)


app = wx.App(False)
frame = MainFrame(None, 'Fest Engine')
app.MainLoop()
