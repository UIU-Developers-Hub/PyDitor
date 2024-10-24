from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.token import Token
from pygments.formatter import Formatter

class QFormatter(Formatter):
    """
    A custom Pygments formatter that applies syntax highlighting
    via the QSyntaxHighlighter interface.
    """
    def __init__(self, highlighter):
        super().__init__()
        self.highlighter = highlighter
        self.data = []

    def format(self, tokensource, outfile):
        """Store tokens for later use."""
        for ttype, value in tokensource:
            self.data.append((ttype, value))

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for Python using Pygments lexer and custom QSyntaxHighlighter.
    """
    def __init__(self, document):
        super().__init__(document)
        self.lexer = PythonLexer()
        self.formatter = QFormatter(self)

        # Define the text formats for each token type (VS Code-like theme)
        self.formats = {
            Token.Keyword: self.create_format(QColor("#569CD6"), bold=True),  # Blue for keywords
            Token.Comment: self.create_format(QColor("#6A9955")),  # Green for comments
            Token.String: self.create_format(QColor("#CE9178")),  # Red for strings
            Token.Number: self.create_format(QColor("#B5CEA8")),  # Light green for numbers
            Token.Operator: self.create_format(QColor("#D4D4D4")),  # Light grey for operators
            Token.Name.Function: self.create_format(QColor("#DCDCAA")),  # Yellow for functions
            Token.Name.Class: self.create_format(QColor("#4EC9B0")),  # Cyan for classes
            Token.Name.Variable: self.create_format(QColor("#9CDCFE")),  # Light blue for variables
            Token.Text: self.create_format(QColor("#D4D4D4")),  # Default text color (light grey)
        }

    def create_format(self, color, bold=False, italic=False):
        """Helper method to create a QTextCharFormat."""
        text_format = QTextCharFormat()
        text_format.setForeground(color)
        if bold:
            text_format.setFontWeight(QFont.Weight.Bold)
        if italic:
            text_format.setFontItalic(True)
        return text_format

    def highlightBlock(self, text):
        """Apply syntax highlighting to the block of text."""
        # Use Pygments to tokenize the text
        highlight(text, self.lexer, self.formatter)

        # Apply formatting based on the tokens
        index = 0
        for ttype, value in self.formatter.data:
            length = len(value)
            token_type = ttype
            while token_type not in self.formats and token_type.parent:
                token_type = token_type.parent  # Fallback to parent token type
            if token_type in self.formats:
                self.setFormat(index, length, self.formats[token_type])
            index += length

        # Clear formatter data for next use
        self.formatter.data = []
