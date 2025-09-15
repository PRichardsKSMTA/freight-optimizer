'''
Author: Daniel Kinn
Date: 2023-10-04

This file contains code for creating the configuration metadata groupbox. This is a
groupbox that contains the configuration name entry, date created, and last modified.

'''

from ..widgets.common.styled_groupbox import StyledGroupBox
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout
from ..widgets.common.disableable_widget import DisableableWidget
from ..widgets import widget_functions
from ..widgets.common.styled_label import StyledLabel
import time

class DataSelectionGroupbox(DisableableWidget): 

    def __init__(self, app_configs, data_filter, enabled: bool, width: int, parent=None):
        self.app_configs = app_configs
        self.data_filter = data_filter
        self.date_display_label = None
        self.width = width
        self.box_configs = self.app_configs.get_application_setting('configuration_panel', 'data_selection_groupbox')
        self.group_box = self.generate_groupbox()
        super(DataSelectionGroupbox, self).__init__(enabled=enabled, parent=parent, width=width)
        

    def load_ui(self): 
        self.clear_ui() 
        vbox = StyledVBoxLayout()
        item_widgets = []
        self.date_display_label = self.get_date_display_label()
        for field_items in self.box_configs['fields']:
            item_widget = widget_functions.get_widget_from_field_configs(
                field_configs=field_items,
                app_configs=self.app_configs,
                data_filter=self.data_filter
            )
            item_widgets.append(item_widget)
            vbox.addWidget(item_widget)
            if 'update_data_delay' in field_items.keys():
                if field_items['update_data_delay']:
                    item_widget.valueChanged.connect(lambda x: self.update_label_text(delay=True))
        
        
        vbox.addWidget(self.date_display_label)

        self.group_box = self.generate_groupbox()
        self.group_box.set_ui(enabled=True)
        self.group_box.setLayout(vbox)
        self.layout.addWidget(self.group_box)
 

    def load_disabled_ui(self):
        self.clear_ui()
        self.group_box.set_ui(enabled=False)
        self.layout.addWidget(self.group_box)


    def reset(self):
        """Rebuild the group box while keeping the current filter selections."""
        preserved_filters = {}
        for field_items in self.box_configs.get('fields', []):
            field_configs = widget_functions.FieldConfigs(field_items)
            filter_key = None
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

        if rebuild_enabled and self.date_display_label is not None:
            self.update_label_text()


    def update_label_text(self, delay: bool=False):
        """This function updates the label text for
        the date display label.
        
        Args:
            delay (bool, optional): Whether to update the data delay. 
                The delay may be useful if other items need to update.
                Defaults to False.
        """
        if delay:
            time.sleep(0.01)
        text = self.get_date_display_text()
        self.date_display_label.setText(text)

        
    
    def get_date_display_text(self) -> str:
        """This function returns the date display text

        Returns:
            str: The date display text
        """
        trial_start, trial_end = self.data_filter.get_trial_range()
        date_display_text = f'Trial will include data from {trial_start} to {trial_end}'

        return date_display_text

    
    def get_date_display_label(self) -> StyledLabel:
        """This function returns the date display text

        Returns:
            StyledLabel: The date display text
        """
        date_display_text = self.get_date_display_text()
        date_display_label = StyledLabel(text=date_display_text, app_configs=self.app_configs)
        return date_display_label  

    
    def generate_groupbox(self) -> StyledGroupBox:
        """This function generates the groupbox for this widget

        Returns:
            styled_groupbox.StyledGroupBox: The groupbox for this widget
        """
        group_box = StyledGroupBox(self.box_configs['title'], app_configs=self.app_configs)
        group_box.setFixedSize(self.width, self.box_configs['height'] - 20 )
        return group_box