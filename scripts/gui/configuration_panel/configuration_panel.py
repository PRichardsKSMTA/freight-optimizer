'''
Author: Daniel Kinn
Date: 2023-10-04

This file contains manages the configuration panel for the optimization GUI. This panel
is responsible for maintaining the form components that allow the user to modify configurations.

'''

from ..widgets.colored_widget import ColoredWidget
from gui.dialogs.data_exclusion_dialog import DataExclusionDialog
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout
from ..widgets.common.styled_hbox_layout import StyledHBoxLayout
from ..widgets.common.styled_button import StyledButton
from ..widgets.common.styled_scroll_area import StyledScrollArea
from .configuration_entries_group import ConfigurationEntryGroup
from .configuration_metadata_groupbox import ConfigurationMetaData
from .customer_groupbox import CustomerGroupBox
from .aggregation_builder_groupbox import AggregationBuilderGroupbox
from .data_selection_groupbox import DataSelectionGroupbox
from gui.configuration_panel.data_exclusion_groupbox import DataExclusionGroupbox
from gui.dialogs.save_configuration_dialog import SaveConfigurationDialog

class ConfigurationPanel(ColoredWidget):
    """This panel is responsible for maintaining the form components that allow the user to modify configurations.
    The panel is a vertical box layout that contains the following widgets:
        - CustomerGroupBox
        - ConfigurationMetaData
        - model_selector_group.ModelSelectorGroup
        - configuration_entries_group.ConfigurationEntryGroup
        - configuration_date_groupbox.ConfigurationDateGroupbox
    """
    def __init__(self, model_configs, data_filter, start_func):
        self.model_configs = model_configs
        self.data_filter = data_filter
        self.start_func = start_func
        panel_color = self.model_configs.get_application_setting('configuration_panel', 'background_color')
        super(ConfigurationPanel, self).__init__(panel_color)
        self.load_ui()
        

    def load_ui(self) -> None:
        
        left_width = self.model_configs.get_application_setting('configuration_panel', 'left_width')
        right_width = self.model_configs.get_application_setting('configuration_panel', 'right_width')
        
        self.hlayout = StyledHBoxLayout(margins=(0, 0, 0, 0))
        leftVboxLayout = StyledVBoxLayout(margins=(5, 5, 5, 5))

        cust_groupbox_scroll = StyledScrollArea()
        self.cust_groupbox = CustomerGroupBox(
            model_configs=self.model_configs,
            data_filter=self.data_filter,
            parent=self,
            width=left_width
            )
        cust_groupbox_scroll.setWidget(self.cust_groupbox)
        cust_groupbox_scroll.setFixedHeight(
            self.model_configs.get_application_setting('configuration_panel', 'configuration_customer_information')['height'] - 10)
        leftVboxLayout.addWidget(cust_groupbox_scroll)

        metadata_scroll_area = StyledScrollArea()
        self.metadata_groupbox = ConfigurationMetaData(
            self.model_configs,
            data_filter=self.data_filter,
            enabled=False,
            width=left_width,
            load_client_func=self.load_client,
            undo_changes_func=self.undo_changes,
            )
        metadata_scroll_area.setWidget(self.metadata_groupbox)
        metadata_scroll_area.setFixedHeight(self.model_configs.get_application_setting('configuration_panel', 'configuration_metadata_box')['height'] - 10)
        leftVboxLayout.addWidget(metadata_scroll_area)

        data_selection_scroll_area = StyledScrollArea()
        self.data_selection_groupbox = DataSelectionGroupbox(
            self.model_configs,
            data_filter=self.data_filter,
            enabled=False,
            width=left_width
            )
        data_selection_scroll_area.setWidget(self.data_selection_groupbox)
        data_selection_scroll_area.setFixedHeight(self.model_configs.get_application_setting('configuration_panel', 'data_selection_groupbox')['height'] - 10)
        leftVboxLayout.addWidget(data_selection_scroll_area)

        rightVboxLayout = StyledVBoxLayout(margins=(0, 5, 5, 5))
    
        configuration_entry_scroll_area = StyledScrollArea()
        self.configuration_entry_group = ConfigurationEntryGroup(
            self.model_configs,
            enabled=False,
            width=right_width)
        configuration_entry_scroll_area.setWidget(self.configuration_entry_group)
        configuration_entry_scroll_area.setFixedHeight(
            self.model_configs.get_application_setting('configuration_panel', 'model_parameters_groupbox')['height'] - 10)
        rightVboxLayout.addWidget(configuration_entry_scroll_area)

        aggregation_builder_scroll_area = StyledScrollArea()
        self.aggregation_builder_groupbox = AggregationBuilderGroupbox(self.model_configs, self.data_filter, enabled=False, width=right_width)
        aggregation_builder_scroll_area.setWidget(self.aggregation_builder_groupbox)
        aggregation_builder_scroll_area.setFixedHeight(
            self.model_configs.get_application_setting('configuration_panel', 'aggregration_builder_box')['height'] - 10)
        rightVboxLayout.addWidget(aggregation_builder_scroll_area)

        self.data_exclusion_button = StyledButton(
            label=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['label'],
            tooltip_text=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['tooltip_text'],
            invalid_tooltip_text=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['invalid_tooltip_text'],
            background_color=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['background_color'],
            text_color=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['text_color'],
            hover_background_color=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['hover_background_color'],
            hover_text_color=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['hover_text_color'],
            border_color=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['border_color'],
            invalid_background_color=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['invalid_background_color'],
            invalid_hover_background_color=self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')['button']['invalid_hover_background_color'],
            func_=self.open_exclusion_dialog,
            valid_state=False,
            margins=(5,5,5,5),
            max_width=left_width + 10
        )
        leftVboxLayout.addWidget(self.data_exclusion_button)

        self.run_button = self.get_run_button('run_button', func_=self.verify_scenario_on_run, enabled=False, max_width=right_width + 10)
        rightVboxLayout.addWidget(self.run_button)
              
        self.hlayout.addLayout(leftVboxLayout)
        self.hlayout.addLayout(rightVboxLayout)

        self.setLayout(self.hlayout)


    def load_client(self, client_id: str) -> None:
        """This function is trigged when a client is loaded from the CustomerGroupBox.
        This function will active the appropriate widgets in the configuration panel.

        Args:
            client_id (string): A string representing the client_id.
        """
        refresh_ui = True
        if self.data_filter.client_id == client_id:
            refresh_ui = False
        else:
            self.data_filter.scenario_id = None
        self.data_filter.client_id = client_id
        if client_id is not None:
            self.metadata_groupbox.set_enabled(True, refresh_ui=refresh_ui)
            self.data_exclusion_button.set_valid_state(True)
            self.run_button.set_valid_state(True)
            self.configuration_entry_group.set_enabled(True, refresh_ui=refresh_ui)
            self.data_selection_groupbox.set_enabled(True, refresh_ui=refresh_ui)
            self.aggregation_builder_groupbox.set_enabled(True, refresh_ui=refresh_ui)
            self.data_exclusion_configs = self.model_configs.get_application_setting('configuration_panel', 'data_exclusion')
            self.data_exclusion_groupbox = DataExclusionGroupbox(
                self.model_configs,
                self.data_filter,
                enabled=True,
                width=self.data_exclusion_configs['width']
                )
            # self.data_exclusion_dialog = DataExclusionDialog(self.model_configs, data_filter=self.data_filter, groupbox=self.data_exclusion_groupbox, parent=self)
            self.data_filter.get_configuration_load_table(client_id)
        else:
            self.metadata_groupbox.set_enabled(False)
            self.data_exclusion_button.set_valid_state(False)
            self.run_button.set_valid_state(False)
            self.configuration_entry_group.set_enabled(False)
            self.data_selection_groupbox.set_enabled(False)
            self.aggregation_builder_groupbox.set_enabled(False)
            self.data_exclusion_dialog = None

    def open_exclusion_dialog(self) -> None:
        """This function is called when the user clicks the data exclusion button. This function will
        open the data exclusion dialog.
        """
        self.data_exclusion_groupbox = DataExclusionGroupbox(
            self.model_configs,
            self.data_filter,
            enabled=True,
            width=self.data_exclusion_configs['width']
            )
        self.data_exclusion_dialog = DataExclusionDialog(self.model_configs, data_filter=self.data_filter, groupbox=self.data_exclusion_groupbox, parent=self)
        self.data_filter.capture_config_screenshot()
        if self.data_exclusion_dialog is not None:
            self.data_exclusion_dialog.open_dialog()


    def verify_scenario_on_run(self) -> bool:
        """This function verifies that the scenario is valid before running the optimization.

        Returns:
            bool: True if the scenario is valid, False otherwise.
        """       
        if self.data_filter.scenario_id is None:
            self.save_scenario_dialog = SaveConfigurationDialog(self.model_configs, 
                parent=self, data_filter=self.data_filter, start_func=self.start_func, 
                undo_changes_func=self.undo_changes)
            self.save_scenario_dialog.open_dialog()
        elif self.data_filter.check_scenario_changed():
            self.save_scenario_dialog = SaveConfigurationDialog(self.model_configs, parent=self, 
                data_filter=self.data_filter, start_func=self.start_func, 
                undo_changes_func=self.undo_changes)
            self.save_scenario_dialog.open_dialog()
        else:
            self.start_func()


    def undo_changes(self) -> None:
        '''
        This function is called when the user clicks the undo changes button. 
        This function will reload this configuration panel
        '''
        self.clear_ui()
        self.load_ui()


    def get_run_button(self, button_type: str, enabled:bool=True, func_=None, 
            max_width: int=None) -> StyledButton:
        """This function returns a StyledButton for the run button

        Args:
            button_type (str): The type of button to return
            enabled (bool, optional): True if the button should be enabled, False otherwise. 
                Defaults to True.
            func_ (function, optional): The function to call when the button is clicked.
                Defaults to None.

        Returns:
            StyledButton: _description_
        """        
        button_settings = self.model_configs.get_application_setting('footer', button_type)
        button = StyledButton(button_settings['label'],
                              valid_state=enabled,
                              background_color=button_settings['background_color'],
                              text_color=button_settings['text_color'],
                              func_=func_,
                              hover_background_color=button_settings['hover_background_color'],
                              hover_text_color=button_settings['hover_text_color'],
                              border_color=button_settings['border_color'],
                              invalid_background_color=button_settings['invalid_background_color'],
                              invalid_hover_background_color=button_settings['invalid_hover_background_color'],
                              invalid_tooltip_text=button_settings['invalid_tooltip_text'],
                              margins=(5,5,5,5),
                              max_width=max_width) 
        
        return button
    

    def clear_ui(self) -> None:
        """This function clears the UI for the widget
        """        
        self.configuration_entry_group.reset()
        self.metadata_groupbox.reset()
        self.data_selection_groupbox.reset()