# File: tests/test_main.py

import unittest
from ui.main_window import AICompilerMainWindow
from PyQt6.QtWidgets import QApplication

app = QApplication([])  # QApplication must be instantiated

class TestAICompilerMainWindow(unittest.TestCase):
    def setUp(self):
        self.main_window = AICompilerMainWindow()

    def test_code_execution(self):
        """Test that valid code runs and produces output."""
        self.main_window.add_new_tab()
        current_editor = self.main_window.tab_widget.currentWidget()
        current_editor.setPlainText("print('Hello, World!')")
        self.main_window.run_code()

        output = self.main_window.output_text.toPlainText()
        self.assertIn("Hello, World!", output)  # Check that the output is correct

    def test_invalid_code_execution(self):
        """Test that invalid code raises an error."""
        self.main_window.add_new_tab()
        current_editor = self.main_window.tab_widget.currentWidget()
        current_editor.setPlainText("def x ")
        self.main_window.run_code()

        error_output = self.main_window.output_text.toPlainText()
        self.assertIn("SyntaxError", error_output)  # Check for syntax error in output

if __name__ == '__main__':
    unittest.main()
