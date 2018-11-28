# This file contains function for work witch OS (paths, strings, locale, etc)

# By default in app using absolute path with posix notation. All translations making in entry points (change settings,
# read config, etc)


import os
import sys
from pathlib import Path, PureWindowsPath


def __get_work_dir():
    if 'work_dir' not in __get_work_dir.__dict__:
        __get_work_dir.work_dir = ''

    if __get_work_dir.work_dir == '':
        if getattr(sys, 'frozen', False):
            work_dir = sys._MEIPASS
        else:
            work_dir = Path(__file__).resolve().parent
    return Path(work_dir)


def __get_fest_file_path(fest_file_path=None):
    if 'fest_file_path' not in __get_fest_file_path.__dict__:
        __get_fest_file_path.fest_file_path = ''

    if __get_fest_file_path.fest_file_path == '':
        if fest_file_path == None:
            return __get_work_dir()
        else:
            __get_fest_file_path.fest_file_path = fest_file_path
    return Path(__get_fest_file_path.fest_file_path)


def __tool_get_work_dir():
    if getattr(sys, 'frozen', False):
        work_dir = sys._MEIPASS
    else:
        work_dir = Path(__file__).resolve().parent
    return  Path(work_dir)


def __tool_make_canon_path(path, anchor_path = None):
    # If path was created on windows it may contain \ character. On linux os it make some problems
    if os.name == 'posix' and '\\' in str(path):
        path = Path(PureWindowsPath(path).as_posix())
    if os.name == 'posix' and anchor_path != None and '\\' in str(anchor_path):
        anchor_path = Path(PureWindowsPath(anchor_path).as_posix())

    internal_path = Path(path)
    try:
        if anchor_path == None:
            anchor_path = Path('.').resolve()
        else:
            if anchor_path.is_file():
                anchor_path = anchor_path.parent
            anchor_path = Path(anchor_path).resolve()
    except FileNotFoundError:
        print('Fail to make canon path %d because anchor path %s is not found' % (path, anchor_path))
        return internal_path

    try:
        if internal_path.is_absolute():
            p = internal_path.resolve()
        else:
            p = Path(os.path.join(str(anchor_path), str(internal_path))).resolve()
    except FileNotFoundError:
        print('Fail to make canon path %s because is not found' % (internal_path))
        return internal_path
    return p


def __tool_make_rel_path(path, anchor_path=None):
    # If path was created on windows it may contain \ character. On linux os it make some problems
    if os.name == 'posix' and '\\' in str(path):
        path = Path(PureWindowsPath(path).as_posix())
    else:
        path = Path(path)
    if anchor_path != None:
        anchor_path = __tool_make_canon_path(anchor_path)

    try:
        file_state = os.lstat(path.resolve().as_posix())
    except FileNotFoundError:
        # Target path not found
        print('Fail to make rel path %s because is not found' % (path))
        return path

    if anchor_path is None:
        work_dir = __tool_get_work_dir()
        path_from_location = os.lstat(work_dir)
    else:
        if anchor_path.is_file():
            anchor_path = anchor_path.parent
        try:
            path_from_location = os.lstat(str(anchor_path))
        except FileNotFoundError:
            anchor_path = __get_work_dir()
            path_from_location = os.lstat(str(anchor_path))

    if file_state.st_dev != path_from_location.st_dev:
        return path.resolve()
    else:
        # Path().relative_to() have differ semantic with os.path.relpath()
        return Path(os.path.relpath(str(path.resolve()), str(anchor_path)))


def tool_path_from_fest_file(path, fest_file_path=None):
    if path == "": return path
    fest_file = __get_fest_file_path(fest_file_path)
    return str(__tool_make_rel_path(path, fest_file))


def tool_path_from_workdir(path):
    if path == "": return path
    work_dir = __get_work_dir()
    return str(__tool_make_rel_path(path, work_dir))


def tool_abs_path_from_fest_file(path, fest_file_path=None):
    if path == "": return path
    fest_file = __get_fest_file_path(fest_file_path)
    return str(__tool_make_canon_path(path, fest_file))


def tool_abs_path_from_workdir(path):
    if path == "" : return path
    work_dir = __get_work_dir()
    return str(__tool_make_canon_path(path, work_dir))


def tool_fest_file_set(fest_file_path):
    __get_fest_file_path(fest_file_path)


#If fest file is not set work dir will be returned
def tool_fest_file_get():
    return __get_fest_file_path()


def tool_work_dir_get():
    return __get_work_dir()
