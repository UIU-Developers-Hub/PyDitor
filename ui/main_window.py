# File: ui/main_window.py

import os
import pickle
import json
import subprocess
import sys

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QPlainTextEdit, QFileDialog,
    QVBoxLayout, QWidget, QHBoxLayout, QSplitter,
    QTreeView, QLineEdit, QStatusBar, QDockWidget, QApplication, QMenu, QInputDialog, QMessageBox, QToolBar, QPushButton, QFontDialog
)
from PyQt6.QtGui import QFont, QColor, QAction, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QThreadPool, QRunnable, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFileSystemModel

from ui.toolbar import Toolbar
from runner.code_runner_thread import CodeRunnerThread
from runner.debugger_thread import DebuggerThread
from ui.documentation_sidebar import DocumentationSidebar
from ui.code_editor import CodeEditor


class Signals(QObject):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)


class CodeRunnerRunnable(QRunnable):
    def __init__(self, code, input_value, signals):
        super().__init__()
        self.code = code
        self.input_value = input_value
        self.signals = signals

    def run(self):
        try:
            command = [sys.executable, '-c', self.code]
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = process.communicate(input=self.input_value.encode())

            if output:
                self.signals.output_received.emit(output.decode('utf-8'))
            if error:
                self.signals.error_received.emit(error.decode('utf-8'))
        except Exception as e:
            self.signals.error_received.emit(str(e))


class AICompilerMainWindow(QMainWindow):
    # Constants for autosave and session file paths
    RECENT_FILES_LIMIT = 5
    RECENT_FILES_PATH = "recent_files.pkl"
    SETTINGS_PATH = "user_settings.json"
    SESSION_PATH = "last_session.json"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Science Code Visualization")
        self.setGeometry(100, 100, 1200, 800)
        self.load_user_settings()
        self.setup_ui()
        self.setup_shortcuts()
        self.thread_pool = QThreadPool()

        # Start autosave timer
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(10000)  # Autosave every 10 seconds

        # Restore the last session
        self.restore_session()

    def setup_ui(self):
        # Applying a consistent dark theme with contrast
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.recent_files = self.load_recent_files()

        # Initialize Toolbar
        self.toolbar = Toolbar(self)
        self.addToolBar(self.toolbar)

        # Add Font Settings Button to Toolbar
        font_button = QPushButton("Font Settings", self)
        font_button.clicked.connect(self.open_font_dialog)
        self.toolbar.addWidget(font_button)

        # Add Debugger Controls
        self.debugger_toolbar = QToolBar("Debugger", self)
        self.addToolBar(self.debugger_toolbar)

        # Add Debugger Actions
        self.start_debugger_action = QAction("Start Debugger", self)
        self.start_debugger_action.triggered.connect(self.start_debugger)
        self.debugger_toolbar.addAction(self.start_debugger_action)

        self.continue_debugger_action = QAction("Continue", self)
        self.continue_debugger_action.triggered.connect(self.continue_debugger)
        self.debugger_toolbar.addAction(self.continue_debugger_action)

        self.step_debugger_action = QAction("Step", self)
        self.step_debugger_action.triggered.connect(self.step_debugger)
        self.debugger_toolbar.addAction(self.step_debugger_action)

        # Initialize documentation sidebar
        self.documentation_sidebar = DocumentationSidebar()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.documentation_sidebar)

        # File Explorer setup
        self.file_explorer = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath('')
        self.file_explorer.setModel(self.file_model)
        self.file_explorer.setRootIndex(self.file_model.index(''))
        self.file_explorer.clicked.connect(self.open_file_from_explorer)

        # Create Splitters and Layouts
        left_splitter = QSplitter(Qt.Orientation.Horizontal)
        left_splitter.addWidget(self.file_explorer)

        # Tab Widget for Code Editor
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.highlight_active_tab)
        self.add_new_tab()  # Add an initial tab

        # Layout for the right-hand side splitter
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.tab_widget)
        left_splitter.addWidget(right_splitter)

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(left_splitter)
        self.setCentralWidget(central_widget)

        self.setup_io_tabs(right_splitter)
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    def setup_io_tabs(self, right_splitter):
        """Set up Input/Output tabs in the right splitter."""
        self.io_tabs = QTabWidget()
        self.io_tabs.setTabsClosable(False)
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("background-color: #2e2e2e; color: #abb2bf; padding: 10px;")
        self.input_field.setPlaceholderText("Input for the script...")
        self.io_tabs.addTab(self.input_field, "Input")

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color: #2e2e2e; color: #abb2bf; padding: 10px;")
        self.output_text.setPlaceholderText("Output/Error logs...")
        self.io_tabs.addTab(self.output_text, "Output")

        io_container = QWidget()
        io_layout = QVBoxLayout(io_container)
        io_layout.addWidget(self.io_tabs)
        right_splitter.addWidget(io_container)

    def setup_shortcuts(self):
        """Set up unique keyboard shortcuts."""
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, activated=self.add_new_tab)
        QShortcut(QKeySequence("Ctrl+O"), self, activated=self.open_file)
        QShortcut(QKeySequence("Ctrl+S"), self, activated=self.save_file)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, activated=self.run_code)
        QShortcut(QKeySequence("Ctrl+Shift+D"), self, activated=self.start_debugger)

    def open_file(self):
        """Open a file using a file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Python File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.load_file(file_path)
            self.add_to_recent_files(file_path)

    def load_recent_files(self):
        """Load recent files list from a file."""
        if os.path.exists(self.RECENT_FILES_PATH):
            with open(self.RECENT_FILES_PATH, 'rb') as file:
                return pickle.load(file)
        return []

    def load_file(self, file_path):
        """Load a file's content into a new editor tab."""
        with open(file_path, "r") as file:
            content = file.read()
        new_editor = CodeEditor()
        new_editor.setPlainText(content)
        tab_index = self.tab_widget.addTab(new_editor, os.path.basename(file_path))
        self.tab_widget.setCurrentIndex(tab_index)
        self.statusBar.showMessage(f"Opened: {file_path}", 3000)

    def open_file(self):
        """Open a file using a file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Python File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.load_file(file_path)
            self.add_to_recent_files(file_path)

    def add_new_tab(self):
        """Add a new code editor tab."""
        new_editor = CodeEditor()
        new_editor.setFont(QFont("Courier New", 14))
        tab_index = self.tab_widget.addTab(new_editor, "Untitled")
        self.tab_widget.setCurrentIndex(tab_index)

    def close_tab(self, index):
        """Close a tab, prompting to save if there are unsaved changes."""
        current_editor = self.tab_widget.widget(index)
        if isinstance(current_editor, CodeEditor):
            if current_editor.document().isModified():
                reply = QMessageBox.question(self, 'Unsaved Changes',
                                             "This document has unsaved changes. Do you want to save them?",
                                             QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Save:
                    self.save_file()
                elif reply == QMessageBox.StandardButton.Cancel:
                    return
        self.tab_widget.removeTab(index)

    def highlight_active_tab(self):
        """Highlight the active tab in a distinct color using stylesheets."""
        tab_bar: QTabBar = self.tab_widget.tabBar()
        for index in range(self.tab_widget.count()):
            if index == self.tab_widget.currentIndex():
                # Set active tab style
                tab_bar.setTabTextColor(index, QColor("yellow"))
            else:
                # Set inactive tab style
                tab_bar.setTabTextColor(index, QColor("white"))


    def add_to_recent_files(self, file_path):
        """Add a file path to the recent files list."""
        if not hasattr(self, 'recent_files'):
            self.recent_files = []

        if file_path not in self.recent_files:
            self.recent_files.insert(0, file_path)
            if len(self.recent_files) > self.RECENT_FILES_LIMIT:
                self.recent_files.pop()
            self.save_recent_files()

    def save_recent_files(self):
        """Save the recent files list to a file."""
        with open(self.RECENT_FILES_PATH, 'wb') as file:
            pickle.dump(self.recent_files, file)

    def show_recent_files(self):
        """Show the recent files menu."""
        recent_files_menu = QMenu("Recent Files", self)
        for file_path in self.recent_files:
            recent_file_action = QAction(file_path, self)
            recent_file_action.triggered.connect(lambda checked, path=file_path: self.load_file(path))
            recent_files_menu.addAction(recent_file_action)
        recent_files_menu.exec(self.mapToGlobal(self.toolbar.geometry().topLeft()))

    def open_font_dialog(self):
        """Open a dialog to select font properties and apply them."""
        font, ok = QFontDialog.getFont()
        if ok:
            self.apply_font_settings(font)

    def apply_font_settings(self, font):
        """Apply the selected font to all editor components."""
        for index in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(index)
            if isinstance(editor, CodeEditor):
                editor.setFont(font)

        self.input_field.setFont(font)
        self.output_text.setFont(font)

    def create_new_folder(self):
        """Create a new folder in the current directory."""
        current_index = self.file_explorer.currentIndex()
        current_path = self.file_model.filePath(current_index)

        if os.path.isdir(current_path):
            folder_path = current_path
        else:
            folder_path = os.path.dirname(current_path)

        folder_name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and folder_name:
            new_folder_path = os.path.join(folder_path, folder_name)
            try:
                os.makedirs(new_folder_path)
                self.statusBar.showMessage(f"Created folder: {new_folder_path}", 3000)
                self.file_model.setRootPath(folder_path)
            except Exception as e:
                self.statusBar.showMessage(f"Error creating folder: {e}", 3000)

    def open_file(self):
        """Open a file using a file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Python File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.load_file(file_path)
            self.add_to_recent_files(file_path)

    def open_folder(self):
        """Open a folder and set it as the root for the file explorer."""
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder", "")
        if folder_path:
            self.file_model.setRootPath(folder_path)
            self.file_explorer.setRootIndex(self.file_model.index(folder_path))

    def restore_session(self):
        """Restore the last open session with all tabs and contents."""
        if os.path.exists(self.SESSION_PATH):
            try:
                with open(self.SESSION_PATH, 'r') as session_file:
                    session_data = json.load(session_file)

                    for file_info in session_data.get("open_files", []):
                        content = file_info["content"]
                        file_path = file_info["file_path"]

                        new_editor = CodeEditor()
                        new_editor.setPlainText(content)
                        if file_path:
                            new_editor.file_path = file_path

                        tab_index = self.tab_widget.addTab(new_editor, os.path.basename(file_path) if file_path else "Untitled")
                        self.tab_widget.setCurrentIndex(tab_index)

                    # Restore the current tab
                    self.tab_widget.setCurrentIndex(session_data.get("current_tab_index", 0))

            except Exception as e:
                print(f"Failed to restore session: {str(e)}")

    def autosave(self):
        """Save open tabs periodically to prevent data loss."""
        try:
            session_data = {
                "open_files": [],
                "current_tab_index": self.tab_widget.currentIndex(),
            }

            # Iterate over all open tabs and save content
            for index in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(index)
                if isinstance(editor, CodeEditor):
                    session_data["open_files"].append({
                        "content": editor.toPlainText(),
                        "file_path": editor.file_path if hasattr(editor, "file_path") else None,
                    })

            with open(self.SESSION_PATH, 'w') as session_file:
                json.dump(session_data, session_file)

        except Exception as e:
            print(f"Failed to autosave session: {str(e)}")

    def run_code(self):
        """Run the code from the current editor and show the output tab automatically."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            code = current_editor.toPlainText()
            input_value = self.input_field.text().strip()

            if not code.strip():
                self.statusBar.showMessage("Error: No code to run!", 3000)
                return

            # Run the code using QRunnable for threading
            signals = Signals()
            signals.output_received.connect(self.handle_output)
            signals.error_received.connect(self.handle_error)
            runnable = CodeRunnerRunnable(code, input_value, signals)
            self.thread_pool.start(runnable)

            # Show the output tab automatically
            self.io_tabs.setCurrentIndex(1)

    def start_debugger(self):
        """Start the debugger for the current code."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            code = current_editor.toPlainText()
            if not code.strip():
                self.statusBar.showMessage("Error: No code to debug!", 3000)
                return

            self.debugger_thread = DebuggerThread(code)
            self.debugger_thread.output_received.connect(self.handle_output)
            self.debugger_thread.error_received.connect(self.handle_error)
            self.debugger_thread.start()
            current_editor.set_debugger_thread(self.debugger_thread)

    def continue_debugger(self):
        """Continue the execution in the debugger."""
        if hasattr(self, 'debugger_thread'):
            self.debugger_thread.send_command("continue")

    def step_debugger(self):
        """Step through the code in the debugger."""
        if hasattr(self, 'debugger_thread'):
            self.debugger_thread.send_command("step")

    def open_file_from_explorer(self, index):
        """Open a file from the file explorer."""
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path) and file_path.endswith(".py"):
            self.load_file(file_path)
            self.add_to_recent_files(file_path)

    def save_file(self):
        """Save the current file's content."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, QPlainTextEdit):
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Python File", "", "Python Files (*.py);;All Files (*)")
            if file_path:
                with open(file_path, "w") as file:
                    file.write(current_editor.toPlainText())
                self.add_to_recent_files(file_path)
                self.statusBar.showMessage(f"Saved: {file_path}", 3000)

    def handle_output(self, output):
        """Handle output from the code runner or debugger."""
        self.output_text.appendPlainText(output)

    def handle_error(self, error):
        """Handle errors from the code runner or debugger."""
        self.output_text.appendPlainText(error)

    def load_user_settings(self):
        """Load user settings from a file."""
        if os.path.exists(self.SETTINGS_PATH):
            with open(self.SETTINGS_PATH, 'r') as file:
                settings = json.load(file)
                self.apply_user_settings(settings)

    def apply_user_settings(self, settings):
        """Apply user settings to the UI."""
        if "theme" in settings and settings["theme"] == "dark":
            self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        else:
            self.setStyleSheet("background-color: rgba(255, 255, 255, 0.85); color: black;")

    def save_user_settings(self):
        """Save the current user settings."""
        settings = {"theme": "dark" if self.styleSheet().find("#1e1e1e") != -1 else "light"}
        with open(self.SETTINGS_PATH, 'w') as file:
            json.dump(settings, file)

    def closeEvent(self, event):
        """Handle the event when the window is closed."""
        self.save_user_settings()
        self.autosave()  # Save session when closing
        self.autosave_timer.stop()
        super().closeEvent(event)


# Main entry point
if __name__ == "__main__":
    app = QApplication([])
    main_win = AICompilerMainWindow()
    main_win.show()
    app.exec()
