# This file contains function for work witch OS (paths, strings, locale, etc)

# By default in app using absolute path with posix notation. All translations making in entry points (change settings,
# read config, etc)


import os
import sys
from pathlib import Path, PureWindowsPath

class PathTools:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.work_dir = sys._MEIPASS
        else:
            self.work_dir = Path(__file__).resolve().parent
        self.fest_file = None

    def get_work_dir(self):
        return str(self.work_dir)

    def set_fest_file(self, fest_file):
        self.fest_file = Path(fest_file).resolve()

    def get_fest_file(self):
        return str(self.fest_file)

    def make_path_abs(self, path, anchor=None):
        path, anchor = self._prepare_paths(path, anchor)
        return str(Path(os.path.join(str(anchor), str(path))).resolve())

    def make_path_rel(self, path, anchor=None):
        path, anchor = self._prepare_paths(path, anchor)

        if self._can_make_rel(path, anchor):
            # Path().relative_to() have differ semantic with os.path.relpath()
            return str(os.path.relpath(str(path.resolve()), str(anchor)))
        else:
            return str(path.resolve())

    def _prepare_paths(self, path, anchor):
        if os.name == 'posix' and '\\' in str(path):
            path = Path(PureWindowsPath(path).as_posix())

        if anchor is None:
            anchor = self.work_dir
        else:
            anchor = Path(anchor).resolve()
            if anchor.is_file():
                anchor = anchor.parent

        path = Path(path)
        return (path, anchor)

    def _can_make_rel(self, path, anchor):
        if not path.exists() or not anchor.exists():
            return False

        if os.lstat(path.resolve().as_posix()).st_dev != os.lstat(anchor.resolve().as_posix()).st_dev:
            return False;

        return True

path_tool = PathTools()