from PySide6.QtWidgets import QScrollArea
from PySide6.QtCore import Qt

class StyledScrollArea(QScrollArea):
    def __init__(self, widget=None):
        super(StyledScrollArea, self).__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet('''
            QScrollArea {
                border-radius: 5px;
                border: 0px solid red;
                background-color: transparent;
                padding: 0px;
                margin: 0px;               
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
                margin: 0px;
                padding: 0px;
            }
        ''')
        self.setWidgetResizable(True)
        if not widget is None:
            self.setWidget(widget)
        