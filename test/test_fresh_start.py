import unittest

import time
from pywinauto.application import Application
import os
import glob

sample_fest_path = r"..\..\test\data\sample.fest"
items_number = 3


class FreshStartTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FreshStartTests, self).__init__(*args, **kwargs)

        os.chdir(os.path.join(os.path.split(__file__)[0], "..", "bin", "FestEngine"))
        self.assertTrue(os.path.isfile("FestEngine.exe"), "No build")
        self.assertTrue(os.path.isfile(sample_fest_path), "No test data")

    def setUp(self):
        if os.path.isfile("last_fest.txt"):
            os.remove("last_fest.txt")

    def test_load_session(self):
        app = Application().start("FestEngine.exe")

        app['Welcome to Fest Engine'].OK.click()

        settings = app.Settings
        settings['Current Fest:Edit'].set_text(os.path.abspath(sample_fest_path))
        time.sleep(0.5)
        settings.Load.click()

        app['Restart Required'].NoButton.click()
        app.wxWindowNR.menu_select("Main -> Exit")

        app.wait_for_process_exit(1)

        app = Application().start("FestEngine.exe")
        main_window = app.wxWindowNR

        self.assertTrue(main_window.GridWindow.exists())
        self.assertTrue('Loaded %d items' % items_number in main_window.StatusBar.texts())

        main_window.menu_select("Main -> Show Log")
        time.sleep(0.5)
        log_text = app["FestEngine Log"].Edit.text_block()
        self.assertTrue(log_text.strip() == "Init", "Errors in log:")

        main_window.close()

    def tearDown(self):
        self.setUp()  # Remove last_fest.txt in the end.
        for backup in glob.glob(r"..\..\test\data\*.bkp.fest"):
            os.remove(backup)


if __name__ == '__main__':
    unittest.main()
