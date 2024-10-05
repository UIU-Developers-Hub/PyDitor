# File: tests/test_main_window.py

import unittest
import os
from ui.main_window import AICompilerMainWindow
from PyQt6.QtWidgets import QApplication

app = QApplication([])  # QApplication instance

class TestAICompilerMainWindow(unittest.TestCase):
    def setUp(self):
        self.main_window = AICompilerMainWindow()

    def test_save_user_settings(self):
        """Test that user settings are saved correctly."""
        self.main_window.save_user_settings()
        self.assertTrue(os.path.exists(self.main_window.SETTINGS_PATH))

    def test_run_code(self):
        """Test running a basic piece of code."""
        self.main_window.add_new_tab()
        current_editor = self.main_window.tab_widget.currentWidget()
        current_editor.setPlainText("print('Hello, World!')")
        self.main_window.run_code()

        output = self.main_window.output_text.toPlainText()
        self.assertIn("Hello, World!", output)

if __name__ == '__main__':
    unittest.main()
