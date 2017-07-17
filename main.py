#!python
import wx
import wx.grid
import webbrowser
import os
from projector_window import ProjectorWindow

zad_path = "H:\ownCloud\DATA\Yuki no Odori 2016\Fest\zad_numbered"
mp3_path = "H:\ownCloud\DATA\Yuki no Odori 2016\Fest\mp3_numbered"


class MainFrame(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(700, 500))
        accelerator_table = []
        self.proj_win = ProjectorWindow(self)

        # ------------------ Menu ------------------
        menu_bar = wx.MenuBar()
        self.Bind(wx.EVT_MENU_OPEN, self.on_menu_open)

        # --- File ---
        menu_file = wx.Menu()
        menu_file_about = menu_file.Append(wx.ID_ABOUT, "&About")
        self.Bind(wx.EVT_MENU, self.on_about, menu_file_about)
        menu_file_exit = menu_file.Append(wx.ID_EXIT, "E&xit")
        self.Bind(wx.EVT_MENU, self.on_exit, menu_file_exit)
        menu_bar.Append(menu_file, "&File")

        # --- Projector Window ---
        proj_win_menu = wx.Menu()
        proj_win_menu_create = proj_win_menu.Append(wx.NewId(), "&Create")
        self.Bind(wx.EVT_MENU, self.create_proj_win, proj_win_menu_create)
        menu_bar.Append(proj_win_menu, "&Projector Window")

        # --- Play ---
        menu_play = wx.Menu()
        menu_play_zad = menu_play.Append(wx.NewId(), "&Show ZAD\tF1")
        self.Bind(wx.EVT_MENU, self.show_zad, menu_play_zad)
        accelerator_table.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F1, menu_play_zad.GetId()))
        menu_bar.Append(menu_play, "&Play")

        # --- Load Data ---
        self.menu_load = wx.Menu()
        menu_bar.Append(self.menu_load, "&Load Data")

        self.SetMenuBar(menu_bar)

        # ------------------ Main Sizer ------------------
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

    def on_about(self, e):
        webbrowser.open('https://github.com/Himura2la')

    def on_exit(self, e):
        self.Close(True)
        self.proj_win.Close(True)

    def on_menu_open(self, event):
        if event.GetMenu() == self.menu_load:
            self.read_zad()

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

    def create_proj_win(self, event):
        self.proj_win.Show()

    def read_zad(self):
        file_names = os.listdir(zad_path)
        self.grid_set_shape(len(file_names), 1)
        for i in range(len(file_names)):
            self.grid.SetCellValue(i, 0, file_names[i])
            self.grid.SetReadOnly(i, 0)
        self.grid.AutoSizeColumns()

    def show_zad(self, event):
        self.status("show_zad")


app = wx.App(False)
frame = MainFrame(None, 'Fest Engine')
app.MainLoop()
