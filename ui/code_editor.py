# File: ui/code_editor.py

import subprocess
import os
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QFont, QTextCursor, QSyntaxHighlighter, QTextCharFormat
from PyQt6.QtCore import QRect, QSize, Qt, QTimer, QRegularExpression
from .syntax_highlighter import PythonSyntaxHighlighter  # Import PythonSyntaxHighlighter from syntax_highlighter.py

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Initialize syntax highlighter
        self.highlighter = PythonSyntaxHighlighter(self.document())

        # Set background and text colors
        self.setStyleSheet("background-color: #2b2b2b; color: white;")

        # Debounce timer for linting
        self.lint_timer = QTimer(self)
        self.lint_timer.setInterval(500)  # 500 ms debounce
        self.lint_timer.timeout.connect(self.lint_code)

        # Connect key press event to linting
        self.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        """Handle text changes and debounce linting."""
        self.lint_timer.start()  # Restart the debounce timer

    def line_number_area_width(self):
        """Calculate the width required for the line number area."""
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Update the viewport margins for the line number area."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Update the line number area when scrolling or when text changes."""
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.line_number_area_width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Handle resizing events."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        """Paint the line number area."""
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#2b2b2b"))  # Background color

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#FFFFFF"))  # Line number color
                painter.drawText(0, top, self.lineNumberArea.width(), self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        """Highlight the current line where the cursor is."""
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#3b3b3b")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def highlight_error_line(self, line_number):
        """Highlight the specified line with an error."""
        extra_selections = []
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#FF6347"))  # Tomato color for error highlight
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)

        # Move the cursor to the specified line
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(line_number - 1):  # line_number is 1-based
            cursor.movePosition(QTextCursor.MoveOperation.Down)

        selection.cursor = cursor
        selection.cursor.clearSelection()
        extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def lint_code(self):
        """Lint the code using pylint."""
        code = self.toPlainText()  # Get the current code
        with open("temp_code.py", "w") as temp_file:
            temp_file.write(code)

        # Run pylint on the temporary file
        result = subprocess.run(['pylint', 'temp_code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lint_output = result.stdout.decode('utf-8')

        # Print or process the linting results
        if lint_output:
            print("Linting Errors:")
            print(lint_output)
        else:
            print("No linting issues found.")

        # Cleanup
        os.remove("temp_code.py")
