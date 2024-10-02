import subprocess
import os
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QFont, QTextCursor
from PyQt6.QtCore import QRect, QSize, Qt


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

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.line_number_area_width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
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
        extra_selections = []
        selection = QTextEdit.ExtraSelection()
        selection.format.setBackground(QColor("#FF6347"))  # Tomato color for error highlight
        selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
        selection.cursor = self.textCursor()

        # Move the cursor to the specified line
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(line_number - 1):  # line_number is 1-based
            cursor.movePosition(QTextCursor.MoveOperation.Down)

        selection.cursor = cursor
        selection.cursor.clearSelection()
        extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def lint_code(self, code):
        """Lint the code using pylint."""
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
