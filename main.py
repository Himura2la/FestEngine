#!python
import wx
import wx.grid
import webbrowser
import os

zad_path = "H:\ownCloud\DATA\Yuki no Odori 2016\Fest\zad_numbered"
mp3_path = "H:\ownCloud\DATA\Yuki no Odori 2016\Fest\mp3_numbered"


class MainFrame(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(700, 500))

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

        # --- Load Data ---
        self.menu_load = wx.Menu()
        menu_bar.Append(self.menu_load, "&Load Data")

        self.SetMenuBar(menu_bar)

        # ------------------ Main Sizer ------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # --- Table ---
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(1, 1)

        main_sizer.Add(self.grid, 1, wx.EXPAND)

        self.SetSizer(main_sizer)

        # ------------------ Status Bar ------------------
        self.status_bar = self.CreateStatusBar(3)

        self.status("Ready")

        self.Show(True)

    def status(self, text):
        self.status_bar.SetStatusText(text, 0)

    def on_about(self, e):
        webbrowser.open('https://github.com/Himura2la')

    def on_exit(self, e):
        self.Close(True)

    def on_menu_open(self, event):
        if event.GetMenu() == self.menu_load:
            self.read_zad()

    # ----------------------------------------------------

    def read_zad(self):
        """Assuming grid shape is 1x1"""
        file_names = os.listdir(zad_path)
        self.grid.AppendRows(len(file_names) - 1)
        for i in range(len(file_names)):
            self.grid.SetCellValue(i, 0, file_names[i])
        pass




app = wx.App(False)
frame = MainFrame(None, 'Fest Engine')
app.MainLoop()
