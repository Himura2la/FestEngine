import unittest

# Ugly hack to allow absolute import from the root folder
import sys, os

sys.path.insert(0, os.path.abspath('../..'))

from src.os_tools import path as t
import pathlib as path


def delete_folder(pth):
    for sub in pth.iterdir():
        if sub.is_dir():
            delete_folder(sub)
        else:
            sub.unlink()
    pth.rmdir()


class OsToolsTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(OsToolsTests, self).__init__(*args, **kwargs)

    def setUp(self):
        self.work_dir = path.Path('.')
        self.test_dir = path.Path('phantom')
        if self.test_dir.exists():
            delete_folder(self.test_dir)

        self.test_dir.mkdir()
        self.sub_dir = path.Path('phantom/sub_dir')
        self.sub_dir.mkdir()

        self.fest1_path = path.Path('phantom/test1.fest')
        self.fest1_path.touch()
        self.fest2_path = path.Path('phantom/sub_dir/test2.fest')
        self.fest2_path.touch()

    # TODO check default values (need stable workdir path)

    def test_fest_file_set(self):
        t.fest_file = self.fest1_path
        print(t.fest_file)
        self.assertEqual(t.fest_file, str(self.fest1_path.resolve()))

    def test_relative_path(self):
        # Downstream relative path
        t.fest_file = self.fest1_path
        self.assertEqual(t.make_rel(self.fest2_path, t.fest_file), "sub_dir\\test2.fest")
        # Upstream relative path
        t.fest_file = self.fest2_path
        self.assertEqual(t.make_rel(self.fest1_path, t.fest_file), "..\\test1.fest")
        # TODO test workdir relative path (need stable workdir path)

        # Test empty path
        self.assertEqual(t.make_rel(""), "")

    # TODO test abs paths (need stable enviroment)

    def tearDown(self):
        self.fest2_path.unlink()
        self.fest1_path.unlink()
        self.sub_dir.rmdir()
        self.test_dir.rmdir()


if __name__ == '__main__':
    unittest.main()
