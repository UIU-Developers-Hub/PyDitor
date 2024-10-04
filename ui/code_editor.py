# File: ui/code_editor.py

import sys  # Ensure sys is imported for subprocess handling
import jedi
import subprocess
import os
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QCompleter, QToolTip, QMessageBox
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QTextCursor, QTextCharFormat
from PyQt6.QtCore import QRect, QSize, Qt, QStringListModel, pyqtSignal, QObject, QTimer, QThread
from concurrent.futures import ThreadPoolExecutor
from .syntax_highlighter import PythonSyntaxHighlighter


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class CompletionWorkerSignals(QObject):
    """Signals to be emitted by the background thread worker to update the UI."""
    completion_ready = pyqtSignal(list, list)


class LintWorker(QThread):
    """A QThread to handle linting operations without blocking the UI."""
    lint_result = pyqtSignal(list)  # Emit lint data when finished

    def __init__(self, code, temp_filename):
        super().__init__()
        self.code = code
        self.temp_filename = temp_filename

    def run(self):
        # Write code to a temporary file for linting
        with open(self.temp_filename, "w") as temp_file:
            temp_file.write(self.code)

        # Run pylint on the temporary file
        try:
            result = subprocess.run(
                ['pylint', self.temp_filename, '--output-format', 'json'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            lint_output = result.stdout.decode('utf-8')
            if lint_output:
                import json
                lint_data = json.loads(lint_output)
                self.lint_result.emit(lint_data)
        except Exception as e:
            print(f"Linting error: {e}")
        finally:
            if os.path.exists(self.temp_filename):
                os.remove(self.temp_filename)


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

        # Set up for autocompletion (Deferred Initialization)
        self.completer = None
        self.initialize_autocompleter()

        # Create thread pool executor for Jedi autocompletion (limit max workers to avoid performance issues)
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.worker_signals = CompletionWorkerSignals()
        self.worker_signals.completion_ready.connect(self.show_completions)

        # Linting debounce timer (increase interval to reduce frequency)
        self.lint_timer = QTimer(self)
        self.lint_timer.setInterval(1500)  # Set debounce interval to 1.5 seconds for better performance
        self.lint_timer.timeout.connect(self.lint_code)
        self.textChanged.connect(self.on_text_changed)

        # Dictionary to keep track of linting errors per line
        self.lint_errors = {}

    def initialize_autocompleter(self):
        """Deferred initialization for autocompleter to improve startup performance."""
        if self.completer is None:
            self.completer = QCompleter(self)
            self.completer.popup().setStyleSheet("background-color: #2b2b2b; color: white;")
            self.completer.setWidget(self)
            self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            self.completer.activated.connect(self.insert_completion)

    def on_text_changed(self):
        """Handle text changes and debounce linting."""
        self.lint_timer.start()  # Restart the debounce timer

    def lint_code(self):
        """Lint the code using pylint asynchronously."""
        code = self.toPlainText()
        temp_filename = "temp_code.py"

        # Create and start the lint worker thread
        self.lint_worker = LintWorker(code, temp_filename)
        self.lint_worker.lint_result.connect(self.highlight_lint_errors)
        self.lint_worker.start()

    def highlight_lint_errors(self, lint_data):
        """Highlight lines with linting errors in a more subtle way."""
        self.lint_errors.clear()

        # Clear previous extra selections for lint errors
        self.highlight_current_line()  # This will remove all previous selections

        extra_selections = []

        # Update linting error color to be less aggressive
        for error in lint_data:
            line_number = error.get('line') - 1
            message = error.get('message')
            self.lint_errors[line_number] = message

            # Create an extra selection for lint error highlighting
            selection = QTextEdit.ExtraSelection()
            error_color = QColor("#FFD700")  # Light yellow color for a more subtle background
            selection.format.setBackground(error_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)

            # Move cursor to the problematic line
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)  # Start at the beginning
            for _ in range(line_number):
                cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.MoveAnchor)

            # Apply selection to the specific problematic line
            selection.cursor = cursor
            selection.cursor.clearSelection()

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

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

    def line_number_area_width(self):
        """Calculate the width required for the line number area."""
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

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

    def show_signature_help(self):
        """Display signature help (e.g., function parameters) as a tooltip."""
        cursor = self.textCursor()
        position = cursor.position()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber()

        source_code = self.toPlainText()

        try:
            # Use Jedi to get the signature for the function call at the current cursor position
            script = jedi.Script(source_code)
            signatures = script.get_signatures(line=line, column=column)

            if signatures:
                # Get the signature information to display
                signature = signatures[0]
                params = ', '.join(param.name for param in signature.params)
                signature_text = f"{signature.name}({params})"

                # Show a tooltip near the cursor with the signature information
                cursor_rect = self.cursorRect(cursor)
                QToolTip.showText(self.mapToGlobal(cursor_rect.topRight()), signature_text, self)
        except Exception as e:
            print(f"Error in show_signature_help: {e}")

    def keyPressEvent(self, event):
        """Override keyPressEvent to capture key presses for autocompletion and signature help."""
        super().keyPressEvent(event)

        if event.text() == "(":
            self.show_signature_help()

        if event.text() in (".", "(", "[", "{"):
            self.handle_autocompletion()

    def insert_completion(self, completion):
        """Insert the selected completion into the editor."""
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(completion)
        self.setTextCursor(cursor)

    def handle_autocompletion(self):
        """Handle the logic for showing autocompletion suggestions by using a background thread."""
        self.initialize_autocompleter()  # Ensure autocompleter is initialized
        cursor = self.textCursor()
        position = cursor.position()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber()

        source = self.toPlainText()

        # Trigger Jedi to analyze and fetch completions
        if not source or not source[position - 1].isidentifier() and source[position - 1] != '.':
            self.completer.popup().hide()
            return

        self.executor.submit(self.get_completions, source, line, column)

    def get_completions(self, source, line, column):
        """Use Jedi to get completions in a background thread."""
        try:
            script = jedi.Script(code=source, path='<stdin>')
            completions = script.complete(line=line, column=column)

            completion_suggestions = [completion.name for completion in completions]
            completion_docs = [completion.docstring() for completion in completions]

            self.worker_signals.completion_ready.emit(completion_suggestions, completion_docs)
        except Exception as e:
            print(f"Jedi Error in get_completions: {e}")

    def show_completions(self, completion_suggestions, completion_docs):
        """Update the UI with completion suggestions."""
        if not completion_suggestions:
            self.completer.popup().hide()
            return

        model = QStringListModel(completion_suggestions, self.completer)
        self.completer.setModel(model)

        self.completion_docs = completion_docs
        rect = self.cursorRect()
        rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)
