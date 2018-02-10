#!python3
# -*- coding: utf-8 -*-

import wx
import wx.richtext
import sqlite3


class TextWindow(wx.Frame):
    def __init__(self, parent, title, main_fields):
        self.parent = parent
        self.base_title = title
        self.main_fields = main_fields
        wx.Frame.__init__(self, parent, title=title, size=(800, 400))

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.title_font_size = 21
        self.text_font_size = 18

        self.current_title = ""

        self.rtc = wx.richtext.RichTextCtrl(self, style=wx.VSCROLL | wx.NO_BORDER)
        self.rtc.BeginSuppressUndo()

        main_sizer.Add(self.rtc, 1, wx.EXPAND | wx.TOP, border=1)

        self.SetSizer(main_sizer)
        self.Layout()
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

    def get_list(self):
        self.c.execute("""
            SELECT requests.id, number, title, list.card_code, voting_number, voting_title
            FROM   list, requests
            WHERE  list.id = topic_id AND list.default_duration > 0
        """)
        return self.c.fetchall()

    def _get_details(self, request_id):
        base_query = "SELECT request_section_id, section_title, title, value, type FROM [values] "
        if self.show_full_info:
            self.c.execute(base_query + "WHERE request_id = ?", (request_id,))
        else:
            fields_list = "(%s)" % ",".join(['?' for _ in self.main_fields])

            self.c.execute(base_query + "WHERE request_id = ? AND title IN " + fields_list,
                           ([request_id] + self.main_fields))
        return self.c.fetchall()

    def load_item(self, list_item):
        data = self._get_details(list_item[0])

        section_i = 1
        request_section_id = -1

        self.rtc.Freeze()
        self.rtc.Clear()

        nom = list_item[2]
        title = "%s %s. %s" % list_item[3:6]
        self.current_title = "%s: %s" % (nom, title)

        self.rtc.BeginFontSize(self.title_font_size)
        self.rtc.BeginBold()

        self.rtc.WriteText(nom)
        self.rtc.Newline()
        self.rtc.WriteText(title)

        self.rtc.EndBold()
        self.rtc.EndFontSize()
        self.rtc.Newline()

        self.rtc.BeginFontSize(self.text_font_size)
        self.rtc.Newline()

        for row_number, row_data in enumerate(data):
            prev_section = request_section_id
            request_section_id, section_title, title, value, data_type = row_data
            value_text = str(value)

            if not value_text:
                continue

            self.rtc.BeginBold()

            if self.show_full_info and prev_section != request_section_id:
                if self.rtc.NumberOfLines > 4:
                    self.rtc.Newline()
                self.rtc.WriteText("--- %s [%d] ---" % (section_title, request_section_id))
                self.rtc.Newline()
            self.rtc.WriteText("%s: " % title)
            self.rtc.EndBold()

            if len(value_text) > 50:
                self.rtc.Newline()

            self.rtc.WriteText(value_text)
            self.rtc.Newline()

        self.rtc.EndFontSize()
        self.rtc.Thaw()

    def clear(self, message=None):
        self.rtc.Clear()
        if message:
            self.rtc.BeginFontSize(self.title_font_size)
            self.rtc.WriteText(message)
            self.rtc.EndFontSize()
