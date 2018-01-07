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


class Columns:
    NUM = u'№'
    FILES = 'files'
    NOTES = 'notes'
    NAME = 'name'


class Strings:
    APP_NAME = "Fest Engine"
    COUNTDOWN_FIRST_TEXT = "До начала фестиваля"
    COUNTDOWN_DEFAULT_TEXT = "До конца перерыва"
    COUNTDOWN_ROW_TEXT_FULL = "break"
    COUNTDOWN_ROW_TEXT_SHORT = "brk"


class Colors:
    DUP_ROW = (255, 128, 255, 255)
    COUNTDOWN_ROW = (128, 255, 128, 255)
    FILTERED_GRID = (255, 255, 128, 255)

    BG_NEVER_PLAYED = (255, 255, 255, 255)
    BG_PLAYING_NOW = DUP_ROW
    BG_PLAYED_TO_END = FILTERED_GRID
    BG_SKIPPED = (255, 128, 128, 255)

    COUNTDOWN_TEXT_COLOR = (255, 255, 255, 255)


class FileTypes:
    video_extensions = {'avi', 'mp4', 'mov', 'wmv', 'mkv'}
    audio_extensions = {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac'}
    img_extensions = {'jpeg', 'png', 'jpg'}
