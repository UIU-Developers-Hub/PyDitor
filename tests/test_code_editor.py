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
