'''
Author: Daniel Kinn
Date: 2023-11-08

This file contains code for creating the aggregation builder groupbox. This is a
groupbox that contains client filters

'''

from PySide6.QtWidgets import QWidget

from ..widgets.common.styled_groupbox import StyledGroupBox
from ..widgets.common import disableable_widget
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout
from gui.data_configuration.data_filter import DataFilter
from ..configuration import ModelConfiguration
from ..widgets import widget_functions

class DataExclusionGroupbox(disableable_widget.DisableableWidget): 
    """This is a disableable groupbox that is responsible for setting and viewing
    client filters, including Customer Field, Org Level, and A2A Ln Load Min. This
    groupbox is disableable, since it won't be accessible until the client is selected.
    """    
    def __init__(self, app_configs: ModelConfiguration, data_filter: DataFilter, enabled: bool, width: float, parent: QWidget=None):
        """Initializes this class

        Args:
            model_configs (ModelConfiguration): The model configurations for this application
            data_filter (DataFilter): The data filter for this application
            enabled (bool): Whether this groupbox is enabled
            width (float): The width of this groupbox
            parent (QWidget, optional): The parent widget of this groupbox. Defaults to None.
        """        
        
        self.app_configs = app_configs
        self.data_filter = data_filter
        self.width = width
        self.box_configs = self.app_configs.get_application_setting('configuration_panel', 'data_exclusion')
        self.group_box = self.generate_groupbox()
        super(DataExclusionGroupbox, self).__init__(enabled=enabled, parent=parent, width=width)
        

    def load_ui(self): 
        """This function loads the UI for this groupbox"""        
        self.clear_ui() 
        # self.group_box.set_ui(enabled=True)
        vbox = StyledVBoxLayout()

        self.widgets = []
        for field_items in self.box_configs['fields']:
            item_widget = widget_functions.get_widget_from_field_configs(
                field_configs=field_items,
                app_configs=self.app_configs,
                data_filter=self.data_filter
            )
            vbox.addWidget(item_widget)
            self.widgets.append(item_widget)

        self.group_box = self.generate_groupbox()
        self.group_box.setLayout(vbox)
        self.layout.addWidget(self.group_box)
 

    def load_disabled_ui(self):
        """Loads this widget when it is in a disabled state. This will
        clear the UI and set the groupbox to disabled.
        """        
        self.clear_ui()
        self.widgets = []
        self.group_box.set_ui(enabled=False, add_disabled_label=True)
        self.layout.addWidget(self.group_box)

    
    def close(self):
        '''
        remove all of the widgets in case there are blocking threads
        '''
        self.clear_ui()


    def generate_groupbox(self) -> StyledGroupBox:
        """This function generates the groupbox for this widget.

        Returns:
            StyledGroupBox: The groupbox for this widget.
        """        
        group_box = StyledGroupBox(self.box_configs['title'], app_configs=self.app_configs, 
            enabled_background_color=self.box_configs['background_color'])
        group_box.setFixedSize(self.width, self.box_configs['height'])
        return group_box