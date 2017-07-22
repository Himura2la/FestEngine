#!python
# -*- coding: utf-8 -*-

import os
import re
import time
import webbrowser
import bisect

import wx
import wx.grid
import vlc

from projector import ProjectorWindow
from settings import SettingsDialog
from constants import Config, Colors, Columns

# TODO: Move this to settings
zad_path = u"H:\ownCloud\DATA\Yuki no Odori 2016\Fest\zad_numbered"
mp3_path = u"H:\ownCloud\DATA\Yuki no Odori 2016\Fest\mp3_numbered"
background_zad_path = None
filename_re = "^(?P<nom>\w{1,2})( \[(?P<start>[GW]{1})\])?\. (?P<name>.*?)(\(.(?P<num>\d{1,3})\))?$"


class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(700, 500))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        accelerator_table = []
        self.proj_win = None
        self.settings = {Config.PROJECTOR_SCREEN: wx.Display.GetCount() - 1}  # The last one
        self.items = None
        self.grid_rows = None
        self.in_search = False
        self.grid_default_bg_color = None
        self.full_grid_data = None

        # ------------------ Menu ------------------
        menu_bar = wx.MenuBar()

        # --- File ---
        menu_file = wx.Menu()
        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(os.path.abspath(mp3_path)),
                  menu_file.Append(wx.ID_ANY, "Open &mp3 folder"))
        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(os.path.abspath(zad_path)),
                  menu_file.Append(wx.ID_ANY, "Open &zad folder"))

        menu_file.AppendSeparator()

        def on_settings(e):
            settings_dialog = SettingsDialog(self.settings, self)
            res = settings_dialog.ShowModal()
            if res == wx.ID_OK:
                self.settings = settings_dialog.get_settings()
            settings_dialog.Destroy()

        self.Bind(wx.EVT_MENU, on_settings,
                  menu_file.Append(wx.ID_ANY, "&Setings"))

        menu_file.AppendSeparator()

        self.Bind(wx.EVT_MENU, lambda _: webbrowser.open('https://github.com/Himura2la/FestEngine'),
                  menu_file.Append(wx.ID_ABOUT, "&About"))
        self.Bind(wx.EVT_MENU, self.on_exit,
                  menu_file.Append(wx.ID_EXIT, "E&xit"))
        menu_bar.Append(menu_file, "Fil&e")

        # --- Data ---
        menu_data = wx.Menu()
        self.load_data_item = menu_data.Append(wx.ID_ANY, "&Load Data")
        self.Bind(wx.EVT_MENU, self.load_data, self.load_data_item)

        menu_data.AppendSeparator()

        self.del_dup_row = menu_data.Append(wx.ID_ANY, "&Delete row duplicate")
        self.del_dup_row.Enable(False)
        self.Bind(wx.EVT_MENU, self.del_active_row, self.del_dup_row)

        menu_bar.Append(menu_data, "&Data")

        # --- Projector Window ---
        proj_win_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, self.ensure_proj_win,
                  proj_win_menu.Append(wx.ID_ANY, "&Create/Show"))
        self.destroy_proj_win_item = proj_win_menu.Append(wx.ID_ANY, "&Destroy")
        self.destroy_proj_win_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.destroy_proj_win, self.destroy_proj_win_item)
        menu_bar.Append(proj_win_menu, "&Projector Window")

        # --- Play ---
        menu_play = wx.Menu()
        menu_no_show = menu_play.Append(wx.ID_ANY, "&No Show\tEsc")
        menu_show_zad = menu_play.Append(wx.ID_ANY, "Show &zad\tF1")
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
        toolbar_base_height = 20

        # self.status_color_box = wx.Panel(self, size=(toolbar_base_height, toolbar_base_height))
        # self.toolbar.Add(self.status_color_box, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=1)
        # self.status_color_box.SetBackgroundColour((0, 255, 0))
        # TODO: #9

        self.toolbar.Add(wx.StaticText(self, label=' VOL '), 0, wx.ALIGN_CENTER_VERTICAL)
        self.vol_control = wx.SpinCtrl(self, value='-1', size=(50, toolbar_base_height))
        self.toolbar.Add(self.vol_control, 0, wx.ALIGN_CENTER_VERTICAL)
        self.vol_control.SetRange(-1, 200)
        self.vol_control.Bind(wx.EVT_SPINCTRL, self.set_vol, self.vol_control)

        self.fade_out_btn = wx.Button(self, label="Fade out", size=(70, toolbar_base_height + 2))
        self.fade_out_btn.Enable(False)
        self.toolbar.Add(self.fade_out_btn, 0)
        self.fade_out_btn.Bind(wx.EVT_BUTTON, self.stop)

        self.play_bar = wx.Gauge(self, range=1, size=(-1, toolbar_base_height))
        self.toolbar.Add(self.play_bar, 1, wx.ALIGN_CENTER_VERTICAL)
        self.play_time = wx.StaticText(self, label='Stopped', size=(50, -1), style=wx.ALIGN_CENTER)
        self.toolbar.Add(self.play_time, 0, wx.ALIGN_CENTER_VERTICAL)

        self.timer = wx.Timer(self)  # Events make the app unstable. Plus we can update not too often
        self.timer.Bind(wx.EVT_TIMER, self.on_timer, self.timer)

        self.search_box = wx.TextCtrl(self, size=(35, toolbar_base_height), value='Find')
        self.search_box.SetForegroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_GRAYTEXT))
        self.toolbar.Add(self.search_box, 0, wx.ALIGN_CENTER_VERTICAL)

        def quit_search(e=None):
            self.search_box.SetValue('Find')
            self.search_box.SetForegroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_GRAYTEXT))
            self.quit_search()
            self.SetFocus()

        def search_box_focus_handler(e):
            if self.search_box.GetValue() == 'Find':
                self.search_box.Clear()
                self.search_box.SetForegroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOWTEXT))
                self.enter_search()
            e.Skip()

        def search_box_leave_handler(e):
            if self.search_box.GetValue() == '':
                quit_search()
            e.Skip()

        self.search_box.Bind(wx.EVT_SET_FOCUS, search_box_focus_handler)
        self.search_box.Bind(wx.EVT_KILL_FOCUS, search_box_leave_handler)
        self.search_box.Bind(wx.EVT_TEXT, self.search)
        self.search_box.Bind(wx.EVT_RIGHT_DOWN, quit_search)
        self.search_box.SetToolTipString('Right-click to quit search')

        self.vid_btn = wx.ToggleButton(self, label='VID', size=(35, toolbar_base_height + 2))
        self.zad_btn = wx.ToggleButton(self, label='ZAD', size=(35, toolbar_base_height + 2))
        self.vid_btn.Enable(False)
        self.zad_btn.Enable(False)
        self.toolbar.Add(self.vid_btn, 0)
        self.toolbar.Add(self.zad_btn, 0)

        # --- Table ---
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(1, 1)
        self.grid.HideRowLabels()
        self.grid.DisableDragRowSize()
        self.grid.SetColLabelSize(20)
        self.grid.SetCellValue(0, 0, "Hello World")
        self.grid.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)

        def select_row(e):
            row = e.Row if hasattr(e, 'Row') else e.TopRow
            self.grid.Unbind(wx.grid.EVT_GRID_RANGE_SELECT)
            self.grid.SelectRow(row)
            self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)
            self.del_dup_row.Enable(self.is_dup_row(row))

        self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, select_row)
        self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_cell_changed)

        main_sizer.Add(self.toolbar, 0, wx.EXPAND)
        main_sizer.Add(self.grid, 1, wx.EXPAND | wx.TOP, border=1)

        self.SetSizer(main_sizer)

        # ------------------ Status Bar ------------------
        self.status_bar = self.CreateStatusBar(3)
        self.status("Ready")
        self.SetAcceleratorTable(wx.AcceleratorTable(accelerator_table))

        # ----------------------- VLC ---------------------

        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.player.audio_set_volume(100)
        self.player.audio_set_mute(False)
        self.vol_control.SetValue(self.player.audio_get_volume())
        self.player_status("VLC v.%s: %s" % (vlc.libvlc_get_version(), self.get_player_state(return_str=True)))

        self.Show(True)
        self.grid.SetFocus()

        self.load_data()

    # ------------------------------------------------------------------------------------------------------------------

    def grid_set_shape(self, new_rows, new_cols, readonly_cols=None):
        current_rows, current_cols = self.grid.GetNumberRows(), self.grid.GetNumberCols()
        self.grid.DeleteRows(0, current_rows, False)
        self.grid.AppendRows(new_rows)
        if new_cols < current_cols:
            self.grid.DeleteCols(0, current_cols - new_cols, False)
        elif new_cols > current_cols:
            self.grid.AppendCols(new_cols - current_cols)
        if readonly_cols:
            [self.grid.SetReadOnly(row, col)
             for row in range(new_rows)
             for col in range(new_cols) if col in readonly_cols]

    def status(self, text):
        self.status_bar.SetStatusText(text, 0)

    def image_status(self, text):
        self.status_bar.SetStatusText(text, 1)

    def player_status(self, text):
        self.status_bar.SetStatusText(text, 2)

    def on_exit(self, e):
        self.destroy_proj_win()
        self.Close(True)

    # -------------------------------------------------- Actions --------------------------------------------------

    def proj_win_exists(self):
        return isinstance(self.proj_win, ProjectorWindow)

    def ensure_proj_win(self, e=None):
        if not self.proj_win_exists():
            self.proj_win = ProjectorWindow(self, self.settings[Config.PROJECTOR_SCREEN])

            self.vid_btn.Bind(wx.EVT_TOGGLEBUTTON, self.switch_to_vid)
            self.zad_btn.Bind(wx.EVT_TOGGLEBUTTON, self.switch_to_zad)
            self.vid_btn.Enable(True)
            self.zad_btn.Enable(True)
            self.switch_to_zad()
        self.proj_win.Show()
        self.Raise()
        self.destroy_proj_win_item.Enable(True)

    def destroy_proj_win(self, e=None):
        if not self.proj_win_exists():
            return
        self.proj_win.Close(True)
        self.vid_btn.SetValue(False)
        self.vid_btn.Enable(False)
        self.zad_btn.SetValue(False)
        self.zad_btn.Enable(False)
        self.destroy_proj_win_item.Enable(False)

    def switch_to_vid(self, e=None):
        if not self.proj_win_exists():
            return
        self.vid_btn.SetValue(True)
        self.zad_btn.SetValue(False)
        self.proj_win.switch_to_video()

    def switch_to_zad(self, e=None):
        if not self.proj_win_exists():
            return
        self.vid_btn.SetValue(False)
        self.zad_btn.SetValue(True)
        self.proj_win.switch_to_images()

    def show_zad(self, e):
        self.ensure_proj_win()
        self.proj_win.switch_to_images()
        id = self.get_id(self.grid.GetGridCursorRow())
        try:
            file_path = filter(lambda a: a.rsplit('.', 1)[1] in {'jpg', 'png'}, self.items[id]['files'])[0]
            self.proj_win.load_zad(file_path, True)
            self.image_status("Showing ID %s" % id)
            self.status("ZAD Fired!")
        except IndexError:
            self.status("No zad for ID %s" % id)
            self.clear_zad()

    def clear_zad(self):
        if background_zad_path:
            self.proj_win.load_zad(background_zad_path, True)
            self.image_status("Background")
        else:
            self.proj_win.no_show()
            self.image_status("No show")

    def no_show(self, e=None):
        if self.proj_win_exists():
            self.clear_zad()
        self.stop(fade_out=False)
        self.status("FULL STOP!")

    # -------------------------------------------------- Data --------------------------------------------------

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

        self.grid_rows = [Columns.ID, Columns.NOM, Columns.START, Columns.NAME,
                          Columns.FILES, Columns.NUM, Columns.NOTES]

        self.grid_set_shape(len(self.items), len(self.grid_rows))
        for i in range(len(self.grid_rows)):
            self.grid.SetColLabelValue(i, self.grid_rows[i])

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

            if match.group('num'):
                self.grid.SetCellValue(i, 5, match.group('num'))
            [self.grid.SetReadOnly(i, a) for a in range(6)]
            i += 1

        self.grid.AutoSizeColumns()
        self.status("Loaded %d items" % i)
        self.load_data_item.Enable(False)

    def on_grid_cell_changed(self, e):
        self.grid.Unbind(wx.grid.EVT_GRID_CELL_CHANGED)

        if not self.grid.GetColLabelValue(e.Col) == Columns.NOTES:
            return
        note = self.grid.GetCellValue(e.Row, e.Col)
        match = re.search('>(\d{3}(\w)?)([^\w].*)?', note)  # ">234" or ">305a" or ">152a maybe"
        if not match:
            return
        new_id, _, note = match.groups()

        row = {self.grid.GetColLabelValue(i): {'col': i, 'val': self.grid.GetCellValue(e.Row, i)}
               for i in range(self.grid.GetNumberCols())}

        old_id = row[Columns.ID]['val']
        row[Columns.ID]['val'] = new_id
        row[Columns.NOTES]['val'] = '<%s %s' % (old_id, note) if note else '<%s' % old_id

        ids = [self.grid.GetCellValue(i, row[Columns.ID]['col']) for i in range(self.grid.GetNumberRows())]

        if new_id not in ids or not self.is_dup_row(ids.index(new_id)):
            i = ord('a')
            while row[Columns.ID]['val'] in ids:  # If ID already exists, append a letter
                row[Columns.ID]['val'] = new_id + chr(i)
                i += 1
            new_row = bisect.bisect(ids, row[Columns.ID]['val'])  # determining row insertion point
            self.grid.InsertRows(new_row, 1)
        else:
            new_row = ids.index(new_id)

        for cell in row.values():
            self.grid.SetCellValue(new_row, cell['col'], cell['val'])
            self.grid.SetCellBackgroundColour(new_row, cell['col'], Colors.DUP_ROW)
            self.grid.SetReadOnly(new_row, cell['col'])

        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_cell_changed)

    def is_dup_row(self, row):
        return self.grid.GetCellBackgroundColour(row, 0) == Colors.DUP_ROW

    def get_id(self, row):
        if self.is_dup_row(row):
            return self.grid.GetCellValue(row, self.grid_rows.index(Columns.NOTES))[1:4]
        else:
            return self.grid.GetCellValue(row, self.grid_rows.index(Columns.ID))

    def del_active_row(self, e=None):
        row = self.grid.GetSelectedRows()[0]
        if self.is_dup_row(row):  # Extra check, this method is very dangerous.
            self.grid.DeleteRows(row)

    def grid_push(self):
        self.grid_default_bg_color = self.grid.GetDefaultCellBackgroundColour()
        self.full_grid_data = [{'cols': [self.grid.GetCellValue(row, col) for col in range(self.grid.GetNumberCols())],
                                'color':self.grid.GetCellBackgroundColour(row, 0)}
                               for row in range(self.grid.GetNumberRows())]

    def grid_set(self, grid_state, default_bg=None, readonly=False):
        if not default_bg:
            default_bg = self.grid.GetDefaultCellBackgroundColour()
        rows, cols = len(grid_state), len(grid_state[0]['cols'])
        readonly_cols = [col for col in range(cols) if self.grid.GetColLabelValue(col) != Columns.NOTES or readonly]

        self.grid_set_shape(rows, cols, readonly_cols)
        for row in range(rows):
            for col in range(cols):
                if grid_state[row]['color'] != default_bg:
                    self.grid.SetCellBackgroundColour(row, col, grid_state[row]['color'])
                self.grid.SetCellValue(row, col, grid_state[row]['cols'][col])

    def grid_pop(self):
        self.grid.SetDefaultCellBackgroundColour(self.grid_default_bg_color)
        self.grid_set(self.full_grid_data)

    def enter_search(self):
        self.in_search = True
        self.grid_push()
        self.grid.SetDefaultCellBackgroundColour(Colors.FILTERED_GRID)
        self.grid.ForceRefresh()

    def paint_search_box(self, val):
        if val:
            self.search_box.SetBackgroundColour((255, 200, 200))
        else:
            self.search_box.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.search_box.Refresh()

    def search(self, e=None):
        string = self.search_box.GetValue()
        if string == 'Find' or not self.in_search or not string:
            return

        def match(row):
            """Returns True if any cell in a row matches"""
            return reduce(lambda a, b: a or b, [self.search_box.GetValue().lower() in cell.lower()
                                                for cell in row['cols']])

        filtered_grid_data = filter(match, self.full_grid_data)
        if filtered_grid_data:
            self.grid_set(filtered_grid_data, self.grid_default_bg_color, True)
        self.paint_search_box(not bool(filtered_grid_data))

    def quit_search(self):
        if self.in_search:
            self.in_search = False
            self.paint_search_box(False)
            self.grid_pop()
            self.grid.ForceRefresh()

    # -------------------------------------------------- Player --------------------------------------------------

    def play(self, e=None):
        id = self.get_id(self.grid.GetGridCursorRow())
        try:
            file_path = filter(lambda a: a.rsplit('.', 1)[1] in {'mp3', 'wav', 'mp4', 'avi'},
                               self.items[id]['files'])[0]

            media = self.vlc_instance.media_new(file_path)
            self.player.set_media(media)

            if self.player.play() != -1:
                self.get_player_state(True)
                self.timer.Start(500)
                self.fade_out_btn.Enable(True)

                self.status("SOUND Fired!")

                if file_path.rsplit('.', 1)[1] not in {'mp3', 'wav'}:
                    self.ensure_proj_win()
                    self.switch_to_vid()

                while self.player.audio_get_volume() != self.vol_control.GetValue():
                    self.player.audio_set_mute(False)
                    self.player.audio_set_volume(self.vol_control.GetValue())
                    self.player_status("Trying to unmute...")
                    time.sleep(0.05)

            else:
                self.player_status("ERROR PLAYING FILE!!!")

        except IndexError:
            self.player_status("Nothing to play for '%s'" % self.items[id]['name'])

    def stop(self, e=None, fade_out=True):
        self.fade_out_btn.Enable(False)
        self.timer.Stop()
        if fade_out:
            label = self.fade_out_btn.GetLabel()
            for i in range(self.player.audio_get_volume(), 0, -1):
                self.set_vol(vol=i)
                vol_msg = 'Vol: %d' % self.player.audio_get_volume()
                self.fade_out_btn.SetLabel(vol_msg)
                self.player_status('Fading out... ' + vol_msg)
                time.sleep(0.01)
            self.fade_out_btn.SetLabel(label)
        self.player.stop()
        self.play_bar.SetValue(0)
        self.get_player_state(True)
        self.play_time.SetLabel('Stopped')

    def set_vol(self, e=None, vol=100):
        value = e.Int if e else vol
        if self.player.audio_set_volume(value) == -1:
            self.player_status("Failed to set volume")
        real_vol = self.player.audio_get_volume()
        if real_vol < 0:
            self.player.audio_set_mute(False)

    def get_player_state(self, set_status_bar=False, return_str=False):
        state_int = self.player.get_state()
        state_str = {0: 'Ready',
                     1: 'Opening',
                     2: 'Buffering',
                     3: 'Playing...',
                     4: 'Paused',
                     5: 'Stopped',
                     6: 'Ended',
                     7: 'Error'}[state_int]
        if set_status_bar:
            self.player_status(state_str)
        return state_str if return_str else state_int

    def on_timer(self, e):
        length, time = self.player.get_length(), self.player.get_time()
        self.play_bar.SetRange(length - 1000)  # FIXME: Don't know why it does not reach the end
        self.play_bar.SetValue(time)

        self.play_time.SetLabel('-%02d:%02d' % divmod(length / 1000 - time / 1000, 60))

        state = self.get_player_state(True)
        if state not in range(5):
            self.timer.Stop()
            self.play_bar.SetValue(0)
            self.switch_to_zad()


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame(None, 'Fest Engine')
    app.MainLoop()
