
import os
LOADING_ICON = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'loading.gif')

from PySide6.QtWidgets import QDialog, QLabel
from PySide6.QtWidgets import QLabel

from gui.widgets.common.styled_vbox_layout import StyledVBoxLayout


class Label(QLabel):
    '''
    This is the label that will be displayed in the loading window.
    '''
    def __init__(self, app_configs):
        settings = app_configs.get_application_setting('loading_dialog')
        super(Label, self).__init__(settings['label'])
        
        self.setStyleSheet('''
            QLabel {
                font-family: %s;
                font-size: %spx;
                font-weight: %s;
                color: %s;
                background-color: None;
                border-radius: 5px;
                padding: 5px;
                padding-top: 2px;
                padding-bottom: 2px;
                line-height: 1.2;
            }
            ''' % (
                settings['font_family'],
                settings['font_size'],
                settings['font_weight'],
                settings['text_color']
                )
            )

class LoadingWindow(QDialog):
    '''
    This is a loading window that will be displayed while the application is loading.
    '''
    
    def __init__(self, app_configs):
        QDialog.__init__(self)
        window_settings = app_configs.get_application_setting('loading_dialog')
        self.setGeometry(0,0,400,400)
        self.setStyleSheet('background-color: %s' % window_settings['background_color'])
        self.setWindowTitle("Loading...")
        
        self.layout = StyledVBoxLayout()
        self.label = Label(app_configs)

        self.layout.addStretch(1)
        self.layout.addWidget(self.label)
        self.layout.addStretch(1)
        self.setLayout(self.layout)