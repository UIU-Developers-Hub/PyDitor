import unittest
from ui.syntax_highlighter import PythonSyntaxHighlighter
from PyQt6.QtGui import QTextDocument

class TestSyntaxHighlighter(unittest.TestCase):

    def setUp(self):
        self.document = QTextDocument()
        self.highlighter = PythonSyntaxHighlighter(self.document)

    def test_highlight_python_code(self):
        code = "def test_function():\n    return True"
        self.document.setPlainText(code)
        # You can extend this to check if highlighting rules were applied properly

if __name__ == "__main__":
    unittest.main()
