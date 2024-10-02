from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Define formats for syntax highlighting
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#7aa6da"))  # Softer blue color for keywords
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#b9ca4a"))  # Greenish color for comments

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#dca3a3"))  # Soft red color for strings

        # Define regex patterns for syntax highlighting
        keywords = [
            "def", "class", "if", "elif", "else", "while", "for", "in", "return",
            "import", "from", "as", "try", "except", "finally", "with", "lambda", "and", "or", "not", "is",
            "break", "continue", "pass", "raise", "yield", "assert"
        ]

        self.highlighting_rules = [
            # Keywords
            (QRegularExpression(r'\b(' + '|'.join(keywords) + r')\b'), self.keyword_format),
            # Comments
            (QRegularExpression(r'#.*'), self.comment_format),
            # Strings (single and double quotes)
            (QRegularExpression(r'\".*?\"'), self.string_format),
            (QRegularExpression(r"\'.*?\'"), self.string_format),
        ]

    def highlightBlock(self, text):
        # Apply highlighting rules
        for pattern, fmt in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            match_iterator = expression.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)

        self.setCurrentBlockState(0)
