#!python3
# -*- coding: utf-8 -*-

import bisect
import os
import re
import sys
import threading
import subprocess
import time
import webbrowser
import json
import functools
import gettext
import copy

import vlc
import wx
import wx.grid

from background_music_player import BackgroundMusicPlayer
from constants import Config, Colors, Columns, FileTypes, Strings
from projector import ProjectorWindow
from settings import SettingsDialog
from logger import Logger
from file_replacer import FileReplacer
from text_window import TextWindow
from os_tools import path
from timecode_window import TimecodeWindow

locale_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'locale')
if os.path.isfile(os.path.join(locale_dir, 'ru', 'LC_MESSAGES', 'main.mo')):
    gettext.translation('main', locale_dir, ['ru']).install()
else:
    import builtins
    builtins.__dict__['_'] = lambda t: t

if sys.platform.startswith('linux'):
    try:
        import ctypes
        x11 = ctypes.cdll.LoadLibrary(ctypes.util.find_library('X11'))
        x11.XInitThreads()
    except Exception as x_init_threads_ex:
        print("XInitThreads() call failed:", x_init_threads_ex)


class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title, size=(800, 400))
        self.Bind(wx.EVT_CLOSE, self.on_close, self)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        self.player_time_update_interval_ms = 300
        self.fade_out_delays_ms = 10
        self.logger = Logger(self)
        base_config = {Config.PROJECTOR_SCREEN: wx.Display.GetCount() - 1,  # The last one
                       Config.VLC_ARGUMENTS: "--file-caching=1000 --no-drop-late-frames --no-skip-frames",
                       Config.FILENAME_RE: "^(?P<num>\d{1,3})\W{1,3}(?P<name>.*)$",
                       Config.BG_TRACKS_DIR: "",
                       Config.BG_ZAD_PATH: "",
                       Config.FILES_DIRS: [""],
                       Config.BG_FADE_STOP_DELAYS: 0.03,
                       Config.BG_FADE_PAUSE_DELAYS: 0.01,
                       Config.C2_DATABASE_PATH: "",
                       Config.TEXT_WIN_FIELDS: ["Пожелания по сценическому свету (необязательно)"],
                       Config.COUNTDOWN_OPENING_TEXT: u"До начала фестиваля",
                       Config.COUNTDOWN_INTERMISSION_TEXT: u"До конца перерыва",
                       Config.COUNTDOWN_TIME_FMT: u"Ждём Вас в %s ^_^"}

        self.config_ok = False
        self.fest_file_path = ''
        if os.path.isfile(Config.LAST_SESSION_PATH):
            try:
                self.fest_file_path = open(Config.LAST_SESSION_PATH, 'r', encoding='utf-8-sig').read()
            except UnicodeDecodeError:
                try:
                    self.fest_file_path = open(Config.LAST_SESSION_PATH, 'r', encoding='latin-1').read()
                except UnicodeDecodeError:
                    print("Fail to read last session file.")
                    self.fest_file_path = ''

            self.fest_file_path = path.make_abs(self.fest_file_path)

            if os.path.isfile(self.fest_file_path):
                try:
                    loaded_config = json.load(open(self.fest_file_path, 'r', encoding='utf-8-sig'))
                    config_keys_diff = set(base_config.keys()) - set(loaded_config.keys())
                    if config_keys_diff:
                        self.logger.log("[WARNING] Config file is missing the following keys: " + str(config_keys_diff))
                    self.config = {**base_config, **loaded_config}  # Merging base config with loaded
                    self.config_ok = True
                except json.decoder.JSONDecodeError as e:
                    msg = _("Unfortunately, you broke the JSON format...\n"
                            "Please fix the configuration file%s ASAP.\n\nDetails: %s") % \
                          ("\n(%s)" % self.fest_file_path, str(e))
                    wx.MessageBox(msg, "JSON Error", wx.OK | wx.ICON_ERROR, self)
            else:
                self.logger.log("Session path %s is not file" % self.fest_file_path)
                self.fest_file_path = ''

        path.fest_file = self.fest_file_path  # TODO: Remove self.fest_file_path

        if not self.config_ok:
            self.config = base_config

        self.proj_win = None
        self.text_win = None
        self.timecode_win = None
        self.req_id_field_number = None
        self.filename_re = None
        self.grid_cols = None
        self.data = {}
        self.in_search = False
        self.grid_default_bg_color = None
        self.full_grid_data = None
        self.num_in_player = None
        self.current_playing_row = None

        self.player_time_update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.player_time_update, self.player_time_update_timer)

        self.bg_player = BackgroundMusicPlayer(self)
        self.bg_player_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_background_timer, self.bg_player_timer)

        self.bg_tracks_dir = None
        self.files_dirs = [path.make_abs(d, path.fest_file) for d in self.config[Config.FILES_DIRS]]

        # ------------------ Menu ------------------
        menu_bar = wx.MenuBar()

        # --- Main ---
        menu_file = wx.Menu()

        self.load_data_item = menu_file.Append(wx.ID_ANY, _("&Load ZAD and MP3"))
        self.Bind(wx.EVT_MENU, self.load_files, self.load_data_item)

        menu_file.AppendSeparator()

        if self.fest_file_path:
            session_folder, session_file = os.path.split(self.fest_file_path)
            self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(os.path.abspath(session_folder)),
                      menu_file.Append(wx.ID_ANY, _("Open &Folder with '%s'") % session_file))

        for folder in self.files_dirs:
            self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(os.path.abspath(folder)),
                      menu_file.Append(wx.ID_ANY, _("Open '%s' Folder") % os.path.basename(folder)))

        self.Bind(wx.EVT_MENU, lambda e: webbrowser.open(self.bg_tracks_dir),
                  menu_file.Append(wx.ID_ANY, _("Open &Background Music Folder")))

        menu_file.AppendSeparator()

        self.Bind(wx.EVT_MENU, self.on_settings, menu_file.Append(wx.ID_ANY, _("&Settings")))

        show_log_menu_item = menu_file.Append(wx.ID_ANY, _("&Show Log"))

        def on_log(e):
            self.logger.open_window(lambda: show_log_menu_item.Enable(True))
            show_log_menu_item.Enable(False)

        self.Bind(wx.EVT_MENU, on_log, show_log_menu_item)

        self.prefer_audio = menu_file.Append(wx.ID_ANY, _("&Prefer No Video (fallback)"), kind=wx.ITEM_CHECK)
        self.prefer_audio.Check(False)

        self.end_show_on_bg = menu_file.Append(wx.ID_ANY, _("&End show on BG Music Start"), kind=wx.ITEM_CHECK)
        self.end_show_on_bg.Check(False)

        self.auto_zad = menu_file.Append(wx.ID_ANY, _("Auto Show &ZAD with Sound"), kind=wx.ITEM_CHECK)

        menu_file.AppendSeparator()

        self.Bind(wx.EVT_MENU, lambda _: webbrowser.open('https://github.com/Himura2la/FestEngine'),
                  menu_file.Append(wx.ID_ABOUT, _("&About")))
        self.Bind(wx.EVT_MENU, lambda e: self.Close(True),
                  menu_file.Append(wx.ID_EXIT, _("E&xit")))
        menu_bar.Append(menu_file, _("&Main"))

        # --- Item ---
        menu_item = wx.Menu()

        self.replace_file_item = menu_item.Append(wx.ID_ANY, _("&Replace File"))
        self.replace_file_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.replace_file, self.replace_file_item)

        self.del_row_item = menu_item.Append(wx.ID_ANY, _("&Delete item"))
        self.del_row_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.del_row, self.del_row_item)

        menu_item.AppendSeparator()

        self.Bind(wx.EVT_MENU,
                  lambda e: self.add_countdown_row(False, message=self.config[Config.COUNTDOWN_INTERMISSION_TEXT]),
                  menu_item.Append(wx.ID_ANY, _("&Add intermission (countdown) above")))
        self.Bind(wx.EVT_MENU,
                  lambda e: self.add_countdown_row(True, message=self.config[Config.COUNTDOWN_INTERMISSION_TEXT]),
                  menu_item.Append(wx.ID_ANY, _("&Add intermission (countdown) below")))

        menu_bar.Append(menu_item, _("&Item"))

        # --- Projector Window ---
        proj_win_menu = wx.Menu()
        self.Bind(wx.EVT_MENU, self.ensure_proj_win, proj_win_menu.Append(wx.ID_ANY, _("&Create")))
        self.destroy_proj_win_item = proj_win_menu.Append(wx.ID_ANY, _("&Destroy"))
        self.destroy_proj_win_item.Enable(False)
        self.Bind(wx.EVT_MENU, self.destroy_proj_win, self.destroy_proj_win_item)
        menu_bar.Append(proj_win_menu, _("&Projector Window"))

        # --- Text Windows ---
        text_win_menu = wx.Menu()
        self.text_win_show_item = text_win_menu.Append(wx.ID_ANY, _("&Show Info Window"), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.text_win_show, self.text_win_show_item)
        self.text_win_full_info = text_win_menu.Append(wx.ID_ANY, _("&Full Info"), kind=wx.ITEM_CHECK)
        self.text_win_full_info.Enable(False)
        self.timecode_win_show_item = text_win_menu.Append(wx.ID_ANY, _("&Show Timecode Window"), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self.timecode_win_show, self.timecode_win_show_item)

        def on_full_info_switch(e):
            if self.text_win:
                self.text_win.show_full_info = bool(e.Selection)
        self.Bind(wx.EVT_MENU, on_full_info_switch, self.text_win_full_info)

        menu_bar.Append(text_win_menu, _("&Text Windows"))

        # --- Background Music ---
        menu_bg_music = wx.Menu()

        self.Bind(wx.EVT_MENU, self.on_bg_load_files,
                  menu_bg_music.Append(wx.ID_ANY, _("&Load Files")))
        self.Bind(wx.EVT_MENU, lambda e: self.bg_player.show_window(),
                  menu_bg_music.Append(wx.ID_ANY, _("&Open Window")))

        menu_bg_music.AppendSeparator()

        self.bg_fade_switch = menu_bg_music.Append(wx.ID_ANY, _("&Fade In/Out Enabled"), kind=wx.ITEM_CHECK)
        self.bg_fade_switch.Check(self.bg_player.fade_in_out)
        self.Bind(wx.EVT_MENU, self.fade_switched, self.bg_fade_switch)

        self.play_bg_item = menu_bg_music.Append(wx.ID_ANY, _("&Play Selected Item\tF4"))
        self.Bind(wx.EVT_MENU, lambda e: self.background_play(from_grid=True), self.play_bg_item)
        self.play_bg_item.Enable(False)

        self.bg_pause_switch = menu_bg_music.Append(wx.ID_ANY, _("&Pause\tF3"), kind=wx.ITEM_CHECK)
        self.bg_pause_switch.Enable(False)
        self.Bind(wx.EVT_MENU, self.background_set_pause, self.bg_pause_switch)

        menu_bar.Append(menu_bg_music, _("&Background Music"))

        # --- Fire (Play) ---
        menu_play = wx.Menu()
        emergency_stop_item = menu_play.Append(wx.ID_ANY, _("&Emergency Stop All\tShift+Esc"))
        show_zad_item = menu_play.Append(wx.ID_ANY, _("Show &ZAD\tF1"))
        clear_zad_item = menu_play.Append(wx.ID_ANY, _("&Clear ZAD\tShift+F1"))
        play_track_item = menu_play.Append(wx.ID_ANY, _("&Play Sound/Video\tF2"))
        fade_out_item = menu_play.Append(wx.ID_ANY, _("&Fade Out\tShift+F2"))
        end_show_item = menu_play.Append(wx.ID_ANY, _("&End Show (Clear ZAD + Fade Out)\tEsc"))
        no_show_item = menu_play.Append(wx.ID_ANY, _("&Black Screen\tAlt+F1"))
        menu_play.AppendSeparator()
        self.play_pause_bg_end_show_item = menu_play.Append(wx.ID_ANY, _("Play/Pause &Background (+ End Show)\tF3"))
        self.play_pause_bg_end_show_item.Enable(False)
        self.play_next_bg_item = menu_play.Append(wx.ID_ANY, _("Play &Next BG Track\tShift+F4"))
        self.play_next_bg_item.Enable(False)

        self.Bind(wx.EVT_MENU, self.emergency_stop, emergency_stop_item)
        self.Bind(wx.EVT_MENU, self.show_zad, show_zad_item)
        self.Bind(wx.EVT_MENU, self.clear_zad, clear_zad_item)
        self.Bind(wx.EVT_MENU, self.play_async, play_track_item)
        self.Bind(wx.EVT_MENU, self.stop_async, fade_out_item)
        self.Bind(wx.EVT_MENU, self.end_show, end_show_item)
        self.Bind(wx.EVT_MENU, lambda e: self.clear_zad(e, True), no_show_item)
        self.Bind(wx.EVT_MENU, self.play_pause_bg_end_show, self.play_pause_bg_end_show_item)
        self.Bind(wx.EVT_MENU, self.background_play, self.play_next_bg_item)

        self.SetAcceleratorTable(wx.AcceleratorTable([
            wx.AcceleratorEntry(wx.ACCEL_SHIFT, wx.WXK_ESCAPE, emergency_stop_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F1, show_zad_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_SHIFT, wx.WXK_F1, clear_zad_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F2, play_track_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_SHIFT, wx.WXK_F2, fade_out_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, end_show_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_ALT, wx.WXK_F1, no_show_item.GetId()),

            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F3, self.play_pause_bg_end_show_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F4, self.play_bg_item.GetId()),
            wx.AcceleratorEntry(wx.ACCEL_SHIFT, wx.WXK_F4, self.play_next_bg_item.GetId())]))

        # In the end of `background_music_player.py` it is repeated

        menu_bar.Append(menu_play, _("&Fire"))

        self.SetMenuBar(menu_bar)

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.toolbar = wx.BoxSizer(wx.HORIZONTAL)
        win = sys.platform.startswith('win')
        toolbar_base_height = 20 if win else 36

        # self.status_color_box = wx.Panel(self, size=(toolbar_base_height, toolbar_base_height))
        # self.toolbar.Add(self.status_color_box, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, border=1)
        # self.status_color_box.SetBackgroundColour((0, 255, 0))
        # TODO: #9

        self.toolbar.Add(wx.StaticText(self, label=' VOL '), 0, wx.ALIGN_CENTER_VERTICAL)
        self.vol_control = wx.SpinCtrl(self, value='-1', size=(50 if win else 120, toolbar_base_height))
        self.toolbar.Add(self.vol_control, 0, wx.ALIGN_CENTER_VERTICAL)
        self.vol_control.SetRange(-1, 200)
        self.vol_control.Bind(wx.EVT_SPINCTRL, self.set_vol, self.vol_control)

        self.fade_out_btn = wx.Button(self, label=_("Fade out"), size=(-1, toolbar_base_height + 2))
        self.fade_out_btn.Enable(False)
        self.toolbar.Add(self.fade_out_btn, 0)
        self.fade_out_btn.Bind(wx.EVT_BUTTON, self.stop_async)

        self.time_bar = wx.Gauge(self, range=1, size=(-1, toolbar_base_height))
        self.toolbar.Add(self.time_bar, 1, wx.ALIGN_CENTER_VERTICAL)
        self.time_label = wx.StaticText(self, label='Stop', size=(50, -1), style=wx.ALIGN_CENTER)
        self.toolbar.Add(self.time_label, 0, wx.ALIGN_CENTER_VERTICAL)

        self.search_box = wx.TextCtrl(self, size=(60, toolbar_base_height), value=_('Find'), style=wx.TE_PROCESS_ENTER)
        self.search_box.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
        self.toolbar.Add(self.search_box, 0, wx.ALIGN_CENTER_VERTICAL)

        def search_box_leave_handler(e):
            if self.search_box.GetValue() == '':
                self.quit_search()
            e.Skip()

        self.search_box.Bind(wx.EVT_SET_FOCUS, self.enter_search)
        self.search_box.Bind(wx.EVT_KILL_FOCUS, search_box_leave_handler)
        self.search_box.Bind(wx.EVT_TEXT, self.search)
        self.search_box.Bind(wx.EVT_RIGHT_DOWN, self.quit_search)
        self.search_box.SetToolTip(_('Right-click to quit search'))
        self.search_box.Bind(wx.EVT_TEXT_ENTER, self.quit_search)

        self.vid_btn = wx.ToggleButton(self, label='VID', size=(35 if win else 50, toolbar_base_height + 2))
        self.zad_btn = wx.ToggleButton(self, label='ZAD', size=(35 if win else 50, toolbar_base_height + 2))
        self.vid_btn.Enable(False)
        self.zad_btn.Enable(False)
        self.toolbar.Add(self.vid_btn, 0)
        self.toolbar.Add(self.zad_btn, 0)

        # --- Grid ---
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 0)
        self.grid.HideRowLabels()
        self.grid.DisableDragRowSize()
        self.grid.SetColLabelSize(20)
        self.grid.SetSelectionMode(wx.grid.Grid.GridSelectRows)

        def select_row(e):
            if not e.Selecting() or hasattr(e, 'TopRow') and e.TopRow == e.BottomRow:
                return
            row = e.Row if hasattr(e, 'Row') else self.grid.GridCursorRow
            self.grid.Unbind(wx.grid.EVT_GRID_RANGE_SELECT)
            self.grid.SelectRow(row)
            self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)
            item_is_track = self.row_type(row) == 'track'
            self.del_row_item.Enable(not item_is_track)
            self.replace_file_item.Enable(item_is_track)

            def text_win_load():
                num = self.get_num(row)
                if num not in self.data:
                    self.text_win.clear(num)
                    return
                row_data = self.data[num]
                if Columns.C2_REQUEST_ID in row_data:
                    req_id = row_data[Columns.C2_REQUEST_ID]
                elif '_' + Columns.C2_REQUEST_ID in row_data:
                    req_id = row_data['_' + Columns.C2_REQUEST_ID]
                else:
                    self.logger.log('No request id column found in filenames. Add "{0}" or "_{0}" to your regex'
                                    .format(Columns.C2_REQUEST_ID))
                    self.text_win.clear()
                    return
                self.text_win_load(req_id)

            if self.text_win:
                text_win_load()

            if not self.is_playing:
                self.set_timecode('№ %s ■' % self.get_num(row))

        # Binded after loading data to prevent self.row_type() calls for incomplete grid

        def play_if_track(e):
            if self.row_type(self.grid.GetGridCursorRow()) != 'countdown' and self.grid.GetGridCursorCol() != self.grid_cols.index(Columns.NOTES):
                self.play_async(e)
            else:
                e.Skip()

        def on_grid_key_down(e):
            if e.KeyCode in {wx.WXK_UP, wx.WXK_DOWN}:
                wx.CallAfter(self.grid_align_viewpoint)  # Should start after select_row()
                e.Skip()
            elif e.KeyCode == wx.WXK_RETURN:
                play_if_track(e)  # For emergency situations
            else:
                e.Skip()

        # Binded after loading data to prevent self.row_type() calls for incomplete grid

        self.grid.Bind(wx.EVT_KEY_DOWN, on_grid_key_down)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_DCLICK, play_if_track)  # For emergency situations

        main_sizer.Add(self.toolbar, 0, wx.EXPAND)
        main_sizer.Add(self.grid, 1, wx.EXPAND | wx.TOP, border=1)

        self.SetSizer(main_sizer)

        # ------------------ Status Bar ------------------
        self.status_bar = self.CreateStatusBar(4)
        self.status("Ready")

        # ----------------------- VLC ---------------------

        self.vlc_instance = vlc.Instance(self.config[Config.VLC_ARGUMENTS])

        self.player = self.vlc_instance.media_player_new()
        self.player.audio_set_volume(100)
        self.player.audio_set_mute(False)

        # https://github.com/maddox/vlc/blob/master/src/control/video.c#L626
        # https://wiki.videolan.org/deinterlacing
        self.player.video_set_deinterlace("blend")

        self.vol_control.SetValue(self.player.audio_get_volume())

        self.player_status = "VLC %s: %s" % \
                             (vlc.libvlc_get_version().decode(), self.player_state_parse(self.player.get_state()))
        self.bg_player_status = "Background Player: %s" % self.player_state_parse(self.bg_player.player.get_state())

        self.Show(True)
        self.grid.SetFocus()

        def init():
            if not self.config_ok:
                self.on_settings()
            else:
                self.load_files()
                if self.config[Config.BG_TRACKS_DIR]:
                    self.on_bg_load_files()
            self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_cell_changed)
            self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL, select_row)
            self.grid.Bind(wx.grid.EVT_GRID_RANGE_SELECT, select_row)
            self.grid.Bind(wx.EVT_SIZE, self.grid_autosize_notes_col)

        wx.CallAfter(init)

    # ------------------------------------------------------------------------------------------------------------------

    def grid_set_shape(self, new_rows, new_cols, readonly=False):
        current_rows, current_cols = self.grid.GetNumberRows(), self.grid.GetNumberCols()
        if current_rows > 0:
            self.grid.DeleteRows(0, current_rows, False)
        self.grid.AppendRows(new_rows)
        if new_cols < current_cols:
            self.grid.DeleteCols(0, current_cols - new_cols, False)
        elif new_cols > current_cols:
            self.grid.AppendCols(new_cols - current_cols)

        [self.set_cell_readonly(row, col, readonly) for row in range(new_rows) for col in range(new_cols)]

    def grid_align_viewpoint(self):  # https://stackoverflow.com/a/15894331/3399377
        row = self.grid.GetGridCursorRow()
        cell_origin = self.grid.CellToRect(row, 0).y / self.grid.GetScrollPixelsPerUnit()[1]
        full_page = self.grid.GetScrollPageSize(wx.VERTICAL)
        scroll_target = cell_origin - full_page / 6
        self.grid.Scroll((0, scroll_target))

    def grid_autosize_notes_col(self, e=None):
        if self.grid_cols:
            notes_col = self.grid_cols.index(Columns.NOTES)
            w = self.grid.GetClientSize()[0] - self.grid.GetRowLabelSize()
            col_sizes = sum([self.grid.GetColSize(i) for i in range(self.grid.GetNumberCols())])
            free_space = w - col_sizes
            notes_col_size = self.grid.GetColSize(notes_col)
            target_notes_col_size = notes_col_size + free_space
            if target_notes_col_size > 40:
                self.grid.SetColSize(notes_col, target_notes_col_size)
        if e:
            e.Skip()

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

    # -------------------------------------------------- Actions --------------------------------------------------

    def on_close(self, e=None):
        self.destroy_proj_win()
        self.on_text_win_close()
        self.on_timecode_win_close()
        self.player.stop()
        self.vlc_instance.release()
        if e:
            e.Skip()
        else:
            self.Close(True)

    def on_settings(self, e=None):
        prev_config = copy.copy(self.config)
        with SettingsDialog(self.fest_file_path, self.config, self) as settings_dialog:
            action = settings_dialog.ShowModal()

            self.fest_file_path = path.make_abs(settings_dialog.fest_file_path)  # To be sure.
            path.fest_file = self.fest_file_path
            self.config = settings_dialog.config                        # Maybe redundant
            self.config_ok = action in {wx.ID_SAVE, wx.ID_OPEN}

        if prev_config != self.config:  # Safety is everything!
            bkp_name = "%s-%s.bkp.fest" % (os.path.splitext(self.fest_file_path)[0],
                                           time.strftime("%d%m%y%H%M%S", time.localtime()))
            json.dump(prev_config, open(bkp_name, 'w', encoding='utf-8'),
                      ensure_ascii=False, indent=4)

        if prev_config[Config.FILES_DIRS] != self.config[Config.FILES_DIRS] or \
                        prev_config[Config.FILENAME_RE] != self.config[Config.FILENAME_RE]:
            with wx.MessageDialog(self, _("You may want to restart FestEngine. Do it?"),
                                  _("Restart Required"), wx.YES_NO | wx.ICON_INFORMATION) as restart_dialog:
                action = restart_dialog.ShowModal()
                if action == wx.ID_YES:
                    subprocess.Popen([sys.executable] + sys.argv)
                    self.on_close()

    def on_proj_win_close(self, e):
        self.proj_win.countdown_panel.timer.Stop()
        self.proj_win.Destroy()
        self.proj_win = None

    def on_bg_player_win_close(self, e):
        self.bg_player.window.Destroy()
        self.bg_player.window = None
        self.play_bg_item.Enable(False)

    def ensure_proj_win(self, e=None):
        no_window = not self.proj_win
        if no_window:
            self.proj_win = ProjectorWindow(self, self.config[Config.PROJECTOR_SCREEN])

            self.vid_btn.Bind(wx.EVT_TOGGLEBUTTON, self.switch_to_vid)
            self.zad_btn.Bind(wx.EVT_TOGGLEBUTTON, self.switch_to_zad)
            self.switch_to_zad()
            self.image_status("Projector Window Created")
        self.vid_btn.Enable(True)
        self.zad_btn.Enable(True)
        self.proj_win.Show()
        self.destroy_proj_win_item.Enable(True)
        wx.CallAfter(self.Raise)
        return no_window

    def destroy_proj_win(self, e=None):
        if not self.proj_win:
            return
        self.proj_win.Close(True)
        self.vid_btn.SetValue(False)
        self.vid_btn.Enable(False)
        self.zad_btn.SetValue(False)
        self.zad_btn.Enable(False)
        self.destroy_proj_win_item.Enable(False)
        self.image_status("Projector Window Destroyed")

    def switch_to_vid(self, e=None):
        """ Call set_vlc_video_panel() until it returns True after this"""
        if not self.proj_win:
            return
        self.vid_btn.SetValue(True)
        self.zad_btn.SetValue(False)
        self.proj_win.switch_to_video()

    def set_vlc_video_panel(self):
        handle = self.proj_win.video_panel.GetHandle()
        if not handle:
            return False
        if sys.platform.startswith('linux'):  # for Linux using the X Server
            self.player.set_xwindow(handle)
        elif sys.platform == "win32":  # for Windows
            self.player.set_hwnd(handle)
        elif sys.platform == "darwin":  # for MacOS
            self.player.set_nsobject(handle)
        return True

    def switch_to_zad(self, e=None):
        if not self.proj_win:
            return
        self.vid_btn.SetValue(False)
        self.zad_btn.SetValue(True)
        self.proj_win.switch_to_images()

    def show_zad(self, e=None):
        self.ensure_proj_win()
        if self.get_num(self.grid.GetGridCursorRow()) == 'countdown':
            self.play_async()
            return

        def delayed_run():
            num = self.get_num(self.grid.GetGridCursorRow())
            try:
                file_path = [f[1] for f in self.data[num]['files'].items() if f[0] in FileTypes.img_extensions][0]
                if any([file_path.endswith(e) for e in FileTypes.video_extensions]):
                    self.switch_to_vid()
                    self.player.set_media(self.vlc_instance.media_new(file_path))
                    while not self.set_vlc_video_panel():
                        pass
                    self.player.audio_set_mute(False)
                    self.player.audio_set_volume(self.vol_control.GetValue())
                    if self.player.play() != 0:  # [Play] button is pushed here!
                        wx.CallAfter(lambda: self.image_status(u"Video ZAD FAILED №%s" % num))
                        return
                else:
                    self.switch_to_zad()
                    self.proj_win.load_zad(file_path, True)
                self.image_status(u"Showing №%s" % num)
                self.status("ZAD Fired!")
                wx.CallAfter(lambda: self.proj_win.Layout())
            except IndexError:
                self.clear_zad(status=u"No ZAD for №%s" % num)

        if self.ensure_proj_win():
            wx.CallAfter(delayed_run)
        else:
            delayed_run()

    def clear_zad(self, e=None, no_show=False, status=u"ZAD Cleared"):
        if not self.proj_win:
            return
        self.proj_win.switch_to_images()
        if self.config[Config.BG_ZAD_PATH] and not no_show:
            self.proj_win.load_zad(path.make_abs(self.config[Config.BG_ZAD_PATH],
                                                 path.fest_file), True)
            self.image_status("Background")
        else:
            self.proj_win.no_show()
            self.image_status("No show")
        self.status(status)

    def end_show(self, e=None):
        self.stop_async()
        self.clear_zad()

    def emergency_stop(self, e=None):
        self.clear_zad()
        self.stop_async(fade_out=False)

        bg_fade_state = self.bg_player.fade_in_out
        self.bg_player.fade_in_out = False
        self.background_set_pause(paused=True)
        self.bg_player.fade_in_out = bg_fade_state

        self.status("EMERGENCY STOP !!!")

    # -------------------------------------------------- Data --------------------------------------------------

    def load_files(self, e=None):
        filename_re = self.config[Config.FILENAME_RE]
        if not self.files_dirs or not all([os.path.isdir(d) for d in self.files_dirs]) or not filename_re:
            msg = _("No filename regular expression or ZAD path is invalid or MP3 path is invalid.\n"
                    "Please specify valid paths to folders with your files, and regular\n"
                    "expression that parses your filenames in settings or .fest file.\n\n"
                    "Directories: %s\n"
                    "Filename RegEx: %s") % (", ".join(self.files_dirs), filename_re)
            wx.MessageBox(msg, _("Path Error"), wx.OK | wx.ICON_ERROR, self)
            return

        self.filename_re = re.compile(filename_re)
        # Extracting groups from regular expression (yes, your filename_re must contain groups wigh good names)
        group_names, group_positions = zip(*sorted(self.filename_re.groupindex.items(), key=lambda a: a[1]))

        if 'num' not in group_names:
            msg = _("No 'num' group in filename RegEx. We recommend using a unique sorting-friendly three-digit\n"
                    "number at the beginning of all filenames. The order should correspond to your event's program\n\n"
                    "In this case the RegEx will look like this: ^(?P<num>\d{3})(?P<name>.*)\n\n"
                    "Your filename RegEx: %s") % filename_re
            wx.MessageBox(msg, "Filename RegEx Error", wx.OK | wx.ICON_ERROR, self)
            return

        if Columns.NAME not in group_names:
            msg = _("No '%s' group in filename RegEx. It is required to set the countdown description.\n\n"
                    "The simplest RegEx looks like this: ^(?P<num>\d{3})(?P<name>.*)\n\n"
                    "Your filename RegEx: %s") % (Columns.NAME, filename_re)
            wx.MessageBox(msg, "Filename RegEx Error", wx.OK | wx.ICON_ERROR, self)
            return

        # Making columns from filename_re groups
        self.grid_cols = [r if r != 'num' else Columns.NUM
                          for r in group_names if r[0] != '_'] + [Columns.FILES, Columns.NOTES]

        all_files = [[os.path.join(d, path) for path in os.listdir(d)] for d in self.files_dirs]
        all_files = [item for sublist in all_files for item in sublist]  # Flatten

        for file_path in all_files:
            if not os.path.isfile(file_path):
                continue
            name, ext = os.path.basename(file_path).rsplit('.', 1)
            ext = ext.lower()
            if name.endswith(".zad"):
                ext = "zad." + ext
                name = name[:-4]
            match = re.search(self.filename_re, name)
            if not match:
                self.logger.log(_("[WARNING] File %s does not match filename_re") % file_path)
                continue
            num = match.group('num')

            if num not in self.data:
                self.data[num] = {}

            for group in group_names:
                value = match.group(group)
                if value and group != 'num':
                    if group in self.data[num] and self.data[num][group] != value:
                        self.logger.log(_("[WARNING] Inconsistent value '%s': changing '%s' to '%s'.\n\t\tItem: %s") %
                                        (group, self.data[num][group], value, str(self.data[num])))
                    self.data[num][group] = value

            if 'files' not in self.data[num]:
                self.data[num]['files'] = {}

            if ext not in self.data[num]['files']:
                self.data[num]['files'][ext] = file_path
            else:
                msg = _("Duplicate files found:\n%s\nConflicts with: %s") % (file_path, self.data[num])
                self.logger.log('[!!! ALERT !!!] ' + msg)
                wx.MessageBox('ALERT !!!\n' + msg, "Duplicate files alert", wx.OK | wx.ICON_ERROR)

        self.grid_set_shape(len(self.data), len(self.grid_cols))
        [self.grid.SetColLabelValue(i, v) for i, v in enumerate(self.grid_cols)]

        i = 0
        for num, data in sorted(self.data.items()):
            for j, row in enumerate(self.grid_cols):
                if row == Columns.NUM:
                    self.grid.SetCellValue(i, j, num)
                elif row == Columns.FILES:
                    self.grid.SetCellValue(i, j, ", ".join(sorted([ext for ext in data['files'].keys()])))
                elif row in data:
                    self.grid.SetCellValue(i, j, data[row])
                self.set_cell_readonly(i, j)
            i += 1

        self.grid.AutoSizeColumns()
        self.status("Loaded %d items" % i)

        self.add_countdown_row(False, 0, self.config[Config.COUNTDOWN_OPENING_TEXT])

        self.SetLabel("%s: %s" % (Strings.APP_NAME, self.fest_file_path))

        self.load_data_item.Enable(False)  # Safety is everything!

        self.grid_autosize_notes_col()

    # --- Duplication from notes ---

    def on_grid_cell_changed(self, e):
        self.grid.Unbind(wx.grid.EVT_GRID_CELL_CHANGED)

        if self.grid.GetColLabelValue(e.Col) == Columns.NOTES:
            note = self.grid.GetCellValue(e.Row, e.Col)
            match = re.search('>(\d{3}(\w)?)([^\w].*)?', note)  # ">234" or ">305a" or ">152a maybe"
            if match:
                new_num, _, note = match.groups()

                row = {self.grid.GetColLabelValue(i): {'col': i, 'val': self.grid.GetCellValue(e.Row, i)}
                       for i in range(self.grid.GetNumberCols())}

                old_num = row[Columns.NUM]['val']
                row[Columns.NUM]['val'] = new_num
                row[Columns.NOTES]['val'] = '<%s %s' % (old_num, note) if note else '<%s' % old_num

                nums = [self.grid.GetCellValue(i, row[Columns.NUM]['col']) for i in range(self.grid.GetNumberRows())]

                if new_num not in nums or self.row_type(nums.index(new_num)) != 'dup':
                    i = ord('a')
                    while row[Columns.NUM]['val'] in nums:  # If num already exists, append a letter
                        row[Columns.NUM]['val'] = new_num + chr(i)
                        i += 1
                    new_row = bisect.bisect(nums, row[Columns.NUM]['val'])  # determining row insertion point
                    self.grid.InsertRows(new_row, 1)
                else:
                    new_row = nums.index(new_num)  # Updating

                for cell in row.values():
                    self.grid.SetCellValue(new_row, cell['col'], cell['val'])
                    self.grid.SetCellBackgroundColour(new_row, cell['col'], Colors.DUP_ROW)
                    self.set_cell_readonly(new_row, cell['col'], True)

        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_grid_cell_changed)

    def row_type(self, row):
        num = self.grid.GetCellValue(row, self.grid_cols.index(Columns.NUM))
        notes = self.grid.GetCellValue(row, self.grid_cols.index(Columns.NOTES))

        if notes and notes[0] == '<':
            return 'dup'
        elif num == Strings.COUNTDOWN_ROW_TEXT_SHORT:
            return 'countdown'
        else:
            return 'track'

    def get_num(self, row):
        row_type = self.row_type(row)
        if row_type == 'track':
            return self.grid.GetCellValue(row, self.grid_cols.index(Columns.NUM))
        elif row_type == 'dup':
            return self.grid.GetCellValue(row, self.grid_cols.index(Columns.NOTES))[1:4]
        else:
            return row_type

    def del_row(self, e=None):
        row = self.grid.GetGridCursorRow()
        if self.row_type(row) != 'track':  # Extra check, this method is very dangerous.
            self.grid.DeleteRows(row)

    def set_cell_readonly(self, row, col, force_readonly=False):
        editable = self.row_type(row) == 'countdown' and col == self.grid_cols.index(Columns.NAME) or \
                   col == self.grid_cols.index(Columns.NOTES)
        self.grid.SetReadOnly(row, col, not editable or force_readonly)

    # --- Countdown timer ---

    def add_countdown_row(self, below_current_row, base_row=None, message=''):
        base_row = base_row if base_row else self.grid.GetGridCursorRow()

        row_pos = base_row + 1 if below_current_row else base_row

        self.grid.InsertRows(row_pos, 1)
        self.grid.SetCellValue(row_pos, self.grid_cols.index(Columns.NUM), Strings.COUNTDOWN_ROW_TEXT_SHORT)
        self.grid.SetCellValue(row_pos, self.grid_cols.index(Columns.FILES), Strings.COUNTDOWN_ROW_TEXT_FULL)
        self.grid.SetCellValue(row_pos, self.grid_cols.index(Columns.NAME), message)
        self.grid.SetCellValue(row_pos, self.grid_cols.index(Columns.NOTES), "30m")  # Can be 15:35

        for col in range(self.grid.GetNumberCols()):
            self.grid.SetCellBackgroundColour(row_pos, col, Colors.COUNTDOWN_ROW)
            self.set_cell_readonly(row_pos, col)

        self.grid.SelectRow(row_pos)

    # --- Replacer ---

    def replace_file(self, e):
        num = self.get_num(self.grid.GetGridCursorRow())

        with FileReplacer(self, num) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                wx.MessageBox(_("Original file backed up as\n'%s';\n\n"
                                "File\n'%s'\n\n"
                                "copied in place of\n'%s'") % (dlg.bkp_path, dlg.tgt_file, dlg.src_file))

    # --- Search ---

    def enter_search(self, e=None):
        if self.search_box.GetValue() == _('Find'):
            self.search_box.Clear()
            self.search_box.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))
            self.in_search = True
            self.grid_push()
            self.grid.SetDefaultCellBackgroundColour(Colors.FILTERED_GRID)
            self.grid.ForceRefresh()  # Updates colors
        if e:
            e.Skip()

    def grid_push(self):
        self.grid_default_bg_color = self.grid.GetDefaultCellBackgroundColour()
        self.full_grid_data = [{'cols': [self.grid.GetCellValue(row, col) for col in range(self.grid.GetNumberCols())],
                                'color': self.grid.GetCellBackgroundColour(row, 0)}
                               for row in range(self.grid.GetNumberRows())]

    def grid_pop(self):
        self.grid.SetDefaultCellBackgroundColour(self.grid_default_bg_color)
        self.grid_set_data(self.full_grid_data)
        self.grid.ForceRefresh()  # Updates colors

    def grid_set_data(self, dataset, default_bg_in_dataset=None, readonly=False):
        if not default_bg_in_dataset:
            default_bg_in_dataset = self.grid.GetDefaultCellBackgroundColour()
        rows, cols = len(dataset), len(dataset[0]['cols'])

        self.grid_set_shape(rows, cols, readonly)
        for row in range(rows):
            for col in range(cols):
                if dataset[row]['color'] != default_bg_in_dataset:
                    self.grid.SetCellBackgroundColour(row, col, dataset[row]['color'])
                    self.set_cell_readonly(row, col)
                self.grid.SetCellValue(row, col, dataset[row]['cols'][col])

    def search(self, e=None):
        string = self.search_box.GetValue()
        if string == _('Find') or not self.in_search or not string:
            return

        def match(row):
            """Returns True if any cell in a row matches"""
            return functools.reduce(lambda a, b: a or b, [self.search_box.GetValue().lower() in cell.lower()
                                                          for cell in row['cols']])

        filtered_grid_data = list(filter(match, self.full_grid_data))
        found = bool(filtered_grid_data)
        if found:
            self.grid_set_data(filtered_grid_data, self.grid_default_bg_color, True)
        self.paint_search_box(not found)

    def paint_search_box(self, val):
        if val:
            self.search_box.SetBackgroundColour((255, 200, 200))
        else:
            self.search_box.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.search_box.Refresh()

    def quit_search(self, e=None):
        if self.in_search:
            self.in_search = False
            self.paint_search_box(False)

            self.search_box.SetValue(_('Find'))
            self.search_box.SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

            selected_row = [self.grid.GetCellValue(self.grid.GetSelectedRows()[0], col)
                            for col in range(self.grid.GetNumberCols())]
            selected_row_i = 0
            for i, val in enumerate(self.full_grid_data):
                if val['cols'] == selected_row:
                    selected_row_i = i
                    break
            self.grid_pop()

            self.grid.SelectRow(selected_row_i)
            self.grid.SetGridCursor(selected_row_i, 0)
            wx.CallAfter(self.grid_align_viewpoint)

            self.grid.SetFocus()
            # if e: e.Skip() # Invokes default handler with context menu

    # -------------------------------------------------- Player --------------------------------------------------

    def play_async(self, e=None):
        num = self.get_num(self.grid.GetGridCursorRow())
        if self.is_playing and self.num_in_player == num:
            self.status(_("ALREADY PLAYING! Hit Esc to restart!"))
            return
        if num == 'countdown':
            notes = self.grid.GetCellValue(self.grid.GetGridCursorRow(), self.grid_cols.index(Columns.NOTES))
            self.ensure_proj_win()

            self.vid_btn.SetValue(False)
            self.zad_btn.SetValue(False)
            self.vid_btn.Enable(False)
            self.zad_btn.Enable(False)

            if not self.proj_win.launch_timer(notes, self.grid.GetCellValue(self.grid.GetGridCursorRow(),
                                                                            self.grid_cols.index(Columns.NAME))):
                self.status(_("Invalid countdown row"))
            else:
                self.status("Countdown started!")
            return
        try:
            files = self.data[num]['files'].items()  # (ext, path)
            is_stream = any([file[0] == 'm3u' for file in files])
            video_files = [file[1] for file in files if file[0] in FileTypes.video_extensions]

            if video_files and not self.prefer_audio.IsChecked():
                file_path = open(video_files[0], 'r').read() if is_stream else video_files[0]
                sound_only = False
            else:
                audio_files = [file[1] for file in files if file[0] in FileTypes.audio_extensions]
                file_path, sound_only = (audio_files[0], True) if audio_files else (video_files[0], False)
        except IndexError:
            self.player_status = _(u'Nothing to play for %s%s') % ('№', num)
            return
        self.play_pause_bg(play=False)
        self.player.set_media(self.vlc_instance.media_new(file_path))

        if not sound_only:
            self.ensure_proj_win()
            self.switch_to_vid()
        elif self.auto_zad.IsChecked():
            self.show_zad()

        self.num_in_player = num
        self.current_playing_row = self.grid.GetGridCursorRow()
        [self.grid.SetCellBackgroundColour(self.current_playing_row, col, Colors.ROW_PLAYING_NOW)
         for col in range(self.grid.GetNumberCols())]
        wx.CallAfter(self.grid.ForceRefresh)

        def delayed_run():
            threading.Thread(target=self.play_sync, args=(self.vol_control.GetValue(), sound_only)).start()
            self.player_time_update_timer.Start(self.player_time_update_interval_ms)

        wx.CallAfter(delayed_run)  # because set_vlc_video_panel() needs some time...

    def play_sync(self, target_vol, sound_only):
        if not sound_only:
            while not self.set_vlc_video_panel():
                self.logger.log("Trying to get video panel handler...")

        if self.player.play() != 0:  # [Play] button is pushed here!
            wx.CallAfter(lambda: self.set_player_status(_('Playback FAILED !!!')))
            return

        state = self.player.get_state()
        start = time.time()
        while state != vlc.State.Playing:
            state = self.player.get_state()
            status = "%s [%.3fs]" % (self.player_state_parse(state), (time.time() - start))
            wx.CallAfter(lambda: self.set_player_status(status))
            self.logger.log(status)
            time.sleep(0.007)
        self.logger.log("Started playback in %.0fms" % ((time.time() - start) * 1000))

        if not sound_only:
            wx.CallAfter(lambda: self.proj_win.Layout())

        wx.CallAfter(lambda: self.fade_out_btn.Enable(True))

        start = time.time()
        status = '#'
        self.player.audio_set_mute(False)
        self.player.audio_set_volume(target_vol)
        while self.player.audio_get_volume() != target_vol:
            self.player.audio_set_volume(target_vol)
            status = "Trying to unmute... [%.3fs]" % (time.time() - start)
            wx.CallAfter(lambda: self.set_player_status(status))
            self.logger.log(status)
            time.sleep(0.001)
        if status[0] == 'T':
            self.logger.log("Unmuted in %.0fms" % ((time.time() - start) * 1000))

        def ui_upd():
            self.player_status = '%s Vol:%d' % (self.player_state_parse(self.player.get_state()),
                                                self.player.audio_get_volume())
            self.status('SOUND Fired!')

        wx.CallAfter(ui_upd)

    def stop_async(self, e=None, fade_out=True):
        if not self.is_playing:
            return

        self.fade_out_btn.Enable(False)

        if self.current_playing_row is not None:
            [self.grid.SetCellBackgroundColour(self.current_playing_row, col, Colors.ROW_SKIPPED)
             for col in range(self.grid.GetNumberCols())]
            wx.CallAfter(self.grid.ForceRefresh)

        if fade_out:
            threading.Thread(target=self.fade_out_stop_sync,
                             args=(self.fade_out_btn.GetLabel(),)).start()
        else:
            self.player.stop()
            self.time_bar.SetRange(1)
            self.time_bar.SetValue(0)
            self.player_status = self.player_state_parse(self.player.get_state())
            self.time_label.SetLabel('Stopped')
            self.set_timecode('stop')

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
            self.time_bar.SetRange(1)
            self.time_bar.SetValue(0)
            self.player_status = self.player_state_parse(self.player.get_state())
            self.time_label.SetLabel('Stopped')
            self.set_timecode('stop')

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

    @property
    def is_playing(self):
        return self.player.get_state() in range(1, 4)  # Playing or going to play

    def player_time_update(self, e=None):
        if self.is_playing:
            track_length, track_time = self.player.get_length(), self.player.get_time()

            if sys.platform == "win32":  # FIXME: Don't know why it does not reach the end on win32
                gauge_length = track_length - 1000 if track_length > 1000 else track_length
                self.time_bar.SetRange(gauge_length)
                self.time_bar.SetValue(track_time if track_time <= gauge_length else gauge_length)
            elif 0 <= track_time < track_length:
                self.time_bar.SetRange(track_length)
                self.time_bar.SetValue(track_time)

            time_elapsed = '%02d:%02d' % divmod(track_time / 1000, 60)
            time_remaining = '-%02d:%02d' % divmod(track_length / 1000 - track_time / 1000, 60)
            self.time_label.SetLabel(time_elapsed)
            self.set_timecode('№ %s ▶ ' % self.num_in_player, time_elapsed)

            status = u'%s №%s V:%d T:%s' % (self.player_state_parse(self.player.get_state()), self.num_in_player,
                                            self.player.audio_get_volume(), time_remaining)
            if 'Fading' not in self.player_status:
                self.player_status = status
        else:  # Not playing
            self.time_bar.SetRange(1)
            self.time_bar.SetValue(0)
            self.time_label.SetLabel('Stop')
            self.set_timecode('stop')
            self.player_status = self.player_state_parse(self.player.get_state())
            self.switch_to_zad()

            if self.grid.GetCellBackgroundColour(self.current_playing_row, 0) != Colors.ROW_SKIPPED:
                [self.grid.SetCellBackgroundColour(self.current_playing_row, col, Colors.ROW_PLAYED_TO_END)
                 for col in range(self.grid.GetNumberCols())]
                wx.CallAfter(self.grid.ForceRefresh)

                row = self.grid.GetGridCursorRow()
                if row < self.grid.GetNumberRows() - 1 and row == self.current_playing_row:
                    self.current_playing_row += 1
                    self.grid.SetGridCursor(self.current_playing_row, 0)
                    self.grid.SelectRow(self.current_playing_row)

            self.grid.MakeCellVisible(self.current_playing_row, 0)
            self.grid.SetFocus()
            self.player_time_update_timer.Stop()

    # -------------------------------------------- Background Music Player --------------------------------------------

    def on_bg_load_files(self, e=None):
        self.bg_tracks_dir = path.make_abs(self.config[Config.BG_TRACKS_DIR], path.fest_file)
        if not self.config[Config.BG_TRACKS_DIR] or not os.path.isdir(self.bg_tracks_dir):
            msg = _("Background MP3 path is invalid. Please specify a\n"
                    "valid path with your background tracks in settings.\n\n"
                    "Found path: %s") % self.config[Config.BG_TRACKS_DIR]
            d = wx.MessageBox(msg, "Path Error", wx.OK | wx.ICON_ERROR, self)
            return

        self.bg_player.load_files(self.bg_tracks_dir)
        self.play_next_bg_item.Enable(True)
        self.play_pause_bg_end_show_item.Enable(True)

    def fade_switched(self, e):
        value = bool(e.Int)
        self.bg_player.fade_in_out = value
        if isinstance(e.EventObject, wx.CheckBox):
            self.bg_fade_switch.Check(value)
        elif isinstance(e.EventObject, wx.Menu) and self.bg_player.window:
            self.bg_player.window.fade_in_out_switch.SetValue(value)

    def background_play(self, e=None, from_grid=False):
        if not self.bg_player.playlist:
            self.bg_player_status = "Forced playlist loading..."
            self.on_bg_load_files()

        if e and isinstance(e.EventObject, wx.Menu):  # From menu - always play next
            self.bg_player.switch_track_async(False)
        else:
            self.bg_player.switch_track_async(from_grid)

    def background_set_pause(self, e=None, paused=None):
        value = bool(e.Int) if e else paused
        self.bg_player.pause_async(value)
        if not e or isinstance(e.EventObject, wx.ToggleButton):
            self.bg_pause_switch.Check(value)
        if self.bg_player.window:
            self.bg_player.window.pause_btn.SetValue(value)

    @property
    def background_volume(self):
        return self.bg_player.player.audio_get_volume()

    @background_volume.setter
    def background_volume(self, value):
        self.bg_player.volume = value
        self.bg_player.player.audio_set_volume(value)
        if self.bg_player.window:
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

        if self.bg_player.window:
            self.bg_player.window.time_slider.SetRange(0, length)
            self.bg_player.window.time_slider.SetValue(pos)
            self.bg_player.window.time_label.SetLabel(time_remaining)
            if seeking_time:
                self.bg_player.window.time_label.SetBackgroundColour(Colors.ROW_PLAYING_NOW)
            else:
                self.bg_player.window.time_label.SetBackgroundColour(
                    wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))
                pass

        player_state = self.bg_player.player.get_state()
        status = '%s Vol:%d Time:%s' % ('Seeking' if seeking_time else self.player_state_parse(player_state),
                                        self.bg_player.player.audio_get_volume(),
                                        time_remaining)

        if 'Fading' not in self.bg_player_status:
            self.bg_player_status = status

        if player_state in range(4, 8):
            self.bg_player_timer.Stop()
            if player_state != vlc.State.Paused and self.bg_player.window:
                self.bg_player.window.time_slider.SetValue(0)
            if player_state == vlc.State.Ended:
                self.background_play()

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
                self.background_set_pause(paused=False)
            else:
                self.background_play()
        else:
            self.background_set_pause(paused=True)
        return play

    def play_pause_bg_end_show(self, e=None):
        bg_started = self.play_pause_bg()
        if bg_started and self.end_show_on_bg.IsChecked():
            self.end_show()

    # -------------------------------------------------- Text Window --------------------------------------------------

    def text_win_show(self, e):
        if e.Selection:
            if Config.C2_DATABASE_PATH not in self.config or not self.config[Config.C2_DATABASE_PATH]:
                self.status(_("No Cosplay2 database in config"))
                return
            db_path = path.make_abs(self.config[Config.C2_DATABASE_PATH], path.fest_file)
            if not os.path.isfile(db_path):
                self.status(_("Cosplay2 database not found"))
                return
            self.text_win = TextWindow(self, _('Text Data'), self.config[Config.TEXT_WIN_FIELDS], self.on_text_win_close)
            self.req_id_field_number = self.text_win.LIST_FIELDS.index('requests.number')  # The № value in Cosplay2
            self.text_win.Show()
            self.text_win.load_db(db_path)
            self.status("Text Window Created")
            self.text_win_full_info.Enable(True)
        else:
            self.on_text_win_close()

    def on_text_win_close(self, e=None):
        if self.text_win:
            if self.text_win.db:
                self.text_win.db.close()
            self.text_win.Destroy()
            self.text_win = None
            self.status("Text Window Destroyed")
            self.text_win_show_item.Check(False)
            self.text_win_full_info.Enable(False)
        else:
            self.status("WARNING: Text Window Not Found")

    def text_win_load(self, req_id):
        item = next((x for x in self.text_win.list if str(x[self.req_id_field_number]) == req_id), None)
        if item:
            self.text_win.load(item)
        else:
            self.logger.log("[Text Window] Item '%s' not found in row %d of 'self.text_win.list'." % (req_id, self.req_id_field_number))
            self.logger.log("\tself.text_win.list:\n%s" % str(self.text_win.list))
            self.text_win.clear(_("Item not found in the database. Watch the log."))

    # -------------------------------------------------- Timecode Window --------------------------------------------------

    def timecode_win_show(self, e):
        if e.Selection:
            self.timecode_win = TimecodeWindow(self, _('Timecode'), self.on_timecode_win_close)
            self.timecode_win.Show()
            self.status("Timecode Window Created")
            self.timecode_win.set_text("timecode")
        else:
            self.on_timecode_win_close()

    def on_timecode_win_close(self, e=None):
        if self.timecode_win:
            self.timecode_win.Destroy()
            self.timecode_win = None
            self.status("Timecode Window Destroyed")
        else:
            self.status("WARNING: Timecode Window Not Found")
        self.timecode_win_show_item.Check(False)

    def set_timecode(self, plain_text='', bold_text=''):
        if self.timecode_win:
            self.timecode_win.set_text(plain_text, bold_text)


if __name__ == "__main__":
    app = wx.App(False if len(sys.argv) > 1 and sys.argv[1] == '-v' else True)
    frame = MainWindow(None, Strings.APP_NAME)
    app.MainLoop()
