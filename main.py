# main.py

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import AICompilerMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = AICompilerMainWindow()
    main_win.show()
    sys.exit(app.exec())
