# main_window.py

import sys
import os
import json
import logging
from PyQt6.QtCore import QTimer, QThread
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QPlainTextEdit, QFileDialog,
    QVBoxLayout, QWidget, QHBoxLayout, QSplitter, QTreeView,
    QLineEdit, QStatusBar, QDockWidget, QApplication, QMenu, 
    QInputDialog, QMessageBox, QToolBar, QFontDialog, QTextEdit
)
from PyQt6.QtGui import QFont, QAction, QShortcut, QKeySequence, QFileSystemModel, QTextCursor
from PyQt6.QtCore import Qt, QThreadPool

from ui.toolbar import Toolbar
from core.code_runner_thread import CodeRunnerThread, Signals
from ui.documentation_sidebar import DocumentationSidebar
from ui.code_editor import CodeEditor
from core.debugger_thread import DebuggerThread

# Set Jedi's log level to suppress debug messages
logging.getLogger('jedi').setLevel(logging.INFO)

class AICompilerMainWindow(QMainWindow):
    RECENT_FILES_LIMIT = 5
    RECENT_FILES_PATH = "recent_files.json"
    SETTINGS_PATH = "user_settings.json"
    SESSION_PATH = "last_session.json"

    def __init__(self):
        super().__init__()

        # Create the main widget and layout
        main_widget = QWidget()
        layout = QVBoxLayout()

        # Create and add the CodeEditor to the layout
        self.editor = CodeEditor()
        layout.addWidget(self.editor)

        # Set the layout and the central widget
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        self.setWindowTitle("Python IDE")

        self.thread_pool = ThreadPoolExecutor(max_workers=5)
        self.threads = []
        self.previous_tab_index = None
        self.modified_tabs = set()
        self.unsaved_tab_open = False
        self.tab_process_map = {}

        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

        self.setup_ui()
        self.setup_shortcuts()
        self.restore_session()

    def setup_ui(self):
        self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        self.recent_files = self.load_recent_files()

        # Initialize Toolbar
        self.toolbar = Toolbar(self)
        self.addToolBar(self.toolbar)

        # Add the Batch Test button to the toolbar
        self.batch_test_action = QAction("Batch Test", self)
        self.batch_test_action.triggered.connect(self.run_batch_test)
        self.toolbar.addAction(self.batch_test_action)

        # Add Debugger Controls
        self.debugger_toolbar = QToolBar("Debugger", self)
        self.addToolBar(self.debugger_toolbar)

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
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Add an initial tab
        self.add_new_tab()

        # Layout for the right-hand side splitter
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        right_splitter.addWidget(self.tab_widget)
        left_splitter.addWidget(right_splitter)

        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.addWidget(left_splitter)
        self.setCentralWidget(central_widget)

        self.setup_io_tabs(right_splitter)

        # Initialize and set the QStatusBar
        self.setStatusBar(QStatusBar())

    def setup_io_tabs(self, right_splitter):
        """Set up Input/Output tabs in the right splitter."""
        self.io_tabs = QTabWidget()
        self.io_tabs.setTabsClosable(False)

        # Input field setup
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("background-color: #2e2e2e; color: #abb2bf; padding: 10px;")
        self.input_field.setPlaceholderText("Input for the script...")
        self.io_tabs.addTab(self.input_field, "Input")

        # Output field setup using QPlainTextEdit
        self.output_text = QTextEdit()  # Changed from QTextEdit
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color: #2e2e2e; color: #abb2bf; padding: 10px;")
        self.output_text.setPlaceholderText("Output/Error logs...")
        self.io_tabs.addTab(self.output_text, "Output")

        # Container and layout setup
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
        QShortcut(QKeySequence("Ctrl+T"), self, activated=self.run_tests)

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
                        new_editor.file_path = file_path
                        tab_index = self.tab_widget.addTab(new_editor, os.path.basename(file_path) if file_path else "Untitled")
                        self.tab_widget.setCurrentIndex(tab_index)

                    self.tab_widget.setCurrentIndex(session_data.get("current_tab_index", 0))

            except Exception as e:
                print(f"Failed to restore session: {str(e)}")

    def add_new_tab(self):
        """Add a new code editor tab."""
        if self.unsaved_tab_open:
            self.statusBar().showMessage("Error: Please save your current file before opening a new one!", 5000)
            return

        new_editor = CodeEditor()
        new_editor.file_path = None
        new_editor.setFont(QFont("Courier New", 14))
        tab_index = self.tab_widget.addTab(new_editor, "Untitled")
        self.tab_widget.setCurrentIndex(tab_index)

        self.unsaved_tab_open = True
        self.statusBar().showMessage("New tab opened. Please save your work before creating a new tab.", 5000)

    def close_tab(self, index):
        """Close a tab and ensure proper cleanup."""
        current_editor = self.tab_widget.widget(index)
        if isinstance(current_editor, CodeEditor):
            if current_editor.document().isModified() or current_editor.file_path is None:
                reply = QMessageBox.question(self, 'Unsaved Changes', 
                                             "This document has unsaved changes. Do you want to save them?", 
                                             QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Save:
                    if not self.save_file():
                        return  # If saving fails, do not close the tab
                elif reply == QMessageBox.StandardButton.Cancel:
                    return  # User canceled the operation

        if current_editor.file_path is None:
            self.unsaved_tab_open = False

        self.cleanup_tab_process(index)
        self.tab_widget.removeTab(index)

    def cleanup_tab_process(self, index):
        """Terminate and cleanup any process or temp file associated with a tab."""
        if index in self.tab_process_map:
            process, temp_file = self.tab_process_map[index]

            if process and process.poll() is None:
                process.terminate()
                try:
                    process.wait(3)
                except subprocess.TimeoutExpired:
                    process.kill()

            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    logging.error(f"Failed to delete temp file '{temp_file}': {e}")

            del self.tab_process_map[index]

    def run_code(self):
        """Run the code from the current editor and show the output tab automatically."""
        current_editor = self.tab_widget.currentWidget()

        if isinstance(current_editor, CodeEditor):
            if not current_editor.file_path:
                self.statusBar().showMessage("Error: Please save the file before running.", 5000)
                reply = QMessageBox.warning(self, 'Save File',
                                            "The file is not saved. Do you want to save it before running?",
                                            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Save:
                    if not self.save_file():
                        return  # If saving fails
                else:
                    return  # User cancels the run
            elif current_editor.document().isModified():
                reply = QMessageBox.warning(self, 'Unsaved Changes',
                                            "The file has unsaved changes. Do you want to save them before running?",
                                            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Cancel)
                if reply == QMessageBox.StandardButton.Save:
                    if not self.save_file():
                        return  # If saving fails
                else:
                    return  # User cancels the run

            file_path = current_editor.file_path
            self.statusBar().showMessage(f"Running: {file_path}", 3000)

            # Clear previous output before running
            self.output_text.clear()

            # Switch to the "Output" tab automatically
            self.io_tabs.setCurrentIndex(1)

            signals = Signals()
            signals.output_received.connect(self.handle_output)
            signals.error_received.connect(self.handle_error)

            runnable = CodeRunnerThread(file_path, self.input_field.text().strip(), signals)
            self.thread_pool.submit(runnable.run)

    def run_tests(self):
        """Run unit tests from the current editor."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            code = current_editor.toPlainText()

            if not code.strip():
                self.statusBar().showMessage("Error: No tests to run!", 3000)
                return

            signals = Signals()
            signals.output_received.connect(self.handle_output)
            signals.error_received.connect(self.handle_error)

            test_runnable = CodeRunnerThread(code, "", signals)
            self.thread_pool.submit(test_runnable.run)

            self.io_tabs.setCurrentIndex(1)

    def handle_output(self, output):
        """Handle the output received from running the tests or code."""
        self.append_output(output)

    def handle_error(self, error):
        """Handle the error received from running the tests or code."""
        self.append_output(error)

    def open_file(self):
        """Open a file using a file dialog."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Python File", "", "Python Files (*.py);;All Files (*)")
        if file_path:
            self.load_file(file_path)
            self.add_to_recent_files(file_path)

    def load_recent_files(self):
        """Load recent files list from a JSON file."""
        if os.path.exists(self.RECENT_FILES_PATH):
            try:
                with open(self.RECENT_FILES_PATH, 'r') as file:
                    return json.load(file)
            except json.JSONDecodeError as e:
                logging.error(f"Error loading recent files: {str(e)}")
                return []
        return []

    def load_file(self, file_path):
        """Load a file's content into a new editor tab."""
        with open(file_path, "r") as file:
            content = file.read()
        new_editor = CodeEditor()
        new_editor.setPlainText(content)
        new_editor.file_path = file_path
        tab_index = self.tab_widget.addTab(new_editor, os.path.basename(file_path))
        self.tab_widget.setCurrentIndex(tab_index)
        self.statusBar().showMessage(f"Opened: {file_path}", 3000)

    def save_file(self):
        """Save the current file's content."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            if current_editor.file_path is None:
                file_path, _ = QFileDialog.getSaveFileName(self, "Save Python File", "", "Python Files (*.py);;All Files (*)")
                if file_path:
                    current_editor.file_path = file_path
                else:
                    self.statusBar().showMessage("Error: File not saved.", 5000)
                    return False

            try:
                with open(current_editor.file_path, "w") as file:
                    file.write(current_editor.toPlainText())
                self.add_to_recent_files(current_editor.file_path)
                self.statusBar().showMessage(f"Saved: {current_editor.file_path}", 3000)
                current_editor.document().setModified(False)
                return True
            except Exception as e:
                self.statusBar().showMessage(f"Error saving {current_editor.file_path}: {str(e)}", 5000)
                return False

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
        """Save the recent files list to a JSON file."""
        with open(self.RECENT_FILES_PATH, 'w') as file:
            json.dump(self.recent_files, file)

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
                self.statusBar().showMessage(f"Created folder: {new_folder_path}", 3000)
                self.file_model.setRootPath(folder_path)
            except Exception as e:
                self.statusBar().showMessage(f"Error creating folder: {e}", 3000)

    def open_folder(self):
        """Open a folder and set it as the root for the file explorer."""
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder", "")
        if folder_path:
            self.file_model.setRootPath(folder_path)
            self.file_explorer.setRootIndex(self.file_model.index(folder_path))

    def on_tab_changed(self, index):
        """Handle actions when a tab changes."""
        if self.previous_tab_index is not None and self.previous_tab_index != index:
            current_editor = self.tab_widget.widget(self.previous_tab_index)
            if isinstance(current_editor, CodeEditor) and current_editor.document().isModified():
                self.save_file()

        self.previous_tab_index = index

    def start_debugger(self):
        """Start the debugger for the current code."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            code = current_editor.toPlainText()
            if not code.strip():
                self.statusBar().showMessage("Error: No code to debug!", 3000)
                return

            # Clear previous output before starting the debugger
            self.output_text.clear()

            # Switch to the "Output" tab automatically
            self.io_tabs.setCurrentIndex(1)

            # Check if a previous debugger thread is running and stop it
            if hasattr(self, 'debugger_thread') and self.debugger_thread.isRunning():
                self.debugger_thread.terminate()
                self.debugger_thread.wait()

            # Start the DebuggerThread
            self.debugger_thread = DebuggerThread(code)
            self.debugger_thread.output_received.connect(self.handle_output)
            self.debugger_thread.error_received.connect(self.handle_error)
            self.debugger_thread.start()
            logging.info("Debugger started for new code session")

    def handle_output(self, output):
        """Handle the output received from running the tests or code."""
        self.append_output(output)

    def handle_error(self, error):
        """Handle the error received from running the tests or code."""
        self.append_output(error)

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

    def closeEvent(self, event):
        """Ensure all threads are stopped before closing the application."""
        self.thread_pool.shutdown(wait=True)  # Safely stop the thread pool

        # Ensure lint and other QThreads are terminated properly
        for thread in self.findChildren(QThread):
            if thread.isRunning():
                thread.quit()
                thread.wait()

        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            if hasattr(current_editor, 'lint_worker') and current_editor.lint_worker.isRunning():
                current_editor.lint_worker.terminate()
                current_editor.lint_worker.wait()
            elif hasattr(current_editor, 'lint_timer'):
                current_editor.lint_timer.stop()

        event.accept()  # Call the parent class to complete closing

    def save_session(self):
        """Save the current session state."""
        session_data = {
            "open_files": [],
            "current_tab_index": self.tab_widget.currentIndex()
        }

        for i in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(i)
            if isinstance(editor, CodeEditor):
                session_data["open_files"].append({
                    "file_path": editor.file_path,
                    "content": editor.toPlainText()
                })

        with open(self.SESSION_PATH, 'w') as session_file:
            json.dump(session_data, session_file)

    def insert_snippet(self, code_snippet):
        """Insert the provided code snippet into the current editor."""
        current_editor = self.tab_widget.currentWidget()
        if isinstance(current_editor, CodeEditor):
            cursor = current_editor.textCursor()
            cursor.insertText(code_snippet)
            self.statusBar().showMessage("Snippet inserted", 3000)
        else:
            self.statusBar().showMessage("Error: No active code editor to insert the snippet.", 5000)

    def run_batch_test(self):
        """
        Open a file dialog to choose the batch test file and run batch tests.
        """
        input_file, _ = QFileDialog.getOpenFileName(self, "Open Batch Test File", "", "Text Files (*.txt);;All Files (*)")

        if input_file:
            # You can replace 'self.sample_function' with any function you want to test
            self.batch_test(self.sample_function, input_file)

    def batch_test(self, function, input_file_path):
        """
        Function to run batch tests for any provided function.
        
        Parameters:
        function (callable): The function to test, it will be called with arguments from the input file.
        input_file_path (str): Path to the input file containing test cases.
        """
        try:
            # Open the input file and read test cases
            with open(input_file_path, 'r') as file:
                test_cases = file.readlines()

            if not test_cases:
                self.statusBar().showMessage("No test cases found in the file.", 5000)
                return

            results = []
            print("Running batch tests...\n")

            # Process each test case
            for i, case in enumerate(test_cases):
                # Split the test case string into arguments (assuming space-separated arguments)
                args = case.strip().split()

                # Convert arguments to integers (or another type depending on the function)
                try:
                    args = [int(arg) for arg in args]
                except ValueError:
                    self.output_text.appendPlainText(f"Test case {i+1}: Invalid input format: {case.strip()}")
                    continue

                try:
                    # Apply the function and collect the result
                    result = function(*args)
                    results.append(f"Test case {i+1}: Input: {args} -> Output: {result}")
                except Exception as e:
                    results.append(f"Test case {i+1}: Input: {args} -> Error: {e}")

                # Display the result in the output pane
                self.output_text.appendPlainText(results[-1])

        except FileNotFoundError:
            self.statusBar().showMessage(f"Error: The file '{input_file_path}' does not exist.", 5000)
        except Exception as e:
            self.statusBar().showMessage(f"An error occurred: {e}", 5000)

    # Sample function for batch testing
    def sample_function(self, *args):
        """ A sample function that takes arguments and returns their sum. """
        return sum(args)

    def append_output(self, output):
        """Append text to the output field."""
        self.output_text.moveCursor(QTextCursor.End)  # Move cursor to the end
        self.output_text.insertPlainText(output)  # Insert text at the cursor position
        self.output_text.moveCursor(QTextCursor.End)  # Ensure cursor remains at the end


if __name__ == "__main__":
    app = QApplication([])
    main_win = AICompilerMainWindow()
    main_win.show()
    app.exec()

