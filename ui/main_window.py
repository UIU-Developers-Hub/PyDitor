# File: ui/main_window.py

import os
import pickle
import re
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QPlainTextEdit, QFileDialog,
    QVBoxLayout, QWidget, QHBoxLayout, QSplitter,
    QTreeView, QLineEdit, QStatusBar, QDockWidget, QApplication, QMenu, QInputDialog
)
from PyQt6.QtGui import QFont, QColor, QAction
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFileSystemModel
from .toolbar import Toolbar
from runner.code_runner_thread import CodeRunnerThread
from .documentation_sidebar import DocumentationSidebar
from .code_editor import CodeEditor


class AICompilerMainWindow(QMainWindow):
    RECENT_FILES_LIMIT = 5
    RECENT_FILES_PATH = "recent_files.pkl"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Data Science Code Visualization")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")

        # Load recent files
        self.recent_files = self.load_recent_files()

        # Initialize Toolbar
        self.toolbar = Toolbar(self)
        self.addToolBar(self.toolbar)

        # Initialize documentation sidebar
        self.documentation_sidebar = DocumentationSidebar()
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.documentation_sidebar)

        # File Explorer
        self.file_explorer = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath('')
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
        left_splitter.setSizes([200, 800])

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(left_splitter)
        self.setCentralWidget(central_widget)

        # Create a tab for Input and Output
        self.io_tabs = QTabWidget()
        self.io_tabs.setTabsClosable(False)
        self.io_tabs.currentChanged.connect(self.update_active_tab_style)

        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("background-color: #1e1e1e; color: #abb2bf;")
        self.input_field.setPlaceholderText("Input for the script...")
        self.io_tabs.addTab(self.input_field, "Input")

        self.output_text = QPlainTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color: #1e1e1e; color: #abb2bf;")
        self.output_text.setPlaceholderText("Output/Error logs...")
        self.io_tabs.addTab(self.output_text, "Output")

        io_container = QWidget()
        io_layout = QVBoxLayout(io_container)
        io_layout.addWidget(self.io_tabs)

        # Add the IO container to the right splitter
        right_splitter.addWidget(io_container)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

    # Font Handling Methods

    def set_font_size(self, size):
        """Set the font size in the current editor."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_font = current_editor.font()
            current_font.setPointSize(size)
            current_editor.setFont(current_font)

    def set_font_family(self, family):
        """Set the font family in the current editor."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_font = current_editor.font()
            current_font.setFamily(family)
            current_editor.setFont(current_font)

    def increase_font_size(self):
        """Increase the font size in the current editor."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_font = current_editor.font()
            new_size = current_font.pointSize() + 1
            current_font.setPointSize(new_size)
            current_editor.setFont(current_font)

    def decrease_font_size(self):
        """Decrease the font size in the current editor."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_font = current_editor.font()
            new_size = max(current_font.pointSize() - 1, 1)  # Prevent size going below 1
            current_font.setPointSize(new_size)
            current_editor.setFont(current_font)

    def change_font_family(self):
        """Change the font family in the current editor (toggle between two)."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            current_font = current_editor.font()
            new_family = "Courier New" if current_font.family() != "Courier New" else "Arial"
            current_font.setFamily(new_family)
            current_editor.setFont(current_font)

    # File Handling Methods

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder", "")
        if folder_path:
            self.file_model.setRootPath(folder_path)
            self.file_explorer.setRootIndex(self.file_model.index(folder_path))

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Python File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.open_file_from_path(file_path)
            self.add_to_recent_files(file_path)

    def open_file_from_explorer(self, index):
        file_path = self.file_model.filePath(index)
        if file_path.endswith(".py"):
            self.open_file_from_path(file_path)
            self.add_to_recent_files(file_path)

    def open_file_from_path(self, file_path):
        with open(file_path, "r") as file:
            content = file.read()
        new_editor = CodeEditor()
        new_editor.setPlainText(content)
        tab_index = self.tab_widget.addTab(new_editor, os.path.basename(file_path))
        self.tab_widget.setCurrentIndex(tab_index)
        self.statusBar.showMessage(f"Opened: {file_path}", 3000)

    def save_file(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, QPlainTextEdit):
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Python File", "", "Python Files (*.py);;All Files (*)")
            if file_path:
                with open(file_path, "w") as file:
                    file.write(current_editor.toPlainText())
                self.add_to_recent_files(file_path)
                self.statusBar.showMessage(f"Saved: {file_path}", 3000)

    def create_new_folder(self):
        """Create a new folder in the current directory of the file explorer."""
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
                self.file_model.setRootPath(folder_path)  # Refresh file explorer
            except Exception as e:
                self.statusBar.showMessage(f"Error creating folder: {e}", 3000)

    # Code Running and Linting Methods

    def run_code(self):
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            code = current_editor.toPlainText()
            input_value = self.input_field.text().strip()

            if not code.strip():
                self.statusBar.showMessage("Error: No code to run!", 3000)
                return

            # Run linting before executing code
            current_editor.lint_code()

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

    # Recent File Handling Methods

    def show_recent_files(self):
        recent_files_menu = QMenu("Recent Files", self)
        for file_path in self.recent_files:
            recent_file_action = QAction(file_path, self)
            recent_file_action.triggered.connect(lambda checked, path=file_path: self.open_file_from_path(path))
            recent_files_menu.addAction(recent_file_action)
        recent_files_menu.exec(self.mapToGlobal(self.toolbar.geometry().topLeft()))

    def add_to_recent_files(self, file_path):
        if file_path not in self.recent_files:
            self.recent_files.insert(0, file_path)
            if len(self.recent_files) > self.RECENT_FILES_LIMIT:
                self.recent_files.pop()
            self.save_recent_files()

    def load_recent_files(self):
        if os.path.exists(self.RECENT_FILES_PATH):
            with open(self.RECENT_FILES_PATH, 'rb') as file:
                return pickle.load(file)
        return []

    def save_recent_files(self):
        with open(self.RECENT_FILES_PATH, 'wb') as file:
            pickle.dump(self.recent_files, file)

    # Utility Methods

    def add_new_tab(self):
        new_editor = CodeEditor()
        new_editor.setFont(QFont("monospace", 12))
        tab_index = self.tab_widget.addTab(new_editor, "Untitled")
        self.tab_widget.setCurrentIndex(tab_index)

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

    def update_active_tab_style(self):
        for i in range(self.io_tabs.count()):
            if i == self.io_tabs.currentIndex():
                self.io_tabs.tabBar().setTabTextColor(i, QColor("lightgreen"))  # Highlight active tab
            else:
                self.io_tabs.tabBar().setTabTextColor(i, QColor("white"))  # Reset to default color


# Main entry point
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = AICompilerMainWindow()
    main_win.show()
    sys.exit(app.exec())
