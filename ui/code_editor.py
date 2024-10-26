#E:\UDH\Compiler\ui\code_editor.py

import sys
import os
import jedi
import subprocess
import logging
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QCompleter, QToolTip
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QTextCursor, QFont, QTextCharFormat
from PyQt6.QtCore import QRect, QSize, Qt, QStringListModel, pyqtSignal, QObject, QTimer, QThread, QEvent
from concurrent.futures import ThreadPoolExecutor
from .syntax_highlighter import PythonSyntaxHighlighter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.process = None

    def run(self):
        try:
            lint_output = self._run_flake8()  # Run flake8
            lint_data = self._parse_flake8_output(lint_output)  # Parse the output
            if lint_data:
                self.lint_result.emit(lint_data)  # Emit the linting result
        except Exception as e:
            logging.error(f"Linting error: {e}")
        finally:
            self._terminate_and_cleanup()

    def _run_flake8(self):
        try:
            self.process = subprocess.Popen(
                ['flake8', '--stdin-display-name', 'code.py', '-'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output, _ = self.process.communicate(input=self.code)
            return output
        except FileNotFoundError as e:
            logging.error(f"Flake8 not found: {e}")
            raise FileNotFoundError("Flake8 is not installed. Please install it to use linting.")

    def _parse_flake8_output(self, lint_output):
        lint_errors = []
        if lint_output:
            for line in lint_output.splitlines():
                parts = line.split(":")
                if len(parts) >= 4:
                    # Example format: filename:line:column: error_code error_message
                    line_number = int(parts[1])  # Extract the line number
                    error_message = parts[3].strip()  # Extract the error code and message
                    lint_errors.append({
                        "line": line_number,  # 1-based line number
                        "message": error_message,
                    })
        return lint_errors

    def _terminate_and_cleanup(self):
        if self.process:
            try:
                if self.process.poll() is None:
                    self.process.terminate()
                    self.process.wait(3)
            except subprocess.TimeoutExpired:
                self.process.kill()

# CodeEditor class for the main editor functionality
class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()

        # Ensure the Python syntax highlighter is applied
        self.highlighter = PythonSyntaxHighlighter(self.document())  

        self._setup_ui()
        self._setup_linting()
        self._setup_autocompletion()

        self.lint_errors = {}
        self.lint_messages = {}

    def _setup_ui(self):
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Set font and basic appearance settings for the editor
        font = QFont("Courier", 12)
        self.setFont(font)

    def _setup_linting(self):
        self.lint_timer = QTimer(self)
        self.lint_timer.setInterval(1500)
        self.lint_timer.timeout.connect(self.lint_code)
        self.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        self.lint_timer.start()

    def lint_code(self):
        """Lint the code using flake8."""
        code = self.toPlainText()
        
        if hasattr(self, 'lint_worker') and self.lint_worker.isRunning():
            # Ensure we stop any running worker before starting a new one
            self.lint_worker.quit()
            self.lint_worker.wait()

        self.lint_worker = LintWorker(code)
        self.lint_worker.lint_result.connect(self._highlight_lint_errors)
        self.lint_worker.start()

    def _highlight_lint_errors(self, lint_data):
        """Highlight linting errors and warnings in the editor."""
        self.lint_errors.clear()  # Clear previous errors
        extra_selections = []

        for error in lint_data:
            line_number = error['line'] - 1  # Convert 1-based line number to 0-based
            message = error['message']
            self.lint_errors[line_number] = message  # Store the message for further use

            # Create ExtraSelection object to highlight lines
            selection = QTextEdit.ExtraSelection()
            format = QTextCharFormat()  # Create a QTextCharFormat object

            if 'warning' in message.lower():
                format.setBackground(QColor("#FFD700"))  # Yellow for warnings
            else:
                format.setBackground(QColor("#FF6347"))  # Red for errors

            selection.format = format

            cursor = self._get_cursor_at_line(line_number)
            cursor.select(QTextCursor.SelectionType.LineUnderCursor)
            selection.cursor = cursor
            extra_selections.append(selection)

        # Apply selections for highlighting in the editor
        self.setExtraSelections(extra_selections)
        self.update()

        # Send linting data to main window to display in Output Tab
        if hasattr(self.parentWidget(), 'process_lint_results'):
            self.parentWidget().process_lint_results(lint_data)

    def _get_cursor_at_line(self, line_number):
        """Get a QTextCursor positioned at the start of the specified line."""
        cursor = QTextCursor(self.document())  # Create a cursor for the document
        cursor.movePosition(QTextCursor.MoveOperation.Start)  # Move to the start of the document
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.MoveOperation.Down)  # Move down line by line
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)  # Move to the start of the line
        return cursor  # Return the cursor positioned at the start of the specified line

    def eventFilter(self, obj, event):
        """Detect hover events and show tooltips for errors and warnings."""
        if event.type() == QEvent.Type.ToolTip:
            cursor = self.cursorForPosition(event.pos())
            block_number = cursor.blockNumber()

            # If the current line has an error or warning, show a tooltip
            if block_number in self.lint_errors:
                message = self.lint_errors[block_number]
                # Format the message for display
                message = f"<b>Line {block_number + 1}:</b><br>" + message.replace("\n", "<br>")
                QToolTip.showText(event.globalPos(), message, self)
            else:
                QToolTip.hideText()

            return True

        return super().eventFilter(obj, event)

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.line_number_area_width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        return 3 + self.fontMetrics().horizontalAdvance('9') * digits

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
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

    def closeEvent(self, event):
        """Ensure all threads are terminated before closing the application."""
        if hasattr(self, 'lint_worker') and self.lint_worker.isRunning():
            self.lint_worker.quit()
            self.lint_worker.wait()
        super().closeEvent(event)
