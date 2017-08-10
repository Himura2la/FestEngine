#!python2
# -*- coding: utf-8 -*-

import argparse
import bisect
import os
import re
import sys
import threading
import time
import webbrowser

import vlc
import wx
import wx.grid

from background_music_player import BackgroundMusicPlayer
from constants import Config, Colors, Columns, FileTypes
from projector import ProjectorWindow
from settings import SettingsDialog

parser = argparse.ArgumentParser()
parser.add_argument("--filename_re", dest="filename_re", help='Regular expression that parses your '
                                                              'filenames (without ID and extension)')
parser.add_argument("--zad_dir", dest="zad_dir", help='Path to a directory with images that will '
                                                      'be shown on a second screen on F1 (ZAD)')
parser.add_argument("--mp3_dir", dest="mp3_dir", help='Path to a directory with tracks that will '
                                                      'be fired on F2 (music or video)')
parser.add_argument("--background_zad_path", dest="background_zad_path", help='Path to a base image that will be shown '
                                                                              'when nothing else is showing (optional)')
parser.add_argument("--background_mp3_dir", dest="background_mp3_dir", help='Path to a directory with '
                                                                            'background tracks, that will sound on F3')

parser.add_argument("--debug_output", dest="debug_output", action='store_true')
parser.add_argument("--auto_load_files", dest="auto_load_files", action='store_true')
parser.add_argument("--auto_load_bg", dest="auto_load_bg", action='store_true')

args = parser.parse_args()


def fix_encoding(path):
    return path.decode(sys.getfilesystemencoding()) if path and isinstance(path, str) else path

filename_re = fix_encoding(args.filename_re)
zad_dir = fix_encoding(args.zad_dir)
mp3_dir = fix_encoding(args.mp3_dir)
background_zad_path = fix_encoding(args.background_zad_path)
background_mp3_dir = fix_encoding(args.background_mp3_dir)
debug_output = fix_encoding(args.debug_output)
auto_load_files = fix_encoding(args.auto_load_files)
auto_load_bg = fix_encoding(args.auto_load_bg)


class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(700, 500))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        self.player_time_update_interval_ms = 300
        self.fade_out_delays_ms = 10
        self.settings = {Config.PROJECTOR_SCREEN: wx.Display.GetCount() - 1}  # The last one

        self.proj_win = None
        self.items = None
        self.grid_rows = None
        self.in_search = False
        self.grid_default_bg_color = None
        self.full_grid_data = None

        self.player_time_update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.player_time_update, self.player_time_update_timer)

        self.bg_player = BackgroundMusicPlayer(self)
        self.bg_player_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_background_timer, self.bg_player_timer)

        # ------------------ Menu ------------------
        menu_bar = wx.MenuBar()

        # --- File ---
        menu_file = wx.Menu()

        self.load_data_item = menu_file.Append(wx.ID_ANY, "&Load ZAD and MP3")
        self.Bind(wx.EVT_MENU, self.load_files, self.load_data_item)

        menu_file.AppendSeparator()

        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(os.path.abspath(mp3_dir)),
                  menu_file.Append(wx.ID_ANY, "Open &MP3 Folder"))
        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(os.path.abspath(zad_dir)),
                  menu_file.Append(wx.ID_ANY, "Open &ZAD Folder"))
        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(os.path.abspath(background_mp3_dir)),
                  menu_file.Append(wx.ID_ANY, "Open &Background Music Folder"))

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
        menu_grid = wx.Menu()

        self.del_dup_row_item = menu_grid.Append(wx.ID_ANY, "&Delete duplicate")
        self.del_dup_row_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.del_dup_row, self.del_dup_row_item)

        menu_bar.Append(menu_grid, "&Item")

        # --- Projector Window ---
        proj_win_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, self.ensure_proj_win,
                  proj_win_menu.Append(wx.ID_ANY, "&Show"))
        self.destroy_proj_win_item = proj_win_menu.Append(wx.ID_ANY, "&Destroy")
        self.destroy_proj_win_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.destroy_proj_win, self.destroy_proj_win_item)
        menu_bar.Append(proj_win_menu, "&Projector Window")

        # --- Background Music ---
        menu_bg_music = wx.Menu()

        self.Bind(wx.EVT_MENU, self.on_bg_load_files,
                  menu_bg_music.Append(wx.ID_ANY, "&Load Files"))
        self.Bind(wx.EVT_MENU, lambda e: self.bg_player.show_window(),
                  menu_bg_music.Append(wx.ID_ANY, "&Open Window"))

        menu_bg_music.AppendSeparator()

        self.bg_fade_switch = menu_bg_music.Append(wx.ID_ANY, "&Fade In/Out Enabled", kind=wx.ITEM_CHECK)
        self.bg_fade_switch.Check(self.bg_player.fade_in_out)
        self.Bind(wx.EVT_MENU, self.fade_switched, self.bg_fade_switch)

        self.bg_play_item = menu_bg_music.Append(wx.ID_ANY, "&Play Next")
        self.Bind(wx.EVT_MENU, self.background_play, self.bg_play_item)
        self.bg_play_item.Enable(False)

        self.bg_pause_switch = menu_bg_music.Append(wx.ID_ANY, "&Pause", kind=wx.ITEM_CHECK)
        self.bg_pause_switch.Enable(False)
        self.Bind(wx.EVT_MENU, self.background_pause, self.bg_pause_switch)

        menu_bar.Append(menu_bg_music, "&Background Music")

        # --- Fire (Play) ---
        menu_play = wx.Menu()
        no_show_item = menu_play.Append(wx.ID_ANY, "&Emergency No Show\tEsc")
        show_zad_item = menu_play.Append(wx.ID_ANY, "Show &ZAD\tF1")
        play_mp3_item = menu_play.Append(wx.ID_ANY, "&Play Sound/Video\tF2")
        play_pause_bg_item = menu_play.Append(wx.ID_ANY, "&Play/Pause Background\tF3")

        self.Bind(wx.EVT_MENU, self.no_show, no_show_item)
        self.Bind(wx.EVT_MENU, self.show_zad, show_zad_item)
        self.Bind(wx.EVT_MENU, self.play_async, play_mp3_item)
        self.Bind(wx.EVT_MENU, self.play_pause_bg, play_pause_bg_item)

        self.SetAcceleratorTable(wx.AcceleratorTable([
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, no_show_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F1, show_zad_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F2, play_mp3_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F3, play_pause_bg_item.GetId())]))

        menu_bar.Append(menu_play, "&Fire")

        self.SetMenuBar(menu_bar)

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.toolbar = wx.BoxSizer(wx.HORIZONTAL)
        toolbar_base_height = 20
        if sys.platform.startswith('linux'):
            toolbar_base_height += 5

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
        self.fade_out_btn.Bind(wx.EVT_BUTTON, self.stop_async)

        self.time_bar = wx.Gauge(self, range=1, size=(-1, toolbar_base_height))
        self.toolbar.Add(self.time_bar, 1, wx.ALIGN_CENTER_VERTICAL)
        self.time_label = wx.StaticText(self, label='Stopped', size=(50, -1), style=wx.ALIGN_CENTER)
        self.toolbar.Add(self.time_label, 0, wx.ALIGN_CENTER_VERTICAL)

        self.search_box = wx.TextCtrl(self, size=(35, toolbar_base_height), value='Find')
        self.search_box.SetForegroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_GRAYTEXT))
        self.toolbar.Add(self.search_box, 0, wx.ALIGN_CENTER_VERTICAL)

        def search_box_leave_handler(e):
            if self.search_box.GetValue() == '':
                self.quit_search()
            e.Skip()

        self.search_box.Bind(wx.EVT_SET_FOCUS, self.enter_search)
        self.search_box.Bind(wx.EVT_KILL_FOCUS, search_box_leave_handler)
        self.search_box.Bind(wx.EVT_TEXT, self.search)
        self.search_box.Bind(wx.EVT_RIGHT_DOWN, self.quit_search)
        self.search_box.SetToolTipString('Right-click to quit search')

        self.vid_btn = wx.ToggleButton(self, label='VID', size=(35, toolbar_base_height + 2))
        self.zad_btn = wx.ToggleButton(self, label='ZAD', size=(35, toolbar_base_height + 2))
        self.vid_btn.Enable(False)
        self.zad_btn.Enable(False)
        self.toolbar.Add(self.vid_btn, 0)
        self.toolbar.Add(self.zad_btn, 0)

        # --- Table ---
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 0)
        self.grid.HideRowLabels()
        self.grid.DisableDragRowSize()
        self.grid.SetColLabelSize(20)
        self.grid.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)

        def select_row(e):
            row = e.Row if hasattr(e, 'Row') else e.TopRow
            self.grid.Unbind(wx.grid.EVT_GRID_RANGE_SELECT)
            self.grid.SelectRow(row)
            self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)
            self.del_dup_row_item.Enable(self.is_dup_row(row))

        self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, select_row)
        self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_cell_changed)

        main_sizer.Add(self.toolbar, 0, wx.EXPAND)
        main_sizer.Add(self.grid, 1, wx.EXPAND | wx.TOP, border=1)

        self.SetSizer(main_sizer)

        # ------------------ Status Bar ------------------
        self.status_bar = self.CreateStatusBar(4)
        self.status("Ready")

        # ----------------------- VLC ---------------------

        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.player.audio_set_volume(100)
        self.player.audio_set_mute(False)
        self.vol_control.SetValue(self.player.audio_get_volume())

        self.player_status = "VLC v.%s: %s" % \
                             (vlc.libvlc_get_version(), self.player_state_parse(self.player.get_state()))
        self.bg_player_status = "Background Player: %s" % self.player_state_parse(self.bg_player.player.get_state())

        self.Show(True)
        self.grid.SetFocus()

        if auto_load_files: 
            self.load_files()
        if auto_load_bg:
            self.on_bg_load_files()

    # ------------------------------------------------------------------------------------------------------------------

    def grid_set_shape(self, new_rows, new_cols, readonly_cols=None):
        current_rows, current_cols = self.grid.GetNumberRows(), self.grid.GetNumberCols()
        if current_rows > 0:
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

    @property
    def player_status(self):
        return self.status_bar.GetStatusText(2)

    @player_status.setter
    def player_status(self, text):
        self.status_bar.SetStatusText(text, 2)

    def set_player_status(self, text):  # For lambdas
        self.status_bar.SetStatusText(text, 2)

    @property
    def bg_player_status(self):
        return self.status_bar.GetStatusText(3)

    @bg_player_status.setter
    def bg_player_status(self, text):
        self.status_bar.SetStatusText(text, 3)

    def set_bg_player_status(self, text):  # For lambdas
        self.status_bar.SetStatusText(text, 3)

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
            self.image_status("Projector Window Created")
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
        self.image_status("Projector Window Destroyed")

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
        self.stop_async(fade_out=False)

        bg_fade_state = self.bg_player.fade_in_out
        self.bg_player.fade_in_out = False
        self.background_pause(paused=True)
        self.bg_player.fade_in_out = bg_fade_state

        self.status("EMERGENCY STOP !!!")

    # -------------------------------------------------- Data --------------------------------------------------

    def load_files(self, e=None):
        if not zad_dir or not mp3_dir or not os.path.isdir(zad_dir) or not os.path.isdir(mp3_dir) or not filename_re:
            msg = "No filename regular expression or ZAD path is invalid or MP3 path is invalid.\n" \
                  "Please specify valid paths in '--zad_dir' and '--mp3_dir' command line arguments,\n" \
                  "and regular expression that parses your filenames in '--filename_re' command line argument.\n\n" \
                  "ZAD Path: %s\n" \
                  "MP3 Path: %s\n" \
                  "Filename regexp: %s" % (zad_dir, mp3_dir, filename_re)
            d = wx.MessageDialog(self, msg, "Path Error", wx.OK | wx.ICON_ERROR)
            d.ShowModal()
            d.Destroy()
            return

        zad_file_names = os.listdir(zad_dir)
        mp3_file_names = os.listdir(mp3_dir)

        self.items = {a.split(' ', 1)[0]: {os.path.join(zad_dir, a)} for a in zad_file_names}
        for file_name in mp3_file_names:
            id = file_name.split(' ', 1)[0]
            path = os.path.join(mp3_dir, file_name)
            if id in self.items:
                self.items[id].add(path)
            else:
                self.items[id] = {path}

        self.grid_rows = [Columns.ID, Columns.NOM, Columns.START, Columns.NAME,
                          Columns.FILES, Columns.NUM, Columns.NOTES]

        self.grid_set_shape(len(self.items), len(self.grid_rows))
        for i in range(len(self.grid_rows)):
            self.grid.SetColLabelValue(i, self.grid_rows[i])

        i = 0
        for id, files in sorted(self.items.items()):
            name = max([os.path.splitext(os.path.basename(a).split(' ', 1)[1])[0] for a in files], key=len)
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
        self.load_data_item.Enable(False)  # Safety is everything!

    # --- Duplication from notes ---

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

    def del_dup_row(self, e=None):
        row = self.grid.GetSelectedRows()[0]
        if self.is_dup_row(row):  # Extra check, this method is very dangerous.
            self.grid.DeleteRows(row)

    # --- Search ---

    def enter_search(self, e=None):
        if self.search_box.GetValue() == 'Find':
            self.search_box.Clear()
            self.search_box.SetForegroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOWTEXT))
            self.in_search = True
            self.grid_push()
            self.grid.SetDefaultCellBackgroundColour(Colors.FILTERED_GRID)
            self.grid.ForceRefresh()  # Updates colors
        if e:
            e.Skip()

    def grid_push(self):
        self.grid_default_bg_color = self.grid.GetDefaultCellBackgroundColour()
        self.full_grid_data = [{'cols': [self.grid.GetCellValue(row, col) for col in range(self.grid.GetNumberCols())],
                                'color':self.grid.GetCellBackgroundColour(row, 0)}
                               for row in range(self.grid.GetNumberRows())]

    def grid_pop(self):
        self.grid.SetDefaultCellBackgroundColour(self.grid_default_bg_color)
        self.grid_set_data(self.full_grid_data)
        self.grid.ForceRefresh()  # Updates colors

    def grid_set_data(self, dataset, default_bg_in_dataset=None, readonly=False):
        if not default_bg_in_dataset:
            default_bg_in_dataset = self.grid.GetDefaultCellBackgroundColour()
        rows, cols = len(dataset), len(dataset[0]['cols'])
        readonly_cols = [col for col in range(cols) if self.grid.GetColLabelValue(col) != Columns.NOTES or readonly]

        self.grid_set_shape(rows, cols, readonly_cols)
        for row in range(rows):
            for col in range(cols):
                if dataset[row]['color'] != default_bg_in_dataset:
                    self.grid.SetCellBackgroundColour(row, col, dataset[row]['color'])
                self.grid.SetCellValue(row, col, dataset[row]['cols'][col])

    def search(self, e=None):
        string = self.search_box.GetValue()
        if string == 'Find' or not self.in_search or not string:
            return

        def match(row):
            """Returns True if any cell in a row matches"""
            return reduce(lambda a, b: a or b, [self.search_box.GetValue().lower() in cell.lower()
                                                for cell in row['cols']])

        filtered_grid_data = filter(match, self.full_grid_data)
        found = bool(filtered_grid_data)
        if found:
            self.grid_set_data(filtered_grid_data, self.grid_default_bg_color, True)
        self.paint_search_box(not found)

    def paint_search_box(self, val):
        if val:
            self.search_box.SetBackgroundColour((255, 200, 200))
        else:
            self.search_box.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
        self.search_box.Refresh()

    def quit_search(self, e=None):
        if self.in_search:
            self.in_search = False
            self.paint_search_box(False)

            self.search_box.SetValue('Find')
            self.search_box.SetForegroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_GRAYTEXT))

            selected_row = [self.grid.GetCellValue(self.grid.GetSelectedRows()[0], col)
                            for col in range(self.grid.GetNumberCols())]
            selected_row_i = 0
            for i in range(len(self.full_grid_data)):
                if self.full_grid_data[i]['cols'] == selected_row:
                    selected_row_i = i
                    break
            self.grid_pop()

            self.grid.SelectRow(selected_row_i)
            self.grid.SetGridCursor(selected_row_i, 0)
            self.grid.MakeCellVisible(selected_row_i, 0)

            self.grid.SetFocus()
        # if e: e.Skip() # Invokes default handler with context menu

    # -------------------------------------------------- Player --------------------------------------------------

    def play_async(self, e=None):
        id = self.get_id(self.grid.GetGridCursorRow())
        try:
            file_path = filter(lambda a: a.rsplit('.', 1)[1] in FileTypes.sound_extensions | FileTypes.video_extensions,
                               self.items[id]['files'])[0]
        except IndexError:
            self.player_status = "Nothing to play for '%s'" % self.items[id]['name']
            return
        self.play_pause_bg(play=False)
        self.player.set_media(self.vlc_instance.media_new(file_path))

        if file_path.rsplit('.', 1)[1] in FileTypes.video_extensions:
            self.ensure_proj_win()
            self.switch_to_vid()

        threading.Thread(target=self.play_sync, args=(self.vol_control.GetValue(),)).start()

        self.player_time_update_timer.Start(self.player_time_update_interval_ms)

    def play_sync(self, target_vol):
        if self.player.play() != 0:              # [Play] button is pushed here!
            wx.CallAfter(lambda: self.set_player_status('Playback FAILED !!!'))
            return

        state = self.player.get_state()
        start = time.time()
        while state != vlc.State.Playing:
            state = self.player.get_state()
            status = "%s [%.3fs]" % (self.player_state_parse(state), (time.time() - start))
            wx.CallAfter(lambda: self.set_player_status(status))
            if debug_output:
                print status
            time.sleep(0.007)
        if debug_output:
            print "Started playback in %.0fms" % ((time.time() - start) * 1000)

        wx.CallAfter(lambda: self.fade_out_btn.Enable(True))

        start = time.time()
        status = '#'
        while self.player.audio_get_volume() != target_vol:
            self.player.audio_set_mute(False)
            self.player.audio_set_volume(target_vol)
            status = "Trying to unmute... [%.3fs]" % (time.time() - start)
            wx.CallAfter(lambda: self.set_player_status(status))
            if debug_output:
                print status
            time.sleep(0.001)
        if debug_output and status[0] == 'T':
            print "Unmuted in %.0fms" % ((time.time() - start) * 1000)

        def ui_upd():
            self.player_status = '%s Vol:%d' % (self.player_state_parse(self.player.get_state()),
                                                self.player.audio_get_volume())
            self.status('SOUND Fired!')
        wx.CallAfter(ui_upd)

    def stop_async(self, e=None, fade_out=True):
        self.fade_out_btn.Enable(False)
        if fade_out:
            threading.Thread(target=self.fade_out_stop_sync,
                             args=(self.fade_out_btn.GetLabel(),)).start()
        else:
            self.player.stop()
            self.time_bar.SetValue(0)
            self.player_status = self.player_state_parse(self.player.get_state())
            self.time_label.SetLabel('Stopped')

    def fade_out_stop_sync(self, fade_out_btn_label):
        for i in range(self.player.audio_get_volume(), 0, -1):
            self.set_vol(vol=i)
            vol_msg = 'Vol: %d' % self.player.audio_get_volume()

            def ui_upd():
                self.fade_out_btn.SetLabel(vol_msg)
                self.player_status = 'Fading out... ' + vol_msg
            wx.CallAfter(ui_upd)

            time.sleep(self.fade_out_delays_ms / float(1000))
        self.player.stop()

        def ui_upd():
            self.fade_out_btn.SetLabel(fade_out_btn_label)
            self.time_bar.SetValue(0)
            self.player_status = self.player_state_parse(self.player.get_state())
            self.time_label.SetLabel('Stopped')
        wx.CallAfter(ui_upd)

    def set_vol(self, e=None, vol=100):
        value = e.Int if e else vol
        if self.player.audio_set_volume(value) == -1:
            wx.CallAfter(lambda: self.set_player_status('Failed to set volume'))
        real_vol = self.player.audio_get_volume()
        if real_vol < 0:
            self.player.audio_set_mute(False)

    @staticmethod
    def player_state_parse(state_int):
        return {0: 'Ready',
                1: 'Opening',
                2: 'Buffering',
                3: 'Playing',
                4: 'Paused',
                5: 'Stopped',
                6: 'Ended',
                7: 'Error'}[state_int]

    def player_time_update(self, e=None):
        player_state = self.player.get_state()
        if player_state in range(4):  # Playing or going to play
            length, time = self.player.get_length(), self.player.get_time()
            self.time_bar.SetRange(length - 1000 if length else 0)  # FIXME: Don't know why it does not reach the end
            self.time_bar.SetValue(time)

            time_remaining = '-%02d:%02d' % divmod(length / 1000 - time / 1000, 60)
            self.time_label.SetLabel(time_remaining)

            status = '%s Vol:%d Time:%s' % (self.player_state_parse(player_state),
                                            self.player.audio_get_volume(), time_remaining)
            if 'Fading' not in self.player_status:
                self.player_status = status
        else:  # Not playing
            self.time_bar.SetValue(0)
            self.switch_to_zad()

            row = self.grid.GetSelectedRows()[0]
            if row < self.grid.GetNumberRows() - 1:
                self.grid.SetGridCursor(row + 1, 0)
                self.grid.SelectRow(row + 1)

            self.grid.SetFocus()
            self.player_time_update_timer.Stop()

    # -------------------------------------------- Background Music Player --------------------------------------------

    def on_bg_load_files(self, e=None):
        if not background_mp3_dir or not os.path.isdir(background_mp3_dir):
            msg = "Background MP3 path is invalid.\n" \
                  "Please specify valid path with your background tracks\n" \
                  "in '--background_mp3_dir' command line argument.\n\n" \
                  "Found path: %s" % background_mp3_dir
            d = wx.MessageDialog(self, msg, "Path Error", wx.OK | wx.ICON_ERROR)
            d.ShowModal()
            d.Destroy()
            return

        self.bg_player.load_files(background_mp3_dir)
        self.bg_play_item.Enable(True)

    def fade_switched(self, e):
        value = bool(e.Int)
        self.bg_player.fade_in_out = value
        if isinstance(e.EventObject, wx.CheckBox):
            self.bg_fade_switch.Check(value)
        elif isinstance(e.EventObject, wx.Menu) and self.bg_player.window_exists():
            self.bg_player.window.fade_in_out_switch.SetValue(value)

    def background_play(self, e=None, from_grid=True):
        if not self.bg_player.playlist:
            self.bg_player_status = "Forced playlist loading..."
            self.on_bg_load_files()

        if e and isinstance(e.EventObject, wx.Menu):  # From menu - always play next
            self.bg_player.switch_track_async(False)
        else:
            self.bg_player.switch_track_async(from_grid)

    def background_pause(self, e=None, paused=None):
        value = bool(e.Int) if e else paused
        self.bg_player.pause_async(value)
        if not e or isinstance(e.EventObject, wx.ToggleButton):
            self.bg_pause_switch.Check(value)
        if self.bg_player.window_exists():
            self.bg_player.window.pause_btn.SetValue(value)

    @property
    def background_volume(self):
        return self.bg_player.player.audio_get_volume()

    @background_volume.setter
    def background_volume(self, value):
        self.bg_player.volume = value
        self.bg_player.player.audio_set_volume(value)
        if self.bg_player.window_exists():
            self.bg_player.window.vol_slider.SetValue(value)

    def bg_player_timer_start(self, val):
        if val:
            self.bg_player_timer.Start(val)
        else:
            self.bg_player_timer.Stop()

    def on_background_timer(self, e=None, seeking_time=None):
        length = self.bg_player.player.get_length()
        pos = seeking_time if seeking_time else self.bg_player.player.get_time()
        time_remaining = '-%02d:%02d' % divmod(length / 1000 - pos / 1000, 60)

        if self.bg_player.window_exists():
            self.bg_player.window.time_slider.SetRange(0, length)
            self.bg_player.window.time_slider.SetValue(pos)
            self.bg_player.window.time_label.SetLabel(time_remaining)
            if seeking_time:
                self.bg_player.window.time_label.SetBackgroundColour((255, 200, 255, 255))
            else:
                self.bg_player.window.time_label.SetBackgroundColour(
                    wx.SystemSettings_GetColour(wx.SYS_COLOUR_FRAMEBK))
                pass

        player_state = self.bg_player.player.get_state()
        status = '%s Vol:%d Time:%s' % ('Seeking' if seeking_time else self.player_state_parse(player_state),
                                        self.bg_player.player.audio_get_volume(),
                                        time_remaining)

        if 'Fading' not in self.bg_player_status:
            self.bg_player_status = status

        if player_state in range(4, 8):
            self.bg_player_timer.Stop()
            if player_state != vlc.State.Paused and self.bg_player.window_exists():
                self.bg_player.window.time_slider.SetValue(0)
            if player_state == vlc.State.Ended:
                self.background_play(from_grid=False)

    def on_bg_seek(self, e):
        self.bg_player.player.set_time(e.Int)
        self.bg_player_timer_start(self.bg_player.timer_update_ms)

    def play_pause_bg(self, e=None, play=None):
        state = self.bg_player.player.get_state()
        playing = state == vlc.State.Playing
        if play is None:
            play = not playing
        if playing == play:
            return
        if play:
            if state == vlc.State.Paused:
                self.background_pause(paused=False)
            else:
                self.background_play(from_grid=False)
        else:
            self.background_pause(paused=True)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame(None, 'Fest Engine')
    app.MainLoop()
