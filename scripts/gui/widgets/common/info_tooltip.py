from PySide6.QtWidgets import  QToolButton
from PySide6.QtGui import QPixmap, QImage, QIcon, QPainter, QColor
from PySide6.QtCore import Qt


class InfoTooltip(QToolButton):
    '''
    This class constructs a tooltip that is used to display a tooltip with information
    about a certain widget.
    '''


    def __init__(self, configs, tooltip_text, valid: bool=True):
        super(InfoTooltip, self).__init__()
        background_color = configs.get_application_setting('configuration_panel', 'background_color')

        VALID_STYLE = '''
            QLabel {
                margin-bottom:10px;
                margin-left:-30px;
                padding:0px;
            }
            QToolTip {
                border-radius: 5px;
                padding: 0px;
                max-width: 200px;
            }
            QToolButton {
                background-color: %s;
                opacity: 1;
                position:aboslute;
                right:0px;
                border:0px;
            }
            ''' % background_color
        
        INVALID_STYLE = '''
            QLabel {
                margin-bottom:10px;
                margin-left:-30px;
                padding:0px;
            }
            QToolTip {
                border-radius: 5px;
                padding: 0px;
                max-width: 200px;
            }
            QToolButton {
                background-color: %s;
                opacity: 1;
                position:aboslute;
                right:0px;
                border:0px;
            }
            ''' % background_color
        

        if valid:
            self.setStyleSheet(VALID_STYLE)
        else:
            self.setStyleSheet(INVALID_STYLE)
        self.configs = configs
        icon_image_path = configs.get_application_setting('tooltip', 'icon_image_path')
        icon_image = QImage(icon_image_path)
        self.pixmap = QPixmap(icon_image).scaled(15, 15, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.icon = QIcon() 
        self.icon.addPixmap(self.pixmap)
        
        self.setIcon(self.icon) 

        self.setToolTip("<FONT >" + tooltip_text + "</FONT>") 

        self.hoverIcon = QIcon()
        self.painter = QPainter(self.pixmap)
        self.painter.device() 
        self.painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        hover_color = configs.get_application_setting('tooltip', 'hover_color')
        self.painter.setBrush(QColor(hover_color))
        self.painter.setPen(QColor(hover_color))
        self.painter.drawRect(self.pixmap.rect())
        self.hoverIcon.addPixmap(self.pixmap)     
        self.painter.end() 


    #do something on hover
    def enterEvent(self, event):
        self.setIcon(self.hoverIcon)
        super(InfoTooltip, self).enterEvent(event)


    #do something when not hovering
    def leaveEvent(self, event):
        self.setIcon(self.icon)
        super(InfoTooltip, self).leaveEvent(event)


    # def set_valid(self, valid:bool=True) -> None:
    #     """Updates the style for this tooltip to indicate
    #     whether it is valid or not.

    #     TODO: fix
    #     """
    #     if valid:
    #         self.setStyleSheet(VALID_STYLE)
    #         icon_color = 'black'

    #     else:
    #         self.setStyleSheet(INVALID_STYLE)
    #         icon_color = 'red'

    #     painter = QPainter(self.pixmap)
    #     painter.device() 
    #     painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    #     # hover_color = configs.get_application_setting('tooltip', 'hover_color')
    #     painter.setBrush(QColor(icon_color))
    #     painter.setPen(QColor(icon_color))
    #     painter.drawRect(self.pixmap.rect())
    #     self.icon.addPixmap(self.pixmap)     
    #     self.painter.end() 

    def set_tooltip_text(self, tooltip_text: str) -> None:
        """Sets the tooltip text

        Args:
            tooltip_text (str): the tooltip text
        """
        pass
        # self.setToolTip("<FONT >" + tooltip_text + "</FONT>")
