#!python3
# -*- coding: utf-8 -*-

import wx
import wx.grid
import sqlite3


class TextWindow(wx.Frame):
    def __init__(self, parent, db_path):
        self.parent = parent
        wx.Frame.__init__(self, parent, title='Text Window', size=(800, 400))
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_FRAMEBK))

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.grid = wx.grid.Grid(self)
        self.columns = ['Section', 'Key', 'Value']
        self.grid.CreateGrid(0, len(self.columns))
        [self.grid.SetColLabelValue(i, v) for i, v in enumerate(self.columns)]
        self.grid.DisableDragRowSize()
        self.grid.SetRowLabelSize(20)
        self.grid.SetColLabelSize(20)
        self.grid.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)

        main_sizer.Add(self.grid, 1, wx.EXPAND | wx.TOP, border=1)

        self.SetSizer(main_sizer)
        self.Layout()

        # --- DB ---

        self.db = sqlite3.connect(db_path, isolation_level=None)
        self.c = self.db.cursor()

        self.c.execute('PRAGMA encoding = "UTF-8"')
        self.c.execute("SELECT value FROM settings WHERE key = 'subdomain'")
        self.event_name = self.c.fetchone()[0]
        self.SetLabel("%s: %s" % (self.GetLabel(), self.event_name))

        self.list = self.get_list()

        self.show_details(self.list[30][0])

    def get_list(self):
        self.c.execute("""
            SELECT requests.id, number, list.card_code, voting_number, voting_title
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

    def show_details(self, request_id):
        data = self._get_details(request_id)
        self.grid_set_rows(len(data))

        def set_row(row_number, row_data):
            request_section_id, section_title, title, value, data_type = row_data
            self.grid.SetCellValue(row_number, self.columns.index('Section'), str(section_title))
            self.grid.SetCellValue(row_number, self.columns.index('Key'), str(title))
            self.grid.SetCellValue(row_number, self.columns.index('Value'), str(value))
        [set_row(i, val) for i, val in enumerate(data)]

if __name__ == "__main__":
    app = wx.App()
    frame = TextWindow(None, "D:\Fests Local\Past\Yuki no Odori 2016\\2016-fest\C2D\\tulafest\sqlite3_data.db")
    frame.Show(True)
    app.MainLoop()
