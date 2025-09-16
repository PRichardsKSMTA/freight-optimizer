'''
Author: Daniel Kinn
Date: 2023-11-08

This file contains code for creating the aggregation builder groupbox. This is a
groupbox that contains client filters

'''

from PySide6.QtWidgets import QWidget

from ..widgets.common.styled_groupbox import StyledGroupBox
from ..widgets.common.disableable_widget import DisableableWidget
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout
from gui.data_configuration.data_filter import DataFilter
from ..configuration import ModelConfiguration
from ..widgets import widget_functions

class AggregationBuilderGroupbox(DisableableWidget): 
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
        self.box_configs = self.app_configs.get_application_setting('configuration_panel', 'aggregration_builder_box')
        self.group_box = self.generate_groupbox()
        super(AggregationBuilderGroupbox, self).__init__(enabled=enabled, parent=parent, width=width)


    def load_ui(self) -> None:
        """Loads this widget when it is in an enabled state. This will
        clear the UI and set the groupbox to enabled.
        """        
        self.clear_ui() 
        self.group_box.set_ui(enabled=True, add_disabled_label=True)
        vbox = StyledVBoxLayout()

        for field_items in self.box_configs['fields']:
            item_widget = widget_functions.get_widget_from_field_configs(
                field_configs=field_items,
                app_configs=self.app_configs,
                data_filter=self.data_filter
            )
            vbox.addWidget(item_widget)

        self.group_box = self.generate_groupbox()
        self.group_box.setLayout(vbox)
        self.layout.addWidget(self.group_box)
 

    def load_disabled_ui(self) -> None:
        """Loads this widget when it is in a disabled state. This will
        clear the UI and set the groupbox to disabled.
        """        
        self.clear_ui()
        self.group_box.set_ui(enabled=False, add_disabled_label=True)
        self.layout.addWidget(self.group_box)


    def reset(self) -> None:
        """Rebuild the widget while preserving the current data filter selections."""

        preserved_filters = {}
        for field_items in self.box_configs.get('fields', []):
            field_configs = widget_functions.FieldConfigs(field_items)
            if field_configs.data_field is not None:
                filter_key = field_configs.data_field
            elif field_configs.var_name is not None:
                filter_key = field_configs.var_name
            else:
                filter_key = field_configs.label
            filter_value = self.data_filter.get_filter_value(filter_key)
            if filter_value is not None:
                preserved_filters[filter_key] = filter_value

        rebuild_enabled = self.enabled is not False
        if rebuild_enabled:
            self.load_ui()
        else:
            self.load_disabled_ui()

        for filter_key, filter_value in preserved_filters.items():
            self.data_filter.set_filter(filter_key, filter_value)


    def generate_groupbox(self) -> StyledGroupBox:
        """This function generates the groupbox for this widget.

        Returns:
            StyledGroupBox: The groupbox for this widget.
        """        
        group_box = StyledGroupBox(self.box_configs['title'], app_configs=self.app_configs)
        group_box.setMinimumSize(self.width, self.box_configs['height'] - 20)
        group_box.setFixedWidth(self.width)
        return group_box
