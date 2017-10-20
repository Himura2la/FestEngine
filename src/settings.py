import wx

from constants import Config


class SettingsDialog(wx.Dialog):
    def __init__(self, session_file_path, config, parent):
        wx.Dialog.__init__(self, parent, title="Settings", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.session_file_path = session_file_path
        self.config = config

        top_sizer = wx.BoxSizer(wx.VERTICAL)
        panel = wx.Panel(self)

        session_sizer = wx.BoxSizer(wx.HORIZONTAL)
        session_sizer.Add(wx.StaticText(panel, label="Current Fest"), 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)
        self.session_picker = wx.FilePickerCtrl(panel, style=wx.FLP_OPEN | wx.FLP_USE_TEXTCTRL, wildcard="*.fest")
        self.session_picker.SetPath(self.session_file_path)
        session_sizer.Add(self.session_picker, 1, wx.EXPAND | wx.ALL, 5)
        top_sizer.Add(session_sizer, 0, wx.EXPAND)

        # Grid

        top_sizer.Add(wx.StaticLine(panel), 0, wx.ALL | wx.EXPAND, 5)

        configs_grid = wx.FlexGridSizer(rows=5, cols=2, hgap=5, vgap=5)
        configs_grid.AddGrowableCol(1)

        self.screens_combobox = wx.Choice(panel)
        screen_names = ["%d: %s (%d,%d) %dx%d" % ((i, wx.Display(i).GetName()) + wx.Display(i).GetGeometry().Get())
                        for i in range(wx.Display.GetCount())]
        self.screens_combobox.SetItems(screen_names)
        self.screens_combobox.SetSelection(self.config[Config.PROJECTOR_SCREEN])
        configs_grid.Add(wx.StaticText(panel, label=Config.PROJECTOR_SCREEN), 0, wx.ALIGN_CENTER_VERTICAL)
        configs_grid.Add(self.screens_combobox, 1, wx.EXPAND)

        self.filename_re = wx.TextCtrl(panel)
        self.filename_re.SetValue(self.config[Config.FILENAME_RE])
        configs_grid.Add(wx.StaticText(panel, label=Config.FILENAME_RE), 0, wx.ALIGN_CENTER_VERTICAL)
        configs_grid.Add(self.filename_re, 1, wx.EXPAND)

        self.bg_tracks = wx.DirPickerCtrl(panel)
        self.bg_tracks.SetPath(self.config[Config.BG_TRACKS_DIR])
        configs_grid.Add(wx.StaticText(panel, label=Config.BG_TRACKS_DIR), 0, wx.ALIGN_CENTER_VERTICAL)
        configs_grid.Add(self.bg_tracks, 1, wx.EXPAND)

        self.bg_zad = wx.FilePickerCtrl(panel)
        self.bg_zad.SetPath(self.config[Config.BG_ZAD_PATH])
        configs_grid.Add(wx.StaticText(panel, label=Config.BG_ZAD_PATH), 0, wx.ALIGN_CENTER_VERTICAL)
        configs_grid.Add(self.bg_zad, 1, wx.EXPAND)

        top_sizer.Add(configs_grid, 0, wx.EXPAND | wx.ALL, 5)

        # --- Dirs ---

        dirs_box = wx.StaticBox(panel, label=Config.FILES_DIRS)
        dirs_box_sizer = wx.StaticBoxSizer(dirs_box, wx.VERTICAL)
        pickers_sizer = wx.BoxSizer(wx.VERTICAL)

        self.dir_pickers = []

        def add_dir(path=None):
            dir_picker = wx.DirPickerCtrl(panel)
            pickers_sizer.Add(dir_picker, 0, wx.EXPAND)
            if isinstance(path, str):  # Assuming initial calls
                dir_picker.SetPath(path)
            else:   # Assuming manual adding
                top_sizer.Layout()
                size = self.GetSize()
                size[1] += dir_picker.GetSize()[1]
                self.SetSize(size)
            self.dir_pickers.append(dir_picker)

        for path in self.config[Config.FILES_DIRS]:
            add_dir(path)

        # Add / Remove

        dir_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        add_btn = wx.Button(panel, label="+")
        add_btn.Bind(wx.EVT_BUTTON, add_dir)
        dir_buttons_sizer.Add(add_btn, 1)

        def rm_dir(e=None):
            last_picker_height = self.dir_pickers[-1].GetSize()[1]
            last_picker = len(self.dir_pickers) - 1
            if last_picker > 0:
                del self.dir_pickers[-1]
                pickers_sizer.Hide(last_picker)
                pickers_sizer.Remove(last_picker)
                top_sizer.Layout()
                size = self.GetSize()
                size[1] -= last_picker_height
                self.SetSize(size)

        rm_dir_btn = wx.Button(panel, label="-")
        rm_dir_btn.Bind(wx.EVT_BUTTON, rm_dir)
        dir_buttons_sizer.Add(rm_dir_btn, 1)

        dirs_box_sizer.Add(pickers_sizer, 0, wx.EXPAND)
        dirs_box_sizer.Add(dir_buttons_sizer, 0, wx.EXPAND)

        top_sizer.Add(dirs_box_sizer, 0, wx.ALL | wx.EXPAND, 5)

        # --- OK / Cancel ---

        top_sizer.Add(wx.StaticLine(panel), 0, wx.ALL | wx.EXPAND, 5)

        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)

        button_load = wx.Button(panel, wx.ID_OPEN, "Load")
        buttons_sizer.Add(button_load, 1)
        button_load.Bind(wx.EVT_BUTTON, self.on_ok)

        button_save = wx.Button(panel, wx.ID_SAVE, "Save")
        buttons_sizer.Add(button_save, 1)
        button_save.Bind(wx.EVT_BUTTON, self.on_ok)

        button_cancel = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        buttons_sizer.Add(button_cancel, 1)

        top_sizer.Add(buttons_sizer, 0, wx.EXPAND | wx.ALL, 5)
        panel.SetSizerAndFit(top_sizer)
        self.Fit()

        self.SetSize((800, self.GetSize()[1]))

    def on_ok(self, e):
        self.session_file_path = self.session_picker.GetPath()

        self.config[Config.PROJECTOR_SCREEN] = self.screens_combobox.GetSelection()
        self.config[Config.FILENAME_RE] = self.filename_re.GetValue()
        self.config[Config.BG_TRACKS_DIR] = self.bg_tracks.GetPath()
        self.config[Config.BG_ZAD_PATH] = self.bg_zad.GetPath()
        self.config[Config.FILES_DIRS] = [picker.GetPath() for picker in self.dir_pickers]

        self.EndModal(e.Id)

