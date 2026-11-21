import wx


class LightGridColors:
    DUP_ROW = (128, 255, 255)
    COUNTDOWN_ROW = (128, 255, 200)
    FILTERED_GRID = (255, 255, 200)
    ROW_PLAYING_NOW = (200, 200, 255)
    ROW_PLAYED_TO_END = (200, 200, 200)
    ROW_SKIPPED = (255, 200, 200)


class DarkGridColors:
    DUP_ROW = (20, 91, 103)
    COUNTDOWN_ROW = (36, 89, 58)
    FILTERED_GRID = (93, 77, 27)
    ROW_PLAYING_NOW = (56, 69, 120)
    ROW_PLAYED_TO_END = (77, 77, 77)
    ROW_SKIPPED = (115, 52, 59)


def grid_colors_for_theme(settings=wx.SystemSettings):
    """Select once after wx.App starts; older wx versions lack appearance APIs."""
    try:
        dark = settings.GetAppearance().IsDark()
    except AttributeError:
        bg = settings.GetColour(wx.SYS_COLOUR_WINDOW)
        dark = (299 * bg.Red() + 587 * bg.Green() + 114 * bg.Blue()) < 128000
    return DarkGridColors if dark else LightGridColors