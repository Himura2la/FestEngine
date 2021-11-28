#!python3
# -*- coding: utf-8 -*-

import wx
import wx.richtext


class TimecodeWindow(wx.Frame):
    def __init__(self, parent, title, close_callback):
        self.main_window = parent
        self.base_title = title
        wx.Frame.__init__(self, parent, title=title, size=(260, 110))

        # ---------------------------------------------- Layout -----------------------------------------------------
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.font_size = 24
        self.rtc = wx.richtext.RichTextCtrl(self, style=wx.VSCROLL | wx.NO_BORDER)
        self.rtc.BeginSuppressUndo()
        self.rtc.SetEditable(False)
        main_sizer.Add(self.rtc, 1, wx.EXPAND | wx.TOP, border=1)
        self.SetSizer(main_sizer)
        self.Layout()
        self.Bind(wx.EVT_CLOSE, close_callback)

    def set_text(self, plain_text='', bold_text=''):
        self.rtc.Freeze()
        self.rtc.Clear()
        self.rtc.BeginFontSize(self.font_size)
        if plain_text:
            self.rtc.WriteText(plain_text.lstrip())
        self.rtc.BeginBold()
        if bold_text:
            self.rtc.WriteText(bold_text.rstrip())
        self.rtc.EndBold()
        self.rtc.EndFontSize()
        self.rtc.Thaw()