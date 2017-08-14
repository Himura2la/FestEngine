
class Config:
    PROJECTOR_SCREEN = "Projector Screen"


class Columns:
    ID = 'ID'
    FILES = 'files'
    NOTES = 'notes'


class Colors:
    DUP_ROW = (255, 128, 255, 255)
    FILTERED_GRID = (255, 255, 128, 255)

    BG_NEVER_PLAYED = (255, 255, 255, 255)
    BG_PLAYING_NOW = DUP_ROW
    BG_PLAYED_TO_END = FILTERED_GRID
    BG_SKIPPED = (255, 128, 128, 255)


class FileTypes:
    # TODO: Move this to settings
    video_extensions = {'mp4', 'avi', 'wmv'}
    sound_extensions = {'mp3', 'wav'}
