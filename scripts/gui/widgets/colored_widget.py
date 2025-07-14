from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QWidget


class ColoredWidget(QWidget):

    def __init__(self, color):
        super(ColoredWidget, self).__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)