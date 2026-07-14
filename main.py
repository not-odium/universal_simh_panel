import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
from ui.main_window import MainWindow
from ui.themes import DARK_THEME

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_THEME)
    app.setFont(QFont("Segoe UI", 9))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
