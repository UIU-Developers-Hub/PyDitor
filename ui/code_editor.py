import sys
import os
import jedi
import subprocess
import logging
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QCompleter, QToolTip
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QTextCursor
from PyQt6.QtCore import QRect, QSize, Qt, QStringListModel, pyqtSignal, QObject, QTimer, QThread
from concurrent.futures import ThreadPoolExecutor
from .syntax_highlighter import PythonSyntaxHighlighter

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# LineNumberArea class to display line numbers in the editor
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

# Signals for the background worker, allowing communication back to the main thread
class CompletionWorkerSignals(QObject):
    completion_ready = pyqtSignal(list, list)

# LintWorker class for linting code in a separate thread using flake8
class LintWorker(QThread):
    lint_result = pyqtSignal(list)

    def __init__(self, code):
        super().__init__()
        self.code = code

    def run(self):
        try:
            lint_output = self._run_flake8()
            lint_data = self._parse_flake8_output(lint_output)
            if lint_data:
                self.lint_result.emit(lint_data)
        except Exception as e:
            logging.error(f"Linting error: {e}")

    def _run_flake8(self):
        """Run flake8 on the code using stdin."""
        result = subprocess.run(
            ['flake8', '--stdin-display-name', 'code.py', '-'],
            input=self.code.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return result.stdout.decode('utf-8')

    def _parse_flake8_output(self, lint_output):
        """Parse the flake8 output."""
        lint_errors = []
        if lint_output:
            for line in lint_output.splitlines():
                parts = line.split(":")
                if len(parts) >= 3:
                    lint_errors.append({
                        "line": int(parts[1]),
                        "message": parts[2].strip(),
                    })
        return lint_errors

# CodeEditor class for the main editor functionality
class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_linting()
        self._setup_autocompletion()

        # Track lint errors
        self.lint_errors = {}

    def _setup_ui(self):
        """Set up the UI components including the line number area."""
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.setStyleSheet("background-color: #2b2b2b; color: white;")

    def _setup_linting(self):
        """Set up linting with a timer for delayed execution."""
        self.lint_timer = QTimer(self)
        self.lint_timer.setInterval(1500)  # 1.5 seconds idle time before linting
        self.lint_timer.timeout.connect(self.lint_code)
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        """Start lint timer when text is changed."""
        self.lint_timer.start()

    def lint_code(self):
        """Lint the code in the current editor using flake8."""
        code = self.toPlainText()  # Get code from editor directly
        self.lint_worker = LintWorker(code)
        self.lint_worker.lint_result.connect(self._highlight_lint_errors)
        self.lint_worker.start()

    def _highlight_lint_errors(self, lint_data):
        """Highlight errors from linting."""
        self.lint_errors.clear()
        self.highlight_current_line()
        extra_selections = []

        for error in lint_data:
            line_number = error.get('line') - 1
            self.lint_errors[line_number] = error.get('message')

            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#FFD700"))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            cursor = self._get_cursor_at_line(line_number)
            selection.cursor = cursor
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def _get_cursor_at_line(self, line_number):
        """Get a cursor positioned at the specified line."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        return cursor

    def update_line_number_area_width(self, _):
        """Update the line number area width based on the number of digits."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Handle updates to the line number area during scrolling."""
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.line_number_area_width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def line_number_area_width(self):
        """Calculate the required width for the line number area."""
        digits = len(str(max(1, self.blockCount())))
        return 3 + self.fontMetrics().horizontalAdvance('9') * digits

    def resizeEvent(self, event):
        """Resize the line number area when the editor is resized."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        """Paint the line numbers in the line number area."""
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor("#2b2b2b"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#FFFFFF"))
                painter.drawText(0, top, self.lineNumberArea.width(), self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        """Highlight the current line in the editor."""
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#3b3b3b"))
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def _setup_autocompletion(self):
        """Set up autocompletion system."""
        self.completer = QCompleter(self)
        self.completer.popup().setStyleSheet("background-color: #2b2b2b; color: white;")
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.activated.connect(self.insert_completion)

        # Use a thread pool for fetching completions asynchronously
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.worker_signals = CompletionWorkerSignals()
        self.worker_signals.completion_ready.connect(self.show_completions)

        # Set up a timer to delay autocompletion until typing has paused
        self.auto_completion_timer = QTimer(self)
        self.auto_completion_timer.setInterval(300)  # 300ms delay before showing completions
        self.auto_completion_timer.timeout.connect(self._handle_autocompletion)
        self.textChanged.connect(self.auto_completion_timer.start)

    def _handle_autocompletion(self):
        """Handle autocompletion after the timer delay."""
        self.auto_completion_timer.stop()  # Stop the timer after triggering

        cursor = self.textCursor()
        source = self.toPlainText()

        if not source or not source[cursor.position() - 1].isidentifier() and source[cursor.position() - 1] != '.':
            self.completer.popup().hide()
            return

        self.executor.submit(self._get_completions, source, cursor.blockNumber() + 1, cursor.columnNumber())

    def _get_completions(self, source, line, column):
        """Fetch autocompletion suggestions asynchronously using Jedi."""
        try:
            script = jedi.Script(code=source, path='<stdin>')
            completions = script.complete(line=line, column=column)
            self.worker_signals.completion_ready.emit(
                [completion.name for completion in completions],
                [completion.docstring() for completion in completions]
            )
        except Exception as e:
            logging.error(f"Jedi Error in get_completions: {e}")

    def show_completions(self, completion_suggestions):
        """Show autocompletion suggestions in the popup."""
        if not completion_suggestions:
            self.completer.popup().hide()
            return

        # Set the completion suggestions to the completer's model
        model = QStringListModel(completion_suggestions, self.completer)
        self.completer.setModel(model)

        # Show the popup at the current cursor position
        rect = self.cursorRect()
        rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)

    def insert_completion(self, completion):
        """Insert selected completion into the editor."""
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(completion)
        self.setTextCursor(cursor)
