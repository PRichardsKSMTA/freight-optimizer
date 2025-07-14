"""This module contains the DisableableWidget class, which is used to create a widget
that can be enabled or disabled. When the widget is enabled, the load_ui function is called.
When the widget is disabled, the load_disabled_ui function is called.

Author: Daniel Kinn
Date: 2023-11-25
"""

from PySide6.QtWidgets import QWidget

from .styled_vbox_layout import StyledVBoxLayout

class DisableableWidget(QWidget):
    """This is a base class for creating a disableable widget
    """    
    def __init__(self, width: int, enabled: bool=True, parent: QWidget=None):
        """This function initializes the widget

        Args:
            enabled (bool, optional): True if the widget should be enabled, 
                False otherwise. Defaults to True.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """        
        super(DisableableWidget, self).__init__(parent=parent)
        self.width = width
        self.layout = StyledVBoxLayout()
        self.setLayout(self.layout)
        self.enabled = None
        self.set_enabled(enabled)


    def clear_ui(self) -> None:
        """This function clears the UI for the widget
        """        
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)

    
    def load_ui(self) -> None:
        """This function loads the UI for the widget. This function should be overridden

        Raises:
            NotImplementedError: This function should be overridden
        """        
        raise NotImplementedError('load_ui function not implemented')
    
    
    def set_enabled(self, enabled: bool, refresh_ui: bool=False):
        """This function sets the enabled state of the widget. 
        If the widget is enabled, the load_ui function is called.
        If the widget is disabled, the load_disabled_ui function is called.

        Args:
            enabled (bool): True if the widget should be enabled, False otherwise
            refresh_ui (bool, optional): True if the UI should be refreshed. 
                Defaults to False.
        """        
        if self.enabled == enabled:
            if refresh_ui:
                self.load_ui()
        if enabled:
            self.load_ui()
        else:
            self.load_disabled_ui()
        self.enabled = enabled


    def load_disabled_ui(self) -> None:
        """This function loads the UI for this widget when it is disabled.
            This function should be overridden

        Raises:
            NotImplementedError: This function should be overridden
        """        
        raise NotImplementedError('load_ui function not implemented')