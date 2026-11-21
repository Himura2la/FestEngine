# -*- coding: utf-8 -*-


class Config:
    LAST_SESSION_PATH = "last_fest.txt"
    PROJECTOR_SCREEN = "Projector Screen"
    FILENAME_RE = "Filename RegEx"
    BG_TRACKS_DIR = "Background Tracks Dir"
    BG_ZAD_PATH = "Background ZAD Path"
    FILES_DIRS = "Files Dirs"
    VLC_ARGUMENTS = "VLC CLI Arguments"
    BG_FADE_STOP_DELAYS = "BG Player Stop Fade In/Out Delays"
    BG_FADE_PAUSE_DELAYS = "BG Player Pause Fade In/Out Delays"
    COUNTDOWN_TIME_FMT = "Countdown Time Format"
    C2_DATABASE_PATH = "Cosplay2 Database Path"
    TEXT_WIN_FIELDS = "Main Fields in Text Window"
    COUNTDOWN_OPENING_TEXT = "Countdown Opening Text"
    COUNTDOWN_INTERMISSION_TEXT = "Countdown Intermission Text"


class Columns:
    NUM = u'№'
    FILES = 'files'
    NOTES = 'notes'
    NAME = 'name'
    C2_REQUEST_ID = 'req_id'


class Strings:
    APP_NAME = "Fest Engine"
    COUNTDOWN_ROW_TEXT_FULL = "break"
    COUNTDOWN_ROW_TEXT_SHORT = "brk"


class Colors:
    COUNTDOWN_TEXT_COLOR = (255, 255, 255)  # White


class FileTypes:
    video_extensions = {'avi', 'mp4', 'm4v', 'mov', 'wmv', 'mkv', 'm3u'}
    audio_extensions = {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac', 'wma'}
    img_extensions = {'jpeg', 'png', 'jpg', 'zad.mp4'}


class wxWidgetsConstants:
    # https://github.com/wxWidgets/wxWidgets/blob/master/include/wx/image.h#L463
    wxImageLoad_Verbose = 1