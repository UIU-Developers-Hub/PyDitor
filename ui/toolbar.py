from PyQt6.QtWidgets import QToolBar, QFileDialog, QPlainTextEdit
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt


class Toolbar(QToolBar):
    def __init__(self, parent):
        super().__init__("Toolbar", parent)
        self.parent = parent
        self.setMovable(False)
        self.create_toolbar_buttons()

    def create_toolbar_buttons(self):
        # Open File Button
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.parent.open_file)
        self.addAction(open_action)

        # Save File Button
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.parent.save_file)
        self.addAction(save_action)

        # Run Code Button
        run_action = QAction("Run", self)
        run_action.triggered.connect(self.parent.run_code)
        self.addAction(run_action)

        # New Tab Button
        new_tab_action = QAction("New Tab", self)
        new_tab_action.triggered.connect(self.parent.add_new_tab)
        self.addAction(new_tab_action)
