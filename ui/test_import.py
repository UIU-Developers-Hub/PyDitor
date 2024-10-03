from PyQt6.QtWidgets import QApplication, QMainWindow, QAction, QToolBar
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Import")
        self.setGeometry(100, 100, 400, 300)

        toolbar = QToolBar("My Toolbar")
        self.addToolBar(toolbar)

        action = QAction("Exit", self)
        action.triggered.connect(self.close)
        toolbar.addAction(action)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
