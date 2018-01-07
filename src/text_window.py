#!python3
# -*- coding: utf-8 -*-

import wx
import wx.grid
import sqlite3

from constants import Colors


class TextWindow(wx.Frame):
    def __init__(self, parent, title, main_fields):
        self.parent = parent
        self.base_title = title
        self.main_fields = main_fields
        wx.Frame.__init__(self, parent, title=title, size=(1024, 768))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.default_name = "Please wait..."
        self.current_name = self.default_name

        label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label = wx.StaticText(self, style=wx.ALIGN_CENTER_HORIZONTAL, label=self.current_name)
        font = self.label.GetFont()
        font.SetPixelSize(wx.Size(0, 28))
        self.label.SetFont(font)

        label_sizer.AddStretchSpacer()
        label_sizer.Add(self.label, 0, wx.EXPAND)
        label_sizer.AddStretchSpacer()
        main_sizer.Add(label_sizer, 0, wx.EXPAND)

        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(0, 0)
        self.grid.SetColLabelSize(24)
        self.grid.HideRowLabels()
        self.grid.HideColLabels()
        self.grid.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())
        self.grid.SetDefaultEditor(wx.grid.GridCellAutoWrapStringEditor())
        font = self.grid.GetDefaultCellFont()
        font.SetPixelSize(wx.Size(0, 18))
        self.grid.SetDefaultCellFont(font)

        main_sizer.Add(self.grid, 1, wx.EXPAND | wx.TOP, border=1)

        self.SetSizer(main_sizer)
        self.Layout()

        self.grid.Bind(wx.EVT_SIZE, self.grid_autosize_cols)
        self.grid_autosize_cols()

        self.show_full_info = False
        self.show_values_only = False
        self.event_name = ""
        self.list = None
        self.db = None
        self.c = None

        self.Bind(wx.EVT_CLOSE, parent.on_text_win_close)

    def load_db(self, db_path):
        self.db = sqlite3.connect(db_path, isolation_level=None)
        self.c = self.db.cursor()

        self.c.execute('PRAGMA encoding = "UTF-8"')
        self.c.execute("SELECT value FROM settings WHERE key = 'subdomain'")
        self.event_name = self.c.fetchone()[0]

        self.SetLabel("%s: %s" % (self.base_title, self.event_name))

        self.list = self.get_list()

    def grid_autosize_cols(self, e=None):
        w = self.grid.GetClientSize()[0] - self.grid.GetRowLabelSize()
        col_sizes = [self.grid.GetColSize(i) for i in range(self.grid.GetNumberCols())] if e else [1, 2]
        n_cols = self.grid.GetNumberCols()
        for col in range(n_cols):
            k = w / sum(col_sizes)
            self.grid.SetColSize(col, col_sizes[col] * k)
        if e:
            e.Skip()

    def get_list(self):
        self.c.execute("""
            SELECT requests.id, number, title, list.card_code, voting_number, voting_title
            FROM   list, requests 
            WHERE  list.id = topic_id AND list.default_duration > 0
        """)
        return self.c.fetchall()

    def _get_details(self, request_id):
        self.c.execute("""
            SELECT request_section_id, section_title, title, value, type
            FROM   [values]
            WHERE  request_id = ?
        """, (request_id,))
        return self.c.fetchall()

    def grid_set_shape(self, new_rows=-1, new_cols=-1):
        current_rows, current_cols = self.grid.GetNumberRows(), self.grid.GetNumberCols()
        if 0 <= new_rows < current_rows:
            self.grid.DeleteRows(0, current_rows - new_rows, False)
        elif new_rows > current_rows:
            self.grid.AppendRows(new_rows - current_rows)

        if 0 <= new_cols < current_cols:
            self.grid.DeleteCols(0, current_cols - new_cols, False)
        elif new_cols > current_cols:
            self.grid.AppendCols(new_cols - current_cols)

    def load_item(self, list_item):
        data = self._get_details(list_item[0])
        if not self.show_full_info:
            data = list(filter(lambda r: r[2] in self.main_fields, data))

        self.grid_set_shape(len(data), 1 if self.show_values_only else 2)

        section_i = 1
        request_section_id = -1

        for row_number, row_data in enumerate(data):
            prev_section = request_section_id
            request_section_id, section_title, title, value, data_type = row_data
            if self.show_values_only:
                self.grid.SetCellValue(row_number, 0, str(value))
            else:
                self.grid.SetCellValue(row_number, 0, "[%s]\n%s" % (section_title, title))
                self.grid.SetCellValue(row_number, 1, str(value))
                color = self.grid.GetDefaultCellBackgroundColour() if section_i % 2 \
                                                                   else Colors.BG_TXT_WIN_CAT_ALTERNATION
                self.grid.SetCellBackgroundColour(row_number, 0, color)
                self.grid.SetCellBackgroundColour(row_number, 1, color)
                if prev_section != request_section_id:
                    section_i += 1
            if self.show_full_info:
                self.grid.AutoSizeRow(row_number)
            else:
                self.grid.SetRowSize(row_number, self.grid.GetClientSize()[1] - 70)

        self.current_name = "%s: %s %s. %s" % list_item[2:6]
        self.label.SetLabel(self.current_name)
        self.Layout()

    def clear(self, message=None):
        self.current_name = message if message else self.default_name
        self.label.SetLabel(self.current_name)
        self.grid_set_shape(0)
        self.Layout()
