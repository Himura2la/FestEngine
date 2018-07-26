import shutil
import time

import os
import wx

from constants import FileTypes


class FileReplacer(wx.Dialog):
    def __init__(self, parent, num):
        wx.Dialog.__init__(self, parent, title=_(u"Replace File for №%s") % num)
        self.main_window = parent
        top_sizer = wx.BoxSizer(wx.VERTICAL)

        files = [path for ext, path in self.main_window.data[num]['files'].items()]

        self.src_file_chooser = wx.RadioBox(self, label=_("Select which file to replace"),
                                            choices=files, majorDimension=1, style=wx.RA_SPECIFY_COLS)
        self.Bind(wx.EVT_RADIOBOX, self.src_file_selected, self.src_file_chooser)
        top_sizer.Add(self.src_file_chooser, 1, wx.ALL | wx.EXPAND, 5)

        file_picker_box = wx.StaticBox(self, label=_("Select target file"))
        file_picker_box_sizer = wx.StaticBoxSizer(file_picker_box, wx.VERTICAL)
        self.file_picker = wx.FilePickerCtrl(self)
        file_picker_box_sizer.Add(self.file_picker, 0, wx.EXPAND)
        top_sizer.Add(file_picker_box_sizer, 0, wx.ALL | wx.EXPAND, 5)
        self.Bind(wx.EVT_FILEPICKER_CHANGED, self.file_chosen, self.file_picker)

        top_sizer.Add(wx.StaticLine(self), 0, wx.ALL | wx.EXPAND, 5)
        buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ok_button = wx.Button(self, wx.ID_OK, "OK")
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_ok)
        buttons_sizer.Add(self.ok_button, 1)
        buttons_sizer.Add(wx.Button(self, wx.ID_CANCEL, _("Cancel")), 1)
        top_sizer.Add(buttons_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizerAndFit(top_sizer)

        self.src_file = None
        self.bkp_path = None
        self.src_file_selected()

    @property
    def tgt_file(self):
        return self.file_picker.GetPath()

    @tgt_file.setter
    def tgt_file(self, val):
        self.file_picker.SetPath(val)

    def src_file_selected(self, e=None):
        self.src_file = self.src_file_chooser.GetString(self.src_file_chooser.GetSelection())
        self.ok_button.Enable(False)
        self.tgt_file = self.src_file

    def file_chosen(self, e):
        tgt_file = self.file_picker.GetPath()
        tgt_ext = tgt_file.rsplit('.', 1)[1].lower()
        src_ext = self.src_file.rsplit('.', 1)[1].lower()
        known_exts = [val for name, val in vars(FileTypes).items()
                      if name[:2] + name[-2:] != '____' and isinstance(val, set)]
        if not any({src_ext in ext_set and tgt_ext in ext_set for ext_set in known_exts}):
            wx.MessageBox(_("Do not replace .%s to .%s!") % (src_ext, tgt_ext),
                          _("Different file types"), wx.OK | wx.ICON_ERROR, self)
            self.tgt_file = self.src_file
            return
        self.ok_button.Enable(True)

    def on_ok(self, e):
        path, src_name = os.path.split(self.src_file)
        path, src_dir = os.path.split(path)
        bkp_dir = os.path.join(path, src_dir + '_backup')
        if not os.path.exists(bkp_dir):
            os.mkdir(bkp_dir)
        self.bkp_path = os.path.join(bkp_dir, time.strftime("%d%m%y%H%M%S-", time.localtime()) + src_name)
        shutil.move(self.src_file, self.bkp_path)
        shutil.copy(self.tgt_file, self.src_file)  # TODO: Async and progress bar
        self.EndModal(wx.ID_OK)
