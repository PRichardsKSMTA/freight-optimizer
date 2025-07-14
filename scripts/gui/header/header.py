from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

from ..widgets import colored_widget
from ..widgets.common import styled_label
from ..widgets.common import styled_hbox_layout

class Header(colored_widget.ColoredWidget):
    '''
    This class constructs the header for the optimization GUI. The header
    contains a brief description of the app + a logo.   
    '''

    def __init__(self, configs):
        super(Header, self).__init__(configs.get_application_setting('header', 'header_color'))
        
        self.configs = configs
        height = self.configs.get_application_setting('header', 'height')
        self.setMaximumHeight(height)

        layout = styled_hbox_layout.StyledHBoxLayout()  
        layout.addWidget(styled_label.StyledLabel(configs.get_application_setting('header', 'title'), app_configs=configs, label_type='header'))
        layout.addStretch()
        label = QLabel(self)
        header_image_path = configs.get_application_setting('header', 'header_image_path')
        header_image = QImage(header_image_path)
        pixmap = QPixmap(header_image).scaled(height, height*2, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label.setPixmap(pixmap)
        layout.addWidget(label)


        self.setLayout(layout)
