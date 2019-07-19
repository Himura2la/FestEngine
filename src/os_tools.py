# This file contains OS-level stuff (paths, strings, locale, etc)
# By default, the app uses absolute paths with POSIX notation.
# All path translations are performed on start (change settings, read config, etc)


import os
import sys
from pathlib import Path, PureWindowsPath


class PathTools(object):
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self._work_dir = str(Path(sys._MEIPASS))
        else:
            self._work_dir = str(Path(__file__).resolve().parent)
        self._fest_file = None

    @property
    def work_dir(self):
        return self._work_dir

    @property
    def fest_file(self):
        return self._fest_file

    @fest_file.setter
    def fest_file(self, fest_file):
        self._fest_file = str(Path(fest_file).resolve())

    def make_abs(self, path, anchor=None):
        if not path:
            return path
        path, anchor = self._prepare_paths(path, anchor)
        return str(Path(os.path.join(str(anchor), str(path))).resolve())

    def make_rel(self, path, anchor=None):
        if not path:
            return path
        path, anchor = self._prepare_paths(path, anchor)
        if self._can_make_rel(path, anchor):
            # Path().relative_to() have differ semantic with os.path.relpath()
            return str(os.path.relpath(str(path.resolve()), str(anchor)))
        else:
            return str(path.resolve())

    def _prepare_paths(self, path, anchor):
        path = Path(PureWindowsPath(path).as_posix()) if os.name == 'posix' and '\\' in str(path) else Path(path)
        if anchor is None:
            anchor = Path(self._work_dir)
        else:
            anchor = Path(anchor).resolve()
            if anchor.is_file():
                anchor = anchor.parent
        return path, anchor

    @staticmethod
    def _can_make_rel(path, anchor):
        if not path.exists() or not anchor.exists():
            return False
        if os.lstat(path.resolve().as_posix()).st_dev != os.lstat(anchor.resolve().as_posix()).st_dev:
            return False
        return True

path = PathTools()
