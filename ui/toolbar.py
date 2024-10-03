# File: ui/toolbar.py

from PyQt6.QtWidgets import QToolBar, QMenu, QFileDialog, QInputDialog
from PyQt6.QtGui import QAction, QIcon  # Correct import for QAction from PyQt6.QtGui
from PyQt6.QtCore import Qt

class Toolbar(QToolBar):
    def __init__(self, parent):
        super().__init__("Toolbar", parent)
        self.parent = parent
        self.setMovable(False)
        self.setStyleSheet("""
            QToolBar {
                spacing: 15px; /* Spacing between buttons */
                background-color: #2e2e2e; /* Darker background color for toolbar */
                padding: 5px; /* Padding around the toolbar */
            }
            QToolButton {
                margin: 5px; /* Space around the buttons */
                padding: 5px; /* Padding within the buttons */
                color: white; /* Text color for the buttons */
                background-color: #3c3c3c; /* Button background */
                border-radius: 4px; /* Rounded corners for buttons */
                border: 1px solid #444444; /* Slight border for definition */
            }
            QToolButton:hover {
                background-color: #505050; /* Hover effect */
            }
            QToolButton:pressed {
                background-color: #707070; /* Pressed button effect */
            }
        """)
        self.create_toolbar_buttons()

    def create_toolbar_buttons(self):
        # File Menu Button
        file_menu_action = QMenu("File", self)

        # Create New File
        new_file_action = QAction("New File", self)
        new_file_action.setShortcut("Ctrl+N")
        new_file_action.triggered.connect(self.parent.add_new_tab)
        file_menu_action.addAction(new_file_action)

        # Open File
        open_file_action = QAction("Open File", self)
        open_file_action.setShortcut("Ctrl+O")
        open_file_action.triggered.connect(self.parent.open_file)
        file_menu_action.addAction(open_file_action)

        # Create New Folder
        new_folder_action = QAction("New Folder", self)
        new_folder_action.setShortcut("Ctrl+Shift+N")
        new_folder_action.triggered.connect(self.parent.create_new_folder)
        file_menu_action.addAction(new_folder_action)

        # Open Folder
        open_folder_action = QAction("Open Folder", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(self.parent.open_folder)
        file_menu_action.addAction(open_folder_action)

        # Recently Opened Files
        recent_files_action = QAction("Recently Opened", self)
        recent_files_action.triggered.connect(self.parent.show_recent_files)
        file_menu_action.addAction(recent_files_action)

        # Add File Menu Button to Toolbar
        self.addAction(file_menu_action.menuAction())

        # Run Button
        run_action = QAction("Run Code", self)
        run_action.setShortcut("Ctrl+R")
        run_action.triggered.connect(self.parent.run_code)
        self.addAction(run_action)

        # Separator for better UI grouping
        self.addSeparator()

        # Font Settings Dropdown
        font_menu_action = QMenu("Font Settings", self)

        # Font Size Options
        font_size_menu = QMenu("Font Size", self)
        for size in [10, 12, 14, 16, 18, 20]:
            font_size_action = QAction(f"{size} pt", self)
            font_size_action.triggered.connect(lambda checked, s=size: self.parent.set_font_size(s))
            font_size_menu.addAction(font_size_action)
        font_menu_action.addMenu(font_size_menu)

        # Font Family Options
        font_family_menu = QMenu("Font Family", self)
        for family in ["Courier New", "Arial", "Times New Roman", "Verdana"]:
            font_family_action = QAction(family, self)
            font_family_action.triggered.connect(lambda checked, f=family: self.parent.set_font_family(f))
            font_family_menu.addAction(font_family_action)
        font_menu_action.addMenu(font_family_menu)

        # Add Font Settings Dropdown to Toolbar
        self.addAction(font_menu_action.menuAction())

        # New Tab Button
        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(self.parent.add_new_tab)
        self.addAction(new_tab_action)

        # Separator for better UI grouping
        self.addSeparator()
