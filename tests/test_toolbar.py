import unittest
from ui.main_window import AICompilerMainWindow
from PyQt6.QtWidgets import QApplication

app = QApplication([])

class TestToolbar(unittest.TestCase):

    def setUp(self):
        self.main_window = AICompilerMainWindow()
        self.toolbar = self.main_window.toolbar

    def test_toolbar_buttons(self):
        self.assertTrue(self.toolbar.actions(), "Toolbar has no actions")

    def test_run_code_button(self):
        action = next(action for action in self.toolbar.actions() if action.text() == "Run Code")
        self.assertEqual(action.shortcut().toString(), "Ctrl+R", "Shortcut for Run Code is incorrect")

if __name__ == "__main__":
    unittest.main()
