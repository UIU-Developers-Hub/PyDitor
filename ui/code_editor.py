import sys
import os
import jedi
import subprocess
import time
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QCompleter, QToolTip
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QTextCursor
from PyQt6.QtCore import QRect, QSize, Qt, QStringListModel, pyqtSignal, QObject, QTimer, QThread
from concurrent.futures import ThreadPoolExecutor
from .syntax_highlighter import PythonSyntaxHighlighter

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

# LintWorker class for linting code in a separate thread
class LintWorker(QThread):
    lint_result = pyqtSignal(list)

    def __init__(self, code, temp_filename):
        super().__init__()
        self.code = code
        self.temp_filename = temp_filename

    def run(self):
        try:
            self._write_code_to_temp_file()
            lint_output = self._run_pylint()
            lint_data = self._parse_lint_output(lint_output)
            if lint_data:
                self.lint_result.emit(lint_data)
        except Exception as e:
            print(f"Linting error: {e}")
        finally:
            self._delete_temp_file()

    def _write_code_to_temp_file(self):
        with open(self.temp_filename, "w") as temp_file:
            temp_file.write(self.code)

    def _run_pylint(self):
        result = subprocess.run(['pylint', self.temp_filename, '--output-format', 'json'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode('utf-8')

    def _parse_lint_output(self, lint_output):
        if lint_output:
            import json
            return json.loads(lint_output)
        return []

    def _delete_temp_file(self):
        time.sleep(0.1)
        for attempt in range(3):
            try:
                if os.path.exists(self.temp_filename):
                    os.remove(self.temp_filename)
                    return
            except PermissionError:
                time.sleep(0.5)
        print(f"Failed to delete temporary file '{self.temp_filename}' after 3 attempts.")

# CodeEditor class for the main editor functionality
class CodeEditor(QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_highlighting_and_autocompletion()
        self._setup_linting()

        # Track lint errors and breakpoints
        self.lint_errors = {}

    def _setup_ui(self):
        self.lineNumberArea = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.highlight_current_line()
        self.setStyleSheet("background-color: #2b2b2b; color: white;")

    def _setup_highlighting_and_autocompletion(self):
        self.highlighter = PythonSyntaxHighlighter(self.document())
        self.completer = None
        self._initialize_autocompleter()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.worker_signals = CompletionWorkerSignals()
        self.worker_signals.completion_ready.connect(self.show_completions)

    def _setup_linting(self):
        self.lint_timer = QTimer(self)
        self.lint_timer.setInterval(1500)
        self.lint_timer.timeout.connect(self.lint_code)
        self.textChanged.connect(self._on_text_changed)

    def _initialize_autocompleter(self):
        if self.completer is None:
            self.completer = QCompleter(self)
            self.completer.popup().setStyleSheet("background-color: #2b2b2b; color: white;")
            self.completer.setWidget(self)
            self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            self.completer.activated.connect(self.insert_completion)

    def _on_text_changed(self):
        self.lint_timer.start()

    def lint_code(self):
        code = self.toPlainText()
        temp_filename = "temp_code.py"
        self.lint_worker = LintWorker(code, temp_filename)
        self.lint_worker.lint_result.connect(self._highlight_lint_errors)
        self.lint_worker.start()

    def _highlight_lint_errors(self, lint_data):
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
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(line_number):
            cursor.movePosition(QTextCursor.MoveOperation.Down)
        return cursor

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

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.text() == "(":
            self._show_signature_help()
        if event.text() in (".", "(", "[", "{"):
            self._handle_autocompletion()

    def _show_signature_help(self):
        cursor = self.textCursor()
        source_code = self.toPlainText()
        try:
            script = jedi.Script(source_code)
            signatures = script.get_signatures(line=cursor.blockNumber() + 1, column=cursor.columnNumber())
            if signatures:
                signature = signatures[0]
                params = ', '.join(param.name for param in signature.params)
                QToolTip.showText(self.mapToGlobal(self.cursorRect(cursor).topRight()),
                                  f"{signature.name}({params})", self)
        except Exception as e:
            print(f"Error in show_signature_help: {e}")

    def insert_completion(self, completion):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(completion)
        self.setTextCursor(cursor)

    def _handle_autocompletion(self):
        self._initialize_autocompleter()
        cursor = self.textCursor()
        source = self.toPlainText()
        if not source or not source[cursor.position() - 1].isidentifier() and source[cursor.position() - 1] != '.':
            self.completer.popup().hide()
            return
        self.executor.submit(self._get_completions, source, cursor.blockNumber() + 1, cursor.columnNumber())

    def _get_completions(self, source, line, column):
        try:
            script = jedi.Script(code=source, path='<stdin>')
            completions = script.complete(line=line, column=column)
            self.worker_signals.completion_ready.emit(
                [completion.name for completion in completions],
                [completion.docstring() for completion in completions]
            )
        except Exception as e:
            print(f"Jedi Error in get_completions: {e}")

    def show_completions(self, completion_suggestions, _):
        if not completion_suggestions:
            self.completer.popup().hide()
            return
        model = QStringListModel(completion_suggestions, self.completer)
        self.completer.setModel(model)
        rect = self.cursorRect()
        rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)
