from PyQt6.QtWidgets import QToolBar, QMenu, QFileDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt

class Toolbar(QToolBar):
    def __init__(self, parent):
        super().__init__("Toolbar", parent)
        self.parent_widget = parent  # Store a reference to the parent (AICompilerMainWindow)
        self.setMovable(False)

        # Toolbar styling
        self.setStyleSheet("""
            QToolBar {
                spacing: 15px;
                background-color: #2e2e2e;
                padding: 5px;
            }
            QToolButton {
                margin: 5px;
                padding: 5px;
                color: white;
                background-color: #3c3c3c;
                border-radius: 4px;
                border: 1px solid #444444;
            }
            QToolButton:hover {
                background-color: #505050;
            }
            QToolButton:pressed {
                background-color: #707070;
            }
        """)

        self.create_toolbar_buttons()

    def create_toolbar_buttons(self):
        # File Menu Button
        file_menu_action = QMenu("File", self)

        # Create New File
        new_file_action = QAction("New File", self)
        new_file_action.setShortcut("Ctrl+N")
        new_file_action.triggered.connect(self.parent_widget.add_new_tab)
        file_menu_action.addAction(new_file_action)

        # Open File
        open_file_action = QAction("Open File", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.triggered.connect(self.parent_widget.open_file)
        file_menu_action.addAction(open_file_action)

        # Create New Folder
        new_folder_action = QAction("New Folder", self)
        new_folder_action.setShortcut("Ctrl+Shift+N")
        new_folder_action.triggered.connect(self.parent_widget.create_new_folder)
        file_menu_action.addAction(new_folder_action)

        # Open Folder
        open_folder_action = QAction("Open Folder", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(self.parent_widget.open_folder)
        file_menu_action.addAction(open_folder_action)

        # Recently Opened Files
        recent_files_action = QAction("Recently Opened", self)
        recent_files_action.triggered.connect(self.parent_widget.show_recent_files)
        file_menu_action.addAction(recent_files_action)

        # Add File Menu Button to Toolbar
        self.addAction(file_menu_action.menuAction())

        # Add "Run Code" Button (for running the script in the editor)
        run_code_action = QAction("Run Script", self)
        run_code_action.setShortcut("Ctrl+Shift+R")
        run_code_action.triggered.connect(self.parent_widget.run_code)
        self.addAction(run_code_action)

        # Add "Run Tests" Button (for running unit tests)
        run_tests_action = QAction("Run Unit Tests", self)
        run_tests_action.setShortcut("Ctrl+T")
        run_tests_action.triggered.connect(self.parent_widget.run_tests)
        self.addAction(run_tests_action)

        # Debugger Button
        debug_action = QAction("Start Debugger", self)
        debug_action.setShortcut("Ctrl+Shift+D")
        debug_action.triggered.connect(self.parent_widget.start_debugger)
        self.addAction(debug_action)

        # Separator for better UI grouping
        self.addSeparator()

        # Snippets Dropdown
        snippets_menu = QMenu("Snippets", self)
        snippets = {
            "For Loop": "for i in range(10):\n    print(i)",
            "Class Definition": "class MyClass:\n    def __init__(self):\n        pass",
            "Function Definition": "def my_function():\n    pass",
            "If Statement": "if condition:\n    pass",
        }

        for snippet_name, snippet_code in snippets.items():
            snippet_action = QAction(snippet_name, self)
            snippet_action.triggered.connect(lambda checked, code=snippet_code: self.parent_widget.insert_snippet(code))
            snippets_menu.addAction(snippet_action)

        # Add snippets dropdown to toolbar
        self.addAction(snippets_menu.menuAction())

        # Separator for better UI grouping
        self.addSeparator()

        # Add New Tab Button
        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(self.parent_widget.add_new_tab)
        self.addAction(new_tab_action)

        # Add Font Settings as QAction
        font_settings_action = QAction("Font Settings", self)
        font_settings_action.setShortcut("Ctrl+Shift+F")
        font_settings_action.triggered.connect(self.parent_widget.open_font_dialog)
        self.addAction(font_settings_action)
