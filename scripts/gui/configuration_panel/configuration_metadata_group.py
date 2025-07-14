'''
Author: Daniel Kinn
Date: 2023-10-04

This file contains code for creating the configuration metadata groupbox. This is a
groupbox that contains the configuration name entry, date created, and last modified.

'''
import pandas
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

from ..data_configuration.data_filter import DataFilter, ConfigurationNameError
from ..widgets.common.styled_groupbox import StyledGroupBox
from ..widgets.common.styled_line_edit import StyledLineEdit
from ..widgets.common.disableable_widget import DisableableWidget
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout
from ..widgets.common.styled_dialog import StyledDialog
from ..widgets.common.styled_button import StyledButton
from ..widgets.common.styled_hbox_layout import StyledHBoxLayout
from ..dialogs.load_configuration_dialog import LoadConfigurationDialog
from ..widgets.common.styled_checkbox import StyledCheckbox


class ConfigurationMetaData(DisableableWidget): 
    """This is a groupbox that contains the configuration name entry, date created, and last modified.
    """    
    def __init__(self, configs, data_filter: DataFilter, enabled: bool, width: int, load_client_func, 
                 undo_changes_func, parent=None):
        self.configs = configs
        self.data_filter = data_filter
        self.undo_changes_func = undo_changes_func
        self.width = width
        self.load_client_func = load_client_func
        self.box_configs = self.configs.get_application_setting('configuration_panel', 'configuration_metadata_box')
        self.group_box = StyledGroupBox(self.box_configs['title'], app_configs=self.configs)
        self.group_box.setMinimumSize(width, self.box_configs['height'] - 20)
        self.group_box.setFixedWidth(width)
        super(ConfigurationMetaData, self).__init__(enabled=enabled, parent=parent, width=width)
        self.save_error_dialog = SaveErrorDialog(self.configs, parent=self)


    def load_ui(self) -> None: 
        """This function loads the UI for this groupbox.
        """        
        self.clear_ui() 

        vbox = StyledVBoxLayout()
        config_name = self.configs.configuration_name
        if pandas.isnull(config_name):
            config_name = ''
        self.configuration_name_entry = StyledLineEdit(
            self.configs,
            parent=self,
            label=self.box_configs['configuration_name']['label'],
            on_change=self.configs.update_configuration_name,
            tooltip_text=self.box_configs['configuration_name']['tooltip'] ,
            default_entry=config_name
        )
        self.configs.bind_configuration_name_entry(self.configuration_name_entry)
        vbox.addWidget(self.configuration_name_entry)

        config_comment = self.configs.configuration_note
        if pandas.isnull(config_comment):
            config_comment = ''
        self.configuration_comment_entry = StyledLineEdit(
            self.configs,
            parent=self,
            label=self.box_configs['configuration_notes']['label'],
            on_change=self.configs.update_configuration_note,
            tooltip_text=self.box_configs['configuration_notes']['tooltip'],
            default_entry=config_comment
        )
        self.configs.bind_configuration_note_entry(self.configuration_comment_entry)
        vbox.addWidget(self.configuration_comment_entry)

        self.is_preferred_checkbox = StyledCheckbox(
            self.box_configs['preferred_checkbox']['label'],
        )
        vbox.addWidget(self.is_preferred_checkbox)
        is_checked = self.data_filter.get_filter('IsPreferred')
        if pandas.isnull(is_checked):
            is_checked = False
        if is_checked:
            self.is_preferred_checkbox.setCheckState(Qt.Checked)
        else:
            self.is_preferred_checkbox.setCheckState(Qt.Unchecked)
        self.is_preferred_checkbox.stateChanged.connect(self.toggle_preferred_state)

        button_panel = QWidget()
        button_layout = StyledHBoxLayout()
        reset_button = self.get_styled_button('reset_button', func_=self.reset_configuration)
        button_layout.addWidget(reset_button)

        load_button = self.get_styled_button('load_button', func_=self.load_configuration)
        button_layout.addWidget(load_button)

        if self.data_filter.scenario_id is not None:
            save_button = self.get_styled_button('save_button', func_=lambda: self.save_configuration(overwrite_existing=True))
            button_layout.addWidget(save_button)
            button_panel.setLayout(button_layout)

        save_as_button = self.get_styled_button('save_as_button', func_=self.save_configuration)
        button_layout.addWidget(save_as_button)
        button_panel.setLayout(button_layout)

        vbox.addWidget(button_panel)
        self.group_box = StyledGroupBox(self.box_configs['title'], app_configs=self.configs)
        self.group_box.setMinimumSize(self.width, self.box_configs['height'] - 20)
        self.group_box.setFixedWidth(self.width)
        self.group_box.set_ui(enabled=True, add_disabled_label=False)
        self.group_box.setLayout(vbox)
        self.layout.addWidget(self.group_box)
 
    def toggle_preferred_state(self) -> None:
        """This function toggles the preferred state for this configuration.
        """        
        if self.is_preferred_checkbox.isChecked():
            self.data_filter.set_filter('IsPreferred', True)
        else:
            self.data_filter.set_filter('IsPreferred', False)

    def load_disabled_ui(self) -> None:
        """This function loads the disabled UI for this groupbox.
        """        
        self.clear_ui()
        self.group_box.set_ui(enabled=False, add_disabled_label=True)
        self.layout.addWidget(self.group_box)


    
    def save_configuration(self, overwrite_existing:bool=False) -> None:
        """This function calls the save_configuration function in the data filter.
        """        
        try:
            self.data_filter.save_configuration(overwrite_existing=overwrite_existing)
            if not overwrite_existing: #need to refresh to get the save (overwrite) button to display
                self.clear_ui()
                self.load_ui()
        except ConfigurationNameError:
            self.save_error_dialog.open_dialog()
        

    def load_configuration(self) -> None:
        """This function opens the load configuration dialog.
        """        
        load_dialog = LoadConfigurationDialog(self.configs, parent=self, data_filter=self.data_filter, 
                                              on_load=lambda: self.load_client_func(self.data_filter.client_id))
        load_dialog.open_dialog()


    def reset_configuration(self) -> None:
        self.data_filter.undo_changes()
        self.undo_changes_func()

    def get_styled_button(self, button_type: str, func_=None) -> StyledButton:
        button_settings = self.box_configs[button_type]
        button = StyledButton(button_settings['label'],
                                background_color=button_settings['background_color'],
                                text_color=button_settings['text_color'],
                                func_=func_,
                                hover_background_color=button_settings['hover_background_color'],
                                hover_text_color=button_settings['hover_text_color'],
                                border_color=button_settings['border_color'])
        return button
    

class SaveErrorDialog(StyledDialog):
    def __init__(self, configs, parent):
        super(SaveErrorDialog, self).__init__(
            parent=parent,
            window_title='Error',
            save_action=None,
            entry_label=None,
            model_configs=configs,
            default_entry=configs.configuration_name,
            header_label='Configuration name cannot be empty.'
        )
        submit_button_style = configs.get_application_setting('dialog', 'save_button')
        self.submit_button = StyledButton(
            label='Okay',
            background_color=submit_button_style['background_color'],
            text_color=submit_button_style['text_color'],
            func_=self.dialog.close,
            hover_background_color=submit_button_style['hover_background_color'],
            hover_text_color=submit_button_style['hover_text_color'],
            border_color=submit_button_style['border_color'],
            valid_state=True
            )
        self.add_button(self.submit_button)