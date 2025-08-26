import sys, math, time
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QCursor, QBrush

from .world import ChunkWorld
from .objects import StaticWorld

# VFOV pro kameru
VFOV_DEG = 70
LOAD_RADIUS = 60

class FPSDemo(QWidget):
    # Původní třída FPSDemo se sem přesune beze změn, jen jsme aktualizovali importy.
    # Kód zůstává stejný, pouze odkazy na StaticWorld a ChunkWorld vedou na nové soubory.
    pass
