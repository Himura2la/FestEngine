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
    DUP_ROW = (128, 255, 255)  # Sky
    COUNTDOWN_ROW = (128, 255, 200)  # Green
    FILTERED_GRID = (255, 255, 200)  # Yellow

    ROW_PLAYING_NOW = (200, 200, 255)  # Blue
    ROW_PLAYED_TO_END = (200, 200, 200)  # Gray
    ROW_SKIPPED = (255, 200, 200)  # Red

    COUNTDOWN_TEXT_COLOR = (255, 255, 255)  # White


class FileTypes:
    video_extensions = {'avi', 'mp4', 'mov', 'wmv', 'mkv', 'm3u'}
    audio_extensions = {'mp3', 'wav', 'flac', 'ogg', 'm4a', 'aac'}
    img_extensions = {'jpeg', 'png', 'jpg'}
