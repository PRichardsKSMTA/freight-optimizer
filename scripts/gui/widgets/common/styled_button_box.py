from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

from .styled_hbox_layout import StyledHBoxLayout

class StyledButtonBox(QWidget):
    '''
    This is a widget that contains a horizontal layout for buttons
    '''
    def __init__(self):
        super(StyledButtonBox, self).__init__()
        self._setup_ui()

    def _setup_ui(self):
        #create a horizontal layout and add it to the widget
        self.layout = StyledHBoxLayout()
        self.setLayout(self.layout)

    def add_button(self, button):
        #adds a button to the layout
        self.layout.addWidget(button, Qt.AlignCenter)
        