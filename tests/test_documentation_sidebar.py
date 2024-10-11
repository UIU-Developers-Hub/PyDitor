# File: tests/test_documentation_sidebar.py

import unittest
from ui.documentation_sidebar import DocumentationSidebar
from PyQt6.QtWidgets import QApplication

app = QApplication([])

class TestDocumentationSidebar(unittest.TestCase):

    def setUp(self):
        self.sidebar = DocumentationSidebar()

    def test_set_widget_content(self):
        """Test setting content in the documentation sidebar."""
        content = "def test_function():\n    pass"
        self.sidebar.set_widget_content(content)
        self.assertIn("test_function", self.sidebar.text_browser.toPlainText(), "Documentation content not set correctly.")

if __name__ == "__main__":
    unittest.main()
