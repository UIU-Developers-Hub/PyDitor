import sys  # Ensure sys is imported for subprocess handling
import jedi
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QTextEdit, QCompleter, QToolTip, QMessageBox
from PyQt6.QtGui import QColor, QPainter, QTextFormat, QTextCursor, QTextCharFormat
from PyQt6.QtCore import QRect, QSize, Qt, QStringListModel, pyqtSignal, QObject
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

        # Set up for autocompletion
        self.completer = QCompleter(self)
        self.completer.popup().setStyleSheet("background-color: #2b2b2b; color: white;")
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.completer.activated.connect(self.insert_completion)

        # Create thread pool executor for Jedi autocompletion
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.worker_signals = CompletionWorkerSignals()
        self.worker_signals.completion_ready.connect(self.show_completions)

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
            # Create an instance of QTextEdit.ExtraSelection
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#3b3b3b")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def handle_autocompletion(self):
        """Handle the logic for showing autocompletion suggestions by using a background thread."""
        cursor = self.textCursor()
        # Use the actual position of the cursor to get the correct location in the code
        position = cursor.position()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber()

        # Fetch the full content of the editor to pass to Jedi
        source = self.toPlainText()

        # Debugging output to understand what's being processed
        print(f"handle_autocompletion() triggered, line: {line}, column: {column}, position: {position}")

        # Only trigger autocomplete when it makes sense (e.g., alphabetic characters or dot)
        if not source or not source[position - 1].isidentifier() and source[position - 1] != '.':
            self.completer.popup().hide()
            return

        # Submit Jedi analysis to the thread pool
        self.executor.submit(self.get_completions, source, line, column)

    def get_completions(self, source, line, column):
        """Use Jedi to get completions in a background thread."""
        try:
            # Create a Jedi script with the entire source
            script = jedi.Script(code=source, path='<stdin>')
            completions = script.complete(line=line, column=column)

            # Debugging print to check if Jedi is returning completions
            print(f"get_completions() called: line {line}, column {column}, completions found: {[c.name for c in completions]}")

            # Extract the completion names and details
            completion_suggestions = [completion.name for completion in completions]
            completion_docs = [completion.docstring() for completion in completions]

            # Emit signal to update UI
            self.worker_signals.completion_ready.emit(completion_suggestions, completion_docs)
        except Exception as e:
            print(f"Jedi Error in get_completions: {e}")

    def show_completions(self, completion_suggestions, completion_docs):
        """Update the UI with completion suggestions."""
        if not completion_suggestions:
            self.completer.popup().hide()
            return

        # Set the model for the completer
        model = QStringListModel(completion_suggestions, self.completer)
        self.completer.setModel(model)

        # Cache completion documentation to be shown later
        self.completion_docs = completion_docs

        # Move completer to the cursor position
        rect = self.cursorRect()
        rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)  # Show the popup at the cursor

        # Debugging print for completions
        print(f"show_completions() called, suggestions: {completion_suggestions}")

    def show_completion_details(self, index):
        """Show a tooltip with the documentation of the selected completion."""
        if index >= 0 and index < len(self.completion_docs):
            doc = self.completion_docs[index]
            if doc:
                # Display the tooltip with the documentation string
                QToolTip.showText(self.mapToGlobal(self.cursorRect().bottomRight()), doc)

    def insert_completion(self, completion):
        """Insert the selected completion into the editor and suggest imports if necessary."""
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.insertText(completion)
        self.setTextCursor(cursor)

        # Handle automatic import suggestion
        suggested_import = self.get_import_statement(completion)
        if suggested_import and suggested_import not in self.toPlainText():
            # Suggest adding the import statement
            add_import = QMessageBox.question(
                self,
                "Missing Import",
                f"The completion '{completion}' requires an import. Do you want to add: '{suggested_import}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if add_import == QMessageBox.StandardButton.Yes:
                self.insert_import(suggested_import)

    def get_import_statement(self, completion):
        """Use Jedi to determine the necessary import for a given completion."""
        try:
            # Use Jedi to create a script context and fetch completions
            script = jedi.Script(f"{completion}")
            completions = script.complete()

            for comp in completions:
                if comp.name == completion and comp.module_name:
                    # Return the import statement for the missing module
                    return f"import {comp.module_name}"
        except Exception as e:
            print(f"Jedi Error in get_import_statement: {e}")
        return None

    def insert_import(self, import_statement):
        """Insert an import statement at the top of the document."""
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.insertText(import_statement + "\n")
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        """Override keyPressEvent to capture key presses for autocompletion."""
        super().keyPressEvent(event)

        # Debugging output for key presses
        print(f"keyPressEvent() called, key: '{event.text()}'")

        # Trigger autocompletion manually if necessary
        if event.text() in (".", "(", "[", "{"):  # Characters that may warrant a completion
            self.handle_autocompletion()
