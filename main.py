#!python
# -*- coding: utf-8 -*-

import os
import re
import time
import webbrowser

import wx
import wx.grid
import vlc

from projector import ProjectorWindow
from settings import SettingsDialog
from strings import Config

# TODO: Move this to settings or calculate
zad_path = u"H:\ownCloud\DATA\Yuki no Odori 2016\Fest\zad_numbered"
mp3_path = u"H:\ownCloud\DATA\Yuki no Odori 2016\Fest\mp3_numbered"
background_zad = None
filename_re = "^(?P<nom>\w{1,2})( \[(?P<start>[GW]{1})\])?\. (?P<name>.*?)(\(.(?P<num>\d{1,3})\))?$"


class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(700, 500))
        accelerator_table = []
        self.proj_win = None
        self.settings = {Config.PROJECTOR_SCREEN: wx.Display.GetCount() - 1}  # The last one
        self.items = None

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
        self.Bind(wx.EVT_MENU, self.ensure_proj_win,
                  proj_win_menu.Append(wx.ID_ANY, "&Create"))
        self.Bind(wx.EVT_MENU, self.destroy_proj_win,
                  proj_win_menu.Append(wx.ID_ANY, "&Destroy"))
        menu_bar.Append(proj_win_menu, "&Projector Window")

        # --- Play ---
        menu_play = wx.Menu()
        menu_no_show = menu_play.Append(wx.ID_ANY, "&No Show\tEsc")
        menu_show_zad = menu_play.Append(wx.ID_ANY, "Sho&w zad\tF1")
        menu_play_mp3 = menu_play.Append(wx.ID_ANY, "&Play\tF2")
        self.Bind(wx.EVT_MENU, self.no_show, menu_no_show)
        self.Bind(wx.EVT_MENU, self.show_zad, menu_show_zad)
        self.Bind(wx.EVT_MENU, self.play, menu_play_mp3)
        accelerator_table.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, menu_no_show.GetId()))
        accelerator_table.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F1, menu_show_zad.GetId()))
        accelerator_table.append(wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F2, menu_play_mp3.GetId()))

        menu_bar.Append(menu_play, "&Fire")

        self.SetMenuBar(menu_bar)

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.toolbar = wx.BoxSizer(wx.HORIZONTAL)

        self.toolbar.Add(wx.StaticText(self, label=' VOL '), 0, wx.ALIGN_CENTER_VERTICAL)
        self.vol_control = wx.SpinCtrl(self, value='-1', size=(50, 20))
        self.toolbar.Add(self.vol_control, 0)
        self.vol_control.SetRange(-1, 200)
        self.Bind(wx.EVT_SPINCTRL, self.set_vol, self.vol_control)

        self.fade_out_btn = wx.Button(self, label="Fade out", size=(100, 20))
        self.fade_out_btn.Enable(False)
        self.toolbar.Add(self.fade_out_btn, 0)
        self.fade_out_btn.Bind(wx.EVT_BUTTON, self.stop)

        self.vid_btn = wx.ToggleButton(self, label='VID', size=(35, 20))
        self.img_btn = wx.ToggleButton(self, label='IMG', size=(35, 20))
        self.vid_btn.Enable(False)
        self.img_btn.Enable(False)
        self.toolbar.Add(self.vid_btn, 0)
        self.toolbar.Add(self.img_btn, 0)

        # --- Table ---
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(1, 1)
        self.grid.HideRowLabels()
        self.grid.DisableDragRowSize()
        self.grid.SetColLabelSize(20)
        self.grid.SetCellValue(0, 0, "Hello World")
        self.grid.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)

        def select_row(e):
            self.Unbind(wx.grid.EVT_GRID_RANGE_SELECT)
            self.grid.SelectRow(e.Row if hasattr(e, 'Row') else e.TopRow)
            self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, select_row)
        self.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)

        main_sizer.Add(self.toolbar, 0, wx.EXPAND)
        main_sizer.Add(self.grid, 1, wx.EXPAND)

        # TODO: Progress bar
        # TODO: Search

        self.SetSizer(main_sizer)

        # ------------------ Status Bar ------------------
        self.status_bar = self.CreateStatusBar(3)

        self.status("Ready")

        self.SetAcceleratorTable(wx.AcceleratorTable(accelerator_table))
        self.Show(True)

        # ----------------------- VLC ---------------------

        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.player.audio_set_volume(100)
        self.player.audio_set_mute(False)
        self.vol_control.SetValue(self.player.audio_get_volume())

        self.load_data()

# ---------------------------------------------------------------------------------------------------------------------

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

    def status(self, text):
        self.status_bar.SetStatusText(text, 0)

    def image_status(self, text):
        self.status_bar.SetStatusText(text, 1)

    def sound_status(self, text):
        self.status_bar.SetStatusText(text, 2)

    def on_exit(self, e):
        self.destroy_proj_win()
        self.Close(True)

    def on_settings(self, e):
        settings_dialog = SettingsDialog(self.settings, self)
        res = settings_dialog.ShowModal()
        if res == wx.ID_OK:
            self.settings = settings_dialog.get_settings()
        settings_dialog.Destroy()

    def switch_to_vid(self, e=None):
        self.vid_btn.SetValue(True)
        self.img_btn.SetValue(False)
        self.proj_win.switch_to_video()

    def switch_to_img(self, e=None):
        self.vid_btn.SetValue(False)
        self.img_btn.SetValue(True)
        self.proj_win.switch_to_images()

    # ----------------------------------------------------

    def ensure_proj_win(self, e=None):
        if not isinstance(self.proj_win, ProjectorWindow):
            self.proj_win = ProjectorWindow(self, self.settings[Config.PROJECTOR_SCREEN])

            self.vid_btn.Bind(wx.EVT_TOGGLEBUTTON, self.switch_to_vid)
            self.img_btn.Bind(wx.EVT_TOGGLEBUTTON, self.switch_to_img)
            self.vid_btn.Enable(True)
            self.img_btn.Enable(True)
            self.img_btn.SetValue(True)

        self.proj_win.Show()
        self.Raise()

    def destroy_proj_win(self, e=None):
        if isinstance(self.proj_win, ProjectorWindow):
            self.proj_win.Close(True)
            self.vid_btn.Enable(False)
            self.img_btn.Enable(False)

    def load_data(self, e=None):
        zad_file_names = os.listdir(zad_path)
        mp3_file_names = os.listdir(mp3_path)

        self.items = {a.split(' ', 1)[0]: {os.path.join(zad_path, a)} for a in zad_file_names}
        for file_name in mp3_file_names:
            id = file_name.split(' ', 1)[0]
            path = os.path.join(mp3_path, file_name)
            if id in self.items:
                self.items[id].add(path)
            else:
                self.items[id] = {path}

        # if len(items_all) != len(mp3_file_names):
        #     msg = "ZAD files: %d\nmp3 files: %d" % (len(zad_file_names), len(mp3_file_names))
        #     d = wx.MessageDialog(self, msg, "Files integrity error", wx.OK | wx.ICON_WARNING)
        #     d.ShowModal()
        #     d.Destroy()

        self.grid_set_shape(len(self.items), 7)
        self.grid.SetColLabelValue(0, 'ID')
        self.grid.SetColLabelValue(1, 'nom')
        self.grid.SetColLabelValue(2, 'start')
        self.grid.SetColLabelValue(3, 'name')
        self.grid.SetColLabelValue(4, 'files')
        self.grid.SetColLabelValue(5, 'num')
        self.grid.SetColLabelValue(6, 'notes')

        i = 0
        for id, files in sorted(self.items.items()):
            name = max([a.rsplit('\\', 1)[1].split(' ', 1)[1].rsplit('.', 1)[0] for a in files], key=len)
            exts = ", ".join(sorted([a.rsplit('.', 1)[1] for a in files]))
            match = re.search(filename_re, name)
            start = {'W': 'point', 'G': 'instant'}[match.group('start')] if match.group('start') else 'unknown'
            self.items[id] = {'name': name,
                              'files': files,
                              'start': start}
            self.grid.SetCellValue(i, 0, id)
            self.grid.SetCellValue(i, 1, match.group('nom'))
            self.grid.SetCellValue(i, 2, start)
            self.grid.SetCellValue(i, 3, match.group('name'))
            self.grid.SetCellValue(i, 4, exts)

            # TODO: Paint

            if match.group('num'):
                self.grid.SetCellValue(i, 5, match.group('num'))
            [self.grid.SetReadOnly(i, a) for a in range(6)]
            i += 1

        self.grid.AutoSizeColumns()
        self.status("Loaded %d items" % i)

    def show_zad(self, e):
        self.ensure_proj_win()
        self.proj_win.switch_to_images()
        id = self.grid.GetCellValue(self.grid.GetGridCursorRow(), 0)
        try:
            file_path = filter(lambda a: a.rsplit('.', 1)[1] in {'jpg', 'png'}, self.items[id]['files'])[0]
            self.proj_win.load_zad(file_path, True)
            self.image_status("Showing: %s" % self.items[id]['name'])
            self.status("ZAD Fired!")
        except IndexError:
            self.clear_zad("No zad for '%s'" % self.items[id]['name'])

    def no_show(self, e=None):
        if isinstance(self.proj_win, ProjectorWindow):
            self.clear_zad("No show")
        self.stop(fade_out=False)

    def clear_zad(self, main_status="ZAD Cleared!"):
        if background_zad:
            self.proj_win.load_zad(background_zad, True)
            self.image_status("Background")
        else:
            self.proj_win.no_show()
            self.image_status("No show")
        self.status(main_status)

    def play(self, e=None):
        id = self.grid.GetCellValue(self.grid.GetGridCursorRow(), 0)
        try:
            file_path = filter(lambda a: a.rsplit('.', 1)[1] in {'mp3', 'wav', 'mp4', 'avi'},
                               self.items[id]['files'])[0]
            # TODO: What if video and audio?

            media = self.vlc_instance.media_new(file_path)
            self.player.set_media(media)

            if self.player.play() != -1:
                # Playing ...
                self.fade_out_btn.Enable(True)

                if file_path.rsplit('.', 1)[1] not in {'mp3', 'wav'}:
                    self.ensure_proj_win()
                    self.switch_to_vid()
                    # TODO: Switch back after video ends

                while self.player.audio_get_volume() != self.vol_control.GetValue():
                    self.player.audio_set_mute(False)
                    self.player.audio_set_volume(self.vol_control.GetValue())
                    self.sound_status("Trying to unmute...")
                    print "Trying to set unmute..."
                    time.sleep(0.05)
                self.sound_status("Playing...")
            else:
                self.sound_status("ERROR PLAYING FILE!!!")

        except IndexError:
            self.sound_status("Nothing to play for '%s'" % self.items[id]['name'])

    def stop(self, e=None, fade_out=True):
        self.fade_out_btn.Enable(False)
        self.sound_status("Fading out...")
        label = self.fade_out_btn.GetLabel()
        if fade_out:
            for i in range(self.player.audio_get_volume(), 0, -1):
                self.set_vol(vol=i, status='Fading out... ')
                time.sleep(0.01)
        self.player.stop()
        self.sound_status("Stopped")
        self.fade_out_btn.SetLabel(label)

    def set_vol(self, e=None, vol=100, status=''):
        value = e.Int if e else vol
        if self.player.audio_set_volume(value) == -1:
            self.sound_status("Failed to set volume")
        real_vol = self.player.audio_get_volume()
        if real_vol < 0:
            self.player.audio_set_mute(False)
        self.sound_status(status + "Vol: %d" % real_vol)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame(None, 'Fest Engine')
    app.MainLoop()
