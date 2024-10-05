# File: tests/test_code_editor.py

import unittest
import os
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QEvent, Qt, QResizeEvent
from PyQt6.QtGui import QKeyEvent
from ui.code_editor import CodeEditor, LintWorker

# QApplication instance required to run PyQt tests
app = QApplication([])

class TestCodeEditor(unittest.TestCase):

    def setUp(self):
        """Set up the environment for each test."""
        self.editor = CodeEditor()
        self.editor.show()

    def tearDown(self):
        """Clean up after each test."""
        self.editor.close()
        if os.path.exists("test_save_file.py"):
            os.remove("test_save_file.py")

    def test_save_file(self):
        """Test saving file content."""
        # Implementing save_file method in CodeEditor for testing purposes
        self.editor.setPlainText("print('Hello, World!')")
        with patch('PyQt6.QtWidgets.QFileDialog.getSaveFileName', return_value=("test_save_file.py", "")):
            self.editor.save_file()  # Assumes CodeEditor has a save_file method implemented

        # Check if the file was created
        self.assertTrue(os.path.exists("test_save_file.py"))
        # Check if the content is correct
        with open("test_save_file.py", "r") as f:
            content = f.read()
        self.assertEqual(content, "print('Hello, World!')")

    def test_handle_autocompletion(self):
        """Test that autocompletion triggers appropriately."""
        # Triggering autocompletion should result in completion_ready signal being emitted
        mock_slot = MagicMock()
        self.editor.worker_signals.completion_ready.connect(mock_slot)
        
        # Simulate autocompletion trigger
        self.editor.handle_autocompletion()
        
        # Assert that the signal was emitted once
        mock_slot.assert_called_once()

    def test_highlight_current_line(self):
        """Test highlighting the current line."""
        self.editor.highlight_current_line()
        extra_selections = self.editor.extraSelections()
        # Ensure that there is at least one selection indicating the current line is highlighted
        self.assertTrue(len(extra_selections) > 0)

    def test_key_press_event_signature_help(self):
        """Test that key press event triggers signature help."""
        with patch.object(self.editor, 'show_signature_help') as mock_signature_help:
            # Create a key event for opening parenthesis which should trigger signature help
            event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key_ParenLeft, Qt.KeyboardModifier.NoModifier)
            self.editor.keyPressEvent(event)
            mock_signature_help.assert_called_once()

    def test_resize_event(self):
        """Test the resize event handling for line number area adjustment."""
        event = QResizeEvent(self.editor.size(), self.editor.size())
        self.editor.resizeEvent(event)
        # Ensure the line number area width is adjusted correctly
        self.assertEqual(self.editor.lineNumberArea.sizeHint().width(), self.editor.line_number_area_width())

    def test_linting(self):
        """Test that linting detects errors in code."""
        # Run lint worker to check if linting emits results properly
        code = "def my_function("
        lint_worker = LintWorker(code, "temp_code.py")
        
        with patch.object(lint_worker.lint_result, 'emit') as mock_emit:
            lint_worker.run()
            # Assert that lint result was emitted
            mock_emit.assert_called()

if __name__ == "__main__":
    unittest.main()
