from PyQt6.QtWidgets import QApplication
from .gui import FPSDemo
import sys

def main():
    app = QApplication(sys.argv)
    w = FPSDemo()
    w.show()
    w.update_center_global()
    w.recenter_mouse()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
