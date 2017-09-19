import wx
import wx.grid


class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, title=title)
        colors = [
            ['wx.SYS_COLOUR_SCROLLBAR', 'The scrollbar grey area.'],
            ['wx.SYS_COLOUR_DESKTOP', 'The desktop colour.'],
            ['wx.SYS_COLOUR_ACTIVECAPTION', 'Active window caption colour.'],
            ['wx.SYS_COLOUR_INACTIVECAPTION', 'Inactive window caption colour.'],
            ['wx.SYS_COLOUR_MENU', 'Menu background colour.'],
            ['wx.SYS_COLOUR_WINDOW', 'Window background colour.'],
            ['wx.SYS_COLOUR_WINDOWFRAME', 'Window frame colour.'],
            ['wx.SYS_COLOUR_MENUTEXT', 'Colour of the text used in the menus.'],
            ['wx.SYS_COLOUR_WINDOWTEXT', 'Colour of the text used in generic windows.'],
            ['wx.SYS_COLOUR_CAPTIONTEXT', 'Colour of the text used in captions, size boxes and scrollbar arrow boxes.'],
            ['wx.SYS_COLOUR_ACTIVEBORDER', 'Active window border colour.'],
            ['wx.SYS_COLOUR_INACTIVEBORDER', 'Inactive window border colour.'],
            ['wx.SYS_COLOUR_APPWORKSPACE', 'Background colour for MDI applications.'],
            ['wx.SYS_COLOUR_HIGHLIGHT', 'Colour of item(s) selected in a control.'],
            ['wx.SYS_COLOUR_HIGHLIGHTTEXT', 'Colour of the text of item(s) selected in a control.'],
            ['wx.SYS_COLOUR_BTNFACE', 'Face shading colour on push buttons.'],
            ['wx.SYS_COLOUR_BTNSHADOW', 'Edge shading colour on push buttons.'],
            ['wx.SYS_COLOUR_GRAYTEXT', 'Colour of greyed (disabled) text.'],
            ['wx.SYS_COLOUR_BTNTEXT', 'Colour of the text on push buttons.'],
            ['wx.SYS_COLOUR_INACTIVECAPTIONTEXT', 'Colour of the text in active captions.'],
            ['wx.SYS_COLOUR_BTNHIGHLIGHT', 'Highlight colour for buttons.'],
            ['wx.SYS_COLOUR_3DDKSHADOW', 'Dark shadow colour for three-dimensional display elements.'],
            ['wx.SYS_COLOUR_3DLIGHT', 'Light colour for three-dimensional display elements.'],
            ['wx.SYS_COLOUR_INFOTEXT', 'Text colour for tooltip controls.'],
            ['wx.SYS_COLOUR_INFOBK', 'Background colour for tooltip controls.'],
            ['wx.SYS_COLOUR_LISTBOX', 'Background colour for list-like controls.'],
            ['wx.SYS_COLOUR_HOTLIGHT', 'Colour for a hyperlink or hot-tracked item.'],
            ['wx.SYS_COLOUR_GRADIENTACTIVECAPTION', 'Right side colour in the color gradient of an active window\'s title bar.'],
            ['wx.SYS_COLOUR_GRADIENTINACTIVECAPTION', 'Right side colour in the color gradient of an inactive window\'s title bar.'],
            ['wx.SYS_COLOUR_MENUHILIGHT', 'The colour used to highlight menu items when the menu appears as a flat menu.'],
            ['wx.SYS_COLOUR_MENUBAR', 'The background colour for the menu bar when menus appear as flat menus.'],
            ['wx.SYS_COLOUR_LISTBOXTEXT', 'Text colour for list-like controls.'],
            ['wx.SYS_COLOUR_LISTBOXHIGHLIGHTTEXT', 'Text colour for the unfocused selection of list-like controls.'],
            ['wx.SYS_COLOUR_BACKGROUND', 'Synonym for SYS_COLOUR_DESKTOP .'],
            ['wx.SYS_COLOUR_3DFACE', 'Synonym for SYS_COLOUR_BTNFACE .'],
            ['wx.SYS_COLOUR_3DSHADOW', 'Synonym for SYS_COLOUR_BTNSHADOW .'],
            ['wx.SYS_COLOUR_BTNHILIGHT', 'Synonym for SYS_COLOUR_BTNHIGHLIGHT .'],
            ['wx.SYS_COLOUR_3DHIGHLIGHT', 'Synonym for SYS_COLOUR_BTNHIGHLIGHT .'],
            ['wx.SYS_COLOUR_3DHILIGHT', 'Synonym for SYS_COLOUR_BTNHIGHLIGHT .'],
            ['wx.SYS_COLOUR_FRAMEBK', 'Synonym for SYS_COLOUR_BTNFACE .']
        ]

        grid = wx.grid.Grid(self)
        grid.CreateGrid(len(colors), 4)

        for row in range(len(colors)):
            name, desc = colors[row]
            color = wx.SystemSettings.GetColour(eval(name))
            grid.SetCellValue(row, 0, str(color))
            grid.SetCellBackgroundColour(row, 1, color)
            grid.SetCellValue(row, 2, name)
            grid.SetCellValue(row, 3, desc)

        grid.AutoSizeColumns()



        # Top level
        top_sizer = wx.BoxSizer(wx.VERTICAL)
        top_sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizerAndFit(top_sizer)
        self.Fit()
        self.Show(True)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame(None, 'wx.SystemColour Test')
    app.MainLoop()
