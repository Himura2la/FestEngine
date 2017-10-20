import wx

from constants import Config


class SettingsDialog(wx.Dialog):
    def __init__(self, settings, parent):
        wx.Dialog.__init__(self, parent, title="Settings")
        self.settings = settings

        panel = wx.Panel(self)

        button_ok = wx.Button(panel, wx.ID_OK, "OK")
        button_ok.Bind(wx.EVT_BUTTON, self.on_ok)
        button_cancel = wx.Button(panel, wx.ID_CANCEL, "Cancel")

        self.screens_combobox = wx.Choice(panel)
        screen_names = ["%d: %s (%d,%d) %dx%d" % ((i, wx.Display(i).GetName()) + wx.Display(i).GetGeometry().Get())
                        for i in range(wx.Display.GetCount())]
        self.screens_combobox.SetItems(screen_names)
        self.screens_combobox.SetSelection(self.settings[Config.PROJECTOR_SCREEN])

        self.filename_re = wx.TextCtrl(panel)
        self.filename_re.SetValue(self.settings[Config.FILENAME_RE])

        self.bg_tracks = wx.DirPickerCtrl(panel)
        self.bg_tracks.SetPath(self.settings[Config.BG_TRACKS_DIR])

        self.bg_zad = wx.FilePickerCtrl(panel)
        self.bg_zad.SetPath(self.settings[Config.BG_ZAD_PATH])



        # --- Layout ---

        # Grid
        configs_grid = wx.FlexGridSizer(rows=5, cols=2, hgap=5, vgap=5)

        configs_grid.Add(wx.StaticText(panel, label=Config.PROJECTOR_SCREEN), 0, wx.ALIGN_CENTER_VERTICAL)
        configs_grid.Add(self.screens_combobox, 1, wx.EXPAND)

        configs_grid.Add(wx.StaticText(panel, label=Config.FILENAME_RE), 0, wx.ALIGN_CENTER_VERTICAL)
        configs_grid.Add(self.filename_re, 1, wx.EXPAND)

        configs_grid.Add(wx.StaticText(panel, label=Config.BG_TRACKS_DIR), 0, wx.ALIGN_CENTER_VERTICAL)
        configs_grid.Add(self.bg_tracks, 1, wx.EXPAND)

        configs_grid.Add(wx.StaticText(panel, label=Config.BG_ZAD_PATH), 0, wx.ALIGN_CENTER_VERTICAL)
        configs_grid.Add(self.bg_zad, 1, wx.EXPAND)



        # OK / Cancel
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons_sizer.Add(button_ok, 1)
        buttons_sizer.Add(button_cancel, 1)

        # Top level
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(configs_grid, 0, wx.EXPAND | wx.ALL, 5)
        top_sizer.Add(wx.StaticLine(panel), 0, wx.ALL | wx.EXPAND, 5)
        top_sizer.Add(buttons_sizer, 0, wx.EXPAND | wx.ALL, 5)
        panel.SetSizerAndFit(top_sizer)
        self.Fit()

    def on_ok(self, e):
        self.settings[Config.PROJECTOR_SCREEN] = self.screens_combobox.GetSelection()

        self.EndModal(wx.ID_OK)

