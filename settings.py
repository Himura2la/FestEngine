import wx
from strings import Config


class SettingsDialog(wx.Dialog):
    def __init__(self, settings, parent):
        wx.Dialog.__init__(self, parent, title="Settings")
        self.settings = settings

        panel = wx.Panel(self)

        button_ok = wx.Button(panel, label="OK")
        button_ok.Bind(wx.EVT_BUTTON, self.on_ok)
        button_cancel = wx.Button(panel, label="Cancel")
        button_cancel.Bind(wx.EVT_BUTTON, lambda _: self.EndModal(wx.ID_CANCEL))

        self.screens_combobox = wx.Choice(panel)
        screen_names = ["%d: %s (%d,%d) %dx%d" % ((i, wx.Display(i).GetName()) + wx.Display(i).GetGeometry().Get())
                        for i in range(wx.Display.GetCount())]
        self.screens_combobox.SetItems(screen_names)
        self.screens_combobox.SetSelection(self.settings[Config.PROJECTOR_SCREEN])

        # --- Layout ---

        # Grid
        configs_grid = wx.GridSizer(rows=1, cols=2, hgap=5, vgap=5)

        configs_grid.Add(wx.StaticText(panel, label=Config.PROJECTOR_SCREEN), 0, wx.ALIGN_CENTER_VERTICAL)
        configs_grid.Add(self.screens_combobox)

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

    def get_settings(self):
        return self.settings

