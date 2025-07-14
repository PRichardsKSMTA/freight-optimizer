from PySide6.QtWidgets import QGroupBox

from .styled_label import StyledLabel
from .styled_vbox_layout import StyledVBoxLayout

class StyledGroupBox(QGroupBox): 
    '''
    This function creates a consistently styled groupbox for the application.
    '''
    def __init__(self, label: str, app_configs, min_height: float=None, enabled: bool=True,
                 enabled_background_color: str=None):
        """Initializes this class

        Args:
            label (str): The label of this groupbox
            min_height (float, optional): The minimum height attribute value
                for this groupbox. Defaults to None, meaning the css attribute
                will not be explicitly set.
            enabled (bool, optional): Whether this groupbox should have the
                eanbled formatting (True) or disabled formatting (False). 
                Defaults to True.
        """        
        super(StyledGroupBox, self).__init__(label)
        self.app_configs = app_configs
        self.groupbox_style = self.app_configs.get_application_setting('groupbox')
        self.min_height = min_height
        self.enabled_background_color = enabled_background_color
        self.set_ui(enabled)

    
    def set_ui(self, enabled: bool, add_disabled_label: bool=True):
        """Sets the formatting of this groupbox, based on whether it is enabled or not.

        Args:
            enabled (bool): Whether this groupbox is enabled
            add_disabled_label (bool, optional): Whether to add the disabled text to this groupbox.
                Defaults to False.
        """
        if enabled:
            background_color = self.groupbox_style['background_color']
        else:
            background_color = self.groupbox_style['disabled_background_color']

        if enabled:
            color = self.groupbox_style['text_color']
        else:
            color = self.groupbox_style['disabled_title_color']

        if enabled:
            border_color = self.groupbox_style['border_color']
        else:
            border_color = self.groupbox_style['disabled_border_color']
        
        if self.min_height is not None:
            self.setMinimumHeight(self.min_height)

        self.setStyleSheet('''
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: %s;
                background-color: %s;
                border-radius: 5px;
                border: 1px solid %s;
                padding-top: 12px;
                padding-right: 5px;
                padding-left: 5px;        
                padding-bottom:0px;
            }
            QGroupBox::title {
                padding-left: 3px;
                padding-top: 3px;
                border-top-left-radius: 5px;
                border-top: 1px solid %s;
                border-left: 1px solid %s;
            }

        ''' % (
            color,
            background_color,
            border_color,
            border_color,
            border_color
        ))

        if (not enabled) and (add_disabled_label):
            vbox = StyledVBoxLayout()
            text_color = self.groupbox_style['disabled_label_color']
            vbox.addWidget(StyledLabel('\nSelect a client to enable this section', self.app_configs, text_color=text_color))
            self.setLayout(vbox)