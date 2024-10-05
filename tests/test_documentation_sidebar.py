import unittest
from ui.documentation_sidebar import DocumentationSidebar
from PyQt6.QtWidgets import QApplication

app = QApplication([])

class TestDocumentationSidebar(unittest.TestCase):

    def setUp(self):
        self.sidebar = DocumentationSidebar()

    def test_fetch_documentation(self):
        self.sidebar.fetch_documentation("def")
        self.assertIn("def", self.sidebar.text_area.toPlainText(), "Documentation not fetched properly")

if __name__ == "__main__":
    unittest.main()
