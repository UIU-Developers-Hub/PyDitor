from .toolbar import Toolbar
from .syntax_highlighter import PythonSyntaxHighlighter
from runner.code_runner_thread import CodeRunnerThread
from .pandas_model import PandasModel  # Import PandasModel
import qtawesome as qta  # Import Qt Awesome for icons

import sys
import subprocess
import pandas as pd
import plotly.express as px
import io
import base64
import black
import re
import json
import socket
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QPlainTextEdit, QFileDialog,
    QVBoxLayout, QInputDialog, QWidget, QHBoxLayout, QPushButton, QSplitter,
    QTreeView, QLineEdit, QToolBar, QStatusBar, QComboBox,
    QCheckBox, QTextEdit, QSizePolicy, QDockWidget, QTextBrowser, QGraphicsOpacityEffect
)
from PyQt6.QtGui import (
    QFileSystemModel, QFont, QColor, QPainter, QTextCharFormat,
    QSyntaxHighlighter, QTextFormat, QTextCursor, QKeySequence, QShortcut
)
from PyQt6.QtCore import Qt, QRect, QSize, QThread, pyqtSignal, QRegularExpression


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
        self.setStyleSheet("background-color: #282c34; color: #abb2bf; font-family: 'Courier New';")

        # Initialize completion dictionary
        self.completion_dict = {
            "def": "Define a function",
            "class": "Define a class",
            "import": "Import a module",
            "if": "If statement",
            "elif": "Else if statement",
            "else": "Else statement",
            "while": "While loop",
            "for": "For loop",
            "in": "In operator",
            "return": "Return statement",
            "print": "Print output",
        }

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

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        for _ in range(line_number - 1):  # line_number is 1-based
            cursor.movePosition(QTextCursor.MoveOperation.Down)

        selection.cursor = cursor
        selection.cursor.clearSelection()
        extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def lint_code(self, code):
        """Lint the provided code using pylint."""
        with open("temp_code.py", "w") as temp_file:
            temp_file.write(code)

        result = subprocess.run(['pylint', 'temp_code.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        lint_output = result.stdout.decode('utf-8')

        if lint_output:
            print("Linting Errors:")
            print(lint_output)
        else:
            print("No linting errors found.")

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Tab:
            self.show_completion()
        if event.key() == Qt.Key.Key_F1:  # Show documentation on F1
            self.show_documentation()

    def show_completion(self):
        cursor = self.textCursor()
        current_word = self.get_current_word(cursor)
        if current_word:
            suggestions = self.get_completions(current_word)
            if suggestions:
                print("Suggestions:", suggestions)  # Replace with a dropdown

    def get_current_word(self, cursor):
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()

    def get_completions(self, word):
        return {k: v for k, v in self.completion_dict.items() if k.startswith(word)}

    def show_documentation(self):
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        current_word = cursor.selectedText()

        if current_word:
            documentation = self.fetch_documentation(current_word)
            self.parent().documentation_sidebar.set_widget_content(documentation)
            self.parent().documentation_sidebar.show()
        else:
            self.parent().documentation_sidebar.hide()

    def fetch_documentation(self, element):
        """Fetches documentation for the given code element."""
        try:
            documentation_dict = {
                "def": "Defines a function in Python.",
                "class": "Defines a new class in Python.",
                "import": "Imports a module.",
                "if": "Begins a conditional statement.",
                "for": "Starts a for loop.",
            }
            return documentation_dict.get(element, "No documentation available.")
        except Exception as e:
            return str(e)


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#6a9bd1"))  # Soft Blue
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        self.comment_format = QTextCharFormat()
        self.comment_format.setForeground(QColor("#77dd77"))  # Soft Green

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#f6b0b0"))  # Soft Red

        self.highlighting_rules = []
        keywords = [
            "def", "class", "if", "elif", "else", "while", "for", "in", "return",
            "import", "from", "as", "try", "except", "finally", "with", "lambda", "and", "or", "not", "is"
        ]
        self.highlighting_rules += [(QRegularExpression(r'\b' + keyword + r'\b'), self.keyword_format) for keyword in keywords]
        self.highlighting_rules.append((QRegularExpression(r'#.*'), self.comment_format))
        self.highlighting_rules.append((QRegularExpression(r'\".*?\"'), self.string_format))
        self.highlighting_rules.append((QRegularExpression(r'\'.*?\'', ), self.string_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            expression = QRegularExpression(pattern)
            index = expression.match(text).capturedStart()
            while index >= 0:
                length = expression.match(text).capturedLength()
                self.setFormat(index, length, fmt)
                index = text.find(pattern.pattern(), index + length)

        self.setCurrentBlockState(0)


class CodeRunnerThread(QThread):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)

    def __init__(self, code, input_value):
        super().__init__()
        self.code = code
        self.input_value = input_value

    def run(self):
        process = subprocess.Popen(
            [sys.executable, "-c", self.code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        output, error = process.communicate(input=self.input_value.encode())
        if output:
            self.output_received.emit(output.decode("utf-8"))
        if error:
            self.error_received.emit(error.decode("utf-8"))


class DocumentationSidebar(QDockWidget):
    def __init__(self):
        super().__init__("Documentation")
        self.text_browser = QTextBrowser()
        self.setWidget(self.text_browser)
        self.setFixedWidth(300)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        self.hide()  # Initially hide the sidebar

    def set_widget_content(self, content):
        """Set the content of the documentation sidebar."""
        if content:
            formatted_content = self.format_documentation(content)
            self.text_browser.setHtml(formatted_content)
        else:
            self.text_browser.setPlainText("No documentation available.")
            self.hide()  # Hide if there's no content

    def format_documentation(self, content):
        """Format the documentation content for better readability."""
        return f"<h2>Documentation</h2><p>{content}</p>"


class AICompilerMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Science Code Visualization")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")  # Dark theme

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        # Initialize documentation sidebar
        self.documentation_sidebar = DocumentationSidebar()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.documentation_sidebar)

        # Create Toolbar with QPushButton and Font Selection
        self.toolbar = QToolBar("Toolbar")
        self.addToolBar(self.toolbar)
        self.create_toolbar_buttons()

        self.file_explorer = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath('')  # Set the root path to the file system
        self.file_explorer.setModel(self.file_model)
        self.file_explorer.setRootIndex(self.file_model.index(''))
        self.file_explorer.clicked.connect(self.open_file_from_explorer)

        # Create a splitter for layout management
        left_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_splitter.addWidget(self.file_explorer)

        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.add_new_tab()  # Add an initial new tab

        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.tab_widget)

        # Set the proportions for the left panel
        left_splitter.addWidget(right_splitter)
        left_splitter.setSizes([200, 800])  # Set the file explorer to occupy 20% and the code editor to occupy the rest

        main_layout.addWidget(left_splitter)

        # Create a tab for Input and Output
        self.io_tabs = QTabWidget()
        self.io_tabs.setTabsClosable(False)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Input for the script...")
        self.io_tabs.addTab(self.input_field, "Input")

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("Output/Error logs...")
        self.io_tabs.addTab(self.output_text, "Output")

        io_container = QWidget()
        io_layout = QVBoxLayout(io_container)
        io_layout.addWidget(self.io_tabs)

        # Add the IO container to the right splitter
        right_splitter.addWidget(io_container)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Setup shortcuts
        self.setup_shortcuts()

    def create_toolbar_buttons(self):
        open_button = QPushButton("Open Folder")
        open_button.clicked.connect(self.open_folder)
        open_button.setStyleSheet("padding: 8px; margin: 3px; background-color: #4CAF50; color: white; border-radius: 5px;")
        self.animate_button(open_button)
        self.toolbar.addWidget(open_button)

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_file)
        save_button.setStyleSheet("padding: 8px; margin: 3px; background-color: #2196F3; color: white; border-radius: 5px;")
        self.animate_button(save_button)
        self.toolbar.addWidget(save_button)

        run_button = QPushButton("Run Code")
        run_button.clicked.connect(self.run_code)
        run_button.setStyleSheet("padding: 8px; margin: 3px; background-color: #FF9800; color: white; border-radius: 5px;")
        self.animate_button(run_button)
        self.toolbar.addWidget(run_button)

        new_tab_button = QPushButton("New Tab")
        new_tab_button.clicked.connect(self.add_new_tab)
        new_tab_button.setStyleSheet("padding: 8px; margin: 3px; background-color: #673AB7; color: white; border-radius: 5px;")
        self.animate_button(new_tab_button)
        self.toolbar.addWidget(new_tab_button)

        # Font Family Selection
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Courier New", "Arial", "Times New Roman", "Georgia", "Verdana",
            "Comic Sans MS", "Tahoma", "Lucida Console"
        ])
        self.font_family_combo.currentTextChanged.connect(self.change_font_family)
        self.toolbar.addWidget(self.font_family_combo)

        # Font Size Selection
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["8", "10", "12", "14", "16", "18", "20", "22", "24", "28", "32"])
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)
        self.toolbar.addWidget(self.font_size_combo)

        # Auto Alignment Button
        align_button = QPushButton("Align")
        align_button.clicked.connect(self.auto_align_text)
        align_button.setStyleSheet("padding: 8px; margin: 3px; background-color: #009688; color: white; border-radius: 5px;")
        self.animate_button(align_button)
        self.toolbar.addWidget(align_button)

        # AWS Deployment Button
        aws_deploy_button = QPushButton("Deploy to AWS")
        aws_deploy_button.clicked.connect(self.deploy_to_aws)
        aws_deploy_button.setStyleSheet("padding: 8px; margin: 3px; background-color: #F44336; color: white; border-radius: 5px;")
        self.animate_button(aws_deploy_button)
        self.toolbar.addWidget(aws_deploy_button)

    def animate_button(self, button):
        """Animate button on hover."""
        effect = QGraphicsOpacityEffect()
        button.setGraphicsEffect(effect)  # Enable opacity effect for animation
        button.setCursor(Qt.CursorShape.PointingHandCursor)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder", "")
        if folder_path:
            self.file_model.setRootPath(folder_path)
            self.file_explorer.setRootIndex(self.file_model.index(folder_path))

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Python File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            with open(file_path, "r") as file:
                content = file.read()
            new_editor = CodeEditor()
            new_editor.setPlainText(content)
            tab_index = self.tab_widget.addTab(new_editor, file_path.split("/")[-1])
            self.tab_widget.setCurrentIndex(tab_index)
            self.statusBar.showMessage(f"Opened: {file_path}", 3000)

    def open_file_from_explorer(self, index):
        file_path = self.file_model.filePath(index)
        if file_path.endswith(".py"):
            with open(file_path, "r") as file:
                content = file.read()
            new_editor = CodeEditor()
            new_editor.setPlainText(content)
            tab_index = self.tab_widget.addTab(new_editor, file_path.split("/")[-1])
            self.tab_widget.setCurrentIndex(tab_index)
            self.statusBar.showMessage(f"Opened: {file_path}", 3000)

    def save_file(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, QPlainTextEdit):
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Python File", "", "Python Files (*.py);;All Files (*)")
            if file_path:
                with open(file_path, "w") as file:
                    file.write(current_editor.toPlainText())
                self.statusBar.showMessage(f"Saved: {file_path}", 3000)

    def run_code(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            code = current_editor.toPlainText()
            input_value = self.input_field.text().strip()

            if not code.strip():
                self.statusBar.showMessage("Error: No code to run!", 3000)
                return

            # Run linting before executing code
            current_editor.lint_code(code)

            # Run the code in a separate thread
            self.runner = CodeRunnerThread(code, input_value)
            self.runner.output_received.connect(self.handle_output)
            self.runner.error_received.connect(self.handle_error)
            self.runner.start()

    def handle_output(self, output):
        self.output_text.clear()
        self.output_text.appendPlainText(output)

    def handle_error(self, error):
        self.output_text.clear()
        self.output_text.appendPlainText(error)

        # Extract line number from the error message if available
        match = re.search(r'File ".+?", line (\d+)', error)
        if match:
            line_number = int(match.group(1))
            current_editor = self.tab_widget.currentWidget()
            if isinstance(current_editor, CodeEditor):
                current_editor.highlight_error_line(line_number)

    def start_language_server(self):
        try:
            self.language_server_process = subprocess.Popen(
                [r'E:\UDH\Compiler\myenv\Scripts\pylsp.exe'],  # Path to your pylsp executable
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.language_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.language_server_socket.connect(('127.0.0.1', 2087))  # Default port for pylsp
        except FileNotFoundError:
            print("Error: pylsp is not found. Please install the Python Language Server.")
        except ConnectionRefusedError:
            print("Error: Unable to connect to the language server. Make sure it's running.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

    def toggle_dark_mode(self):
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")  # Keep dark theme

    def change_font_family(self, font_family):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_editor.setFont(QFont(font_family, current_editor.font().pointSize()))

    def change_font_size(self, font_size):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_editor.setFont(QFont(current_editor.font().family(), int(font_size)))
            current_editor.update_line_number_area_width(0)  # Update line numbers when font size changes

    def auto_align_text(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            try:
                # Format the text using black
                formatted_code = black.format_str(current_editor.toPlainText(), mode=black.FileMode())
                current_editor.setPlainText(formatted_code)
            except Exception as e:
                self.output_text.setPlainText(f"Error in formatting: {str(e)}")

    def add_new_tab(self):
        new_editor = CodeEditor()
        new_editor.setFont(QFont("monospace", 12))
        tab_index = self.tab_widget.addTab(new_editor, "Untitled")
        self.tab_widget.setCurrentIndex(tab_index)

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_new_tab)  # New Tab
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_file)  # Open File
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_file)  # Save File
        QShortcut(QKeySequence("Ctrl+R"), self, activated=self.run_code)  # Run Code

    def deploy_to_aws(self):
        app_name, ok = QInputDialog.getText(self, "Deploy to AWS", "Enter your app name:")
        if ok and app_name:
            command = f"aws elasticbeanstalk create-application --application-name {app_name}"
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate()
            if output:
                self.output_text.appendPlainText(output.decode("utf-8"))
            if error:
                self.output_text.appendPlainText(error.decode("utf-8"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = AICompilerMainWindow()
    main_win.show()
    sys.exit(app.exec())
