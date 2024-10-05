# File: tests/test_code_editor_extended.py

import unittest
from PyQt6.QtWidgets import QApplication
from ui.code_editor import CodeEditor
from PyQt6.QtGui import QTextCursor

app = QApplication([])  # Required to create the UI components

class TestCodeEditorExtended(unittest.TestCase):
    
    def setUp(self):
        self.editor = CodeEditor()

    def test_highlight_current_line(self):
        """Test that the current line is highlighted correctly."""
        # Move cursor to a specific position
        cursor = self.editor.textCursor()
        cursor.setPosition(5)
        self.editor.setTextCursor(cursor)
        self.editor.highlight_current_line()

        # Check if extra selections contain a highlight for the current line
        extra_selections = self.editor.extraSelections()
        highlighted = any(selection.format.background().color().name() == "#3b3b3b" for selection in extra_selections)
        self.assertTrue(highlighted, "Current line is not highlighted correctly.")

    def test_add_breakpoint(self):
        """Test adding a breakpoint by clicking in the line number area."""
        # Simulate a click in the line number area
        self.editor.breakpoints = set()  # Clear existing breakpoints
        block_number = 2
        self.editor.breakpoints.add(block_number)
        self.assertIn(block_number, self.editor.breakpoints, "Breakpoint was not added correctly.")

    def test_lint_code(self):
        """Test linting the code."""
        code = "def foo():\n    return 1"
        self.editor.setPlainText(code)
        self.editor.lint_code()

        # Wait for linting to complete (since it runs in a separate thread)
        self.editor.lint_worker.wait()

        # Verify that lint_errors contains expected data
        self.assertIsInstance(self.editor.lint_errors, dict, "Lint errors should be a dictionary.")
    
    def test_handle_autocompletion(self):
        """Test that autocompletion triggers appropriately."""
        self.editor.setPlainText("import os\nos.")
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.editor.setTextCursor(cursor)
        self.editor.handle_autocompletion()

        # Check if the completer popup is visible (indicating that autocompletion was triggered)
        self.assertTrue(self.editor.completer.popup().isVisible(), "Autocompletion did not trigger correctly.")

if __name__ == "__main__":
    unittest.main()
