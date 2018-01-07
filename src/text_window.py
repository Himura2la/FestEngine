#!python3
# -*- coding: utf-8 -*-

import wx
import wx.grid
import sqlite3


class TextWindow(wx.Frame):
    def __init__(self, parent, title, db_path):
        self.parent = parent
        self.base_title = title
        wx.Frame.__init__(self, parent, title=title, size=(800, 400))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        label_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label = wx.StaticText(self, style=wx.ALIGN_CENTER_HORIZONTAL)
        font = self.label.GetFont()
        font.SetPixelSize(wx.Size(0, 25))
        self.label.SetFont(font)

        label_sizer.Add(self.label, 1, wx.EXPAND)
        main_sizer.Add(label_sizer, 0, wx.EXPAND)

        self.grid = wx.grid.Grid(self)
        self.columns = ['Section', 'Key', 'Value']
        self.grid.CreateGrid(0, len(self.columns))
        [self.grid.SetColLabelValue(i, v) for i, v in enumerate(self.columns)]
        self.grid.SetRowLabelSize(20)
        self.grid.SetColLabelSize(20)
        self.grid.SetDefaultRenderer(wx.grid.GridCellAutoWrapStringRenderer())

        main_sizer.Add(self.grid, 1, wx.EXPAND | wx.TOP, border=1)

        self.SetSizer(main_sizer)
        self.Layout()

        self.grid.Bind(wx.EVT_SIZE, self.grid_autosize_cols)
        self.grid_autosize_cols()

        # --- DB ---

        self.db = sqlite3.connect(db_path, isolation_level=None)
        self.c = self.db.cursor()

        self.c.execute('PRAGMA encoding = "UTF-8"')
        self.c.execute("SELECT value FROM settings WHERE key = 'subdomain'")
        self.event_name = self.c.fetchone()[0]

        self.SetLabel("%s: %s" % (self.base_title, self.event_name))

        self.list = self.get_list()
        self.current_name = ""

        self.show_details(self.list[30])

    def grid_autosize_cols(self, e=None):
        w = self.grid.GetClientSize()[0] - self.grid.GetRowLabelSize()
        col_sizes = [self.grid.GetColSize(i) for i in range(self.grid.GetNumberCols())] if e else [1, 1, 2]
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

    def grid_set_rows(self, new_rows):
        current_rows = self.grid.GetNumberRows()
        if current_rows > 0:
            self.grid.DeleteRows(0, current_rows, False)
        self.grid.AppendRows(new_rows)

    def show_details(self, list_item):
        data = self._get_details(list_item[0])
        self.grid_set_rows(len(data))

        def set_row(row_number, row_data):
            request_section_id, section_title, title, value, data_type = row_data
            self.grid.SetCellValue(row_number, self.columns.index('Section'), str(section_title))
            self.grid.SetCellValue(row_number, self.columns.index('Key'), str(title))
            self.grid.SetCellValue(row_number, self.columns.index('Value'), str(value))
            self.grid.AutoSizeRow(row_number)
            self.grid.SetRowSize(row_number, self.grid.GetRowSize(row_number) - 10)
        [set_row(i, val) for i, val in enumerate(data)]

        self.current_name = "%s: %s %s. %s" % list_item[2:6]
        self.label.SetLabel(self.current_name)


if __name__ == "__main__":
    app = wx.App()
    frame = TextWindow(None, 'Text Window (Debug)', "D:\Fests Local\Past\Yuki no Odori 2016\\2016-fest\C2D\\tulafest\sqlite3_data.db")
    frame.Show(True)
    app.MainLoop()
