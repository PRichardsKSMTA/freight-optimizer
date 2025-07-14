'''
Author: Daniel Kinn
Date: 2023-10-30

This file contains manages the configuration entries for the optimization GUI.
'''

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

from ..widgets.common import disableable_widget
from ..widgets.common.styled_groupbox import StyledGroupBox
from ..widgets.common.styled_integer_selector import StyledIntegerSelector
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout
from ..widgets.common.styled_checkbox import StyledCheckbox
from ..widgets.common.styled_hbox_layout import StyledHBoxLayout
from ..widgets.common.info_tooltip import InfoTooltip

class ConfigurationEntryGroup(disableable_widget.DisableableWidget): 
    """This class is responsible for displaying the configuration entry groupbox, which
    are all of the model parameters (i.e. max deadhead, mileage rate, etc.)
    """    

    def __init__(self, configs, width: int, enabled: bool=True, parent: QWidget=None):
        self.configs = configs
        self.width = width
        self.box_configs = self.configs.get_application_setting('configuration_panel', 'model_parameters_groupbox')
        self.group_box = self.generate_groupbox()
        super(ConfigurationEntryGroup, self).__init__(parent=parent, enabled=enabled, width=width)


    def load_ui(self) -> None:
        """loads the UI when this widget is enabled
        """
        self.clear_ui()
        self.deadhead_selector = self.create_max_deadhead_selector()
        self.mileage_rate_selector = self.create_mileage_rate_selector()
        self.margin_target_selector = self.create_margin_target_selector()
        self.max_capacity_selector = self.create_max_capacity_selector()
        self.min_miles_selector = self.create_min_miles_selector()

        vbox = StyledVBoxLayout()
        two_tour_limit_checkbox = ModelSelectorCheckbox('two_trip_limit', self.configs)
        vbox.addWidget(two_tour_limit_checkbox)
        tsp_checkbox = ModelSelectorCheckbox('tsp', self.configs)
        vbox.addWidget(tsp_checkbox)
        vbox.addWidget(self.deadhead_selector)
        vbox.addWidget(self.mileage_rate_selector)
        vbox.addWidget(self.margin_target_selector)
        vbox.addWidget(self.max_capacity_selector)
        vbox.addWidget(self.min_miles_selector)
 
        self.group_box = self.generate_groupbox()
        self.group_box.setLayout(vbox)
        self.layout.addWidget(self.group_box)


    def generate_groupbox(self) -> StyledGroupBox:
        """This function generates the groupbox for this widget.

        Args:
            box_configs (dict): The configurations for this groupbox

        Returns:
            StyledGroupBox: The groupbox for this widget
        """
        group_box = StyledGroupBox(self.box_configs['title'], app_configs=self.configs)
        group_box.setFixedSize(self.width, self.box_configs['height'] - 20)
        return group_box


    def reset(self) -> None:
        """This function resets the configuration to the default values
        """        
        self.load_ui()

    def load_disabled_ui(self) -> None:
        """loads the UI when this widget is disabled
        """        
        self.clear_ui()
        self.group_box.set_ui(enabled=False, add_disabled_label=True)
        self.layout.addWidget(self.group_box)

        
    def create_max_deadhead_selector(self) -> StyledIntegerSelector:
        '''
        Creates a selector for the maximum deadhead
        '''
        deadhead_update_function = self.configs.update_max_deadhead
        min_deadhead, max_deadhead = self.configs.get_max_deadhead_range()
        deadhead_label = self.box_configs['max_deadhead_selector']['label']
        deadhead_tooltip = self.box_configs['max_deadhead_selector']['tooltip']
        default_value = self.configs.get_max_deadhead()
        selector = StyledIntegerSelector(deadhead_label, 
                                        min_value=min_deadhead,
                                        max_value=max_deadhead,
                                        update_func=deadhead_update_function,
                                        configs=self.configs,
                                        default_value=default_value,
                                        tooltip_text=deadhead_tooltip)
        
        return selector
    
    
    def create_mileage_rate_selector(self) -> StyledIntegerSelector:
        '''
        Creates a selector for the mileage rate
        '''
        mileage_update_function = self.configs.update_mileage_rate
        min_mileage, max_mileage = self.configs.get_mileage_rate_range()
        mileage_rate_label = self.box_configs['mileage_rate_selector']['label']
        mileage_rate_tooltip = self.box_configs['mileage_rate_selector']['tooltip']
        num_decimals = self.box_configs['mileage_rate_selector']['decimals']
        default_value = self.configs.get_mileage_rate()
        selector = StyledIntegerSelector(mileage_rate_label,
                                        min_value=min_mileage,
                                        max_value=max_mileage,
                                        update_func=mileage_update_function,
                                        configs=self.configs,
                                        default_value=default_value,
                                        tooltip_text=mileage_rate_tooltip,
                                        double=True,
                                        decimals=num_decimals)
        return selector
    

    def create_margin_target_selector(self) -> StyledIntegerSelector:
        '''
        Creates a selector for the mileage rate
        '''
        mileage_update_function = self.configs.update_margin_target
        min_mileage, max_mileage = self.configs.get_margin_target_range()
        mileage_rate_label = self.box_configs['margin_target_selector']['label']
        margin_target_tooltip = self.box_configs['margin_target_selector']['tooltip']
        default_value = self.configs.get_margin_target()
        selector = StyledIntegerSelector(mileage_rate_label,
                                        min_value=min_mileage,
                                        max_value=max_mileage,
                                        update_func=mileage_update_function,
                                        configs=self.configs,
                                        default_value=default_value,
                                        tooltip_text=margin_target_tooltip,
                                        double=False)
        return selector
    

    def create_max_capacity_selector(self) -> StyledIntegerSelector:
        """This function creates and returns the max capacity selector

        Returns:
            StyledIntegerSelector: The max capacity selector
        """
        max_capacity_update_function = self.configs.update_max_capacity
        min_capacity, max_capacity = self.configs.get_max_capacity_range()
        max_capacity_label = self.box_configs['max_capacity_selector']['label']
        max_capacity_tooltip = self.box_configs['max_capacity_selector']['tooltip']
        default_value = self.configs.get_max_capacity()
        selector = StyledIntegerSelector(max_capacity_label,
                                        min_value=min_capacity,
                                        max_value=max_capacity,
                                        update_func=max_capacity_update_function,
                                        configs=self.configs,
                                        default_value=default_value,
                                        tooltip_text=max_capacity_tooltip)
        return selector
    

    def create_min_miles_selector(self) -> StyledIntegerSelector:
        """This function creates and returns the min miles selector

        Returns:
            StyledIntegerSelector: The min miles selector
        """
        min_miles_update_function = self.configs.update_min_miles
        min_miles = self.box_configs['minimum_miles_selector']['minimum']
        max_miles = self.box_configs['minimum_miles_selector']['maximum']
        min_miles_label = self.box_configs['minimum_miles_selector']['label']
        min_miles_tooltip = self.box_configs['minimum_miles_selector']['tooltip']
        default_value = self.configs.get_min_miles()
        selector = StyledIntegerSelector(min_miles_label,
                                        min_value=min_miles,
                                        max_value=max_miles,
                                        update_func=min_miles_update_function,
                                        configs=self.configs,
                                        default_value=default_value,
                                        tooltip_text=min_miles_tooltip)
        return selector



class ModelSelectorCheckbox(QWidget):
    '''
    simple class for a checkbox that toggles the state of a model
    '''

    def __init__(self, model_name: str, configs):
        '''
        text: text to display next to the checkbox
        model_name: name of the model to toggle
        configs: ModelConfiguration object
        '''
        super(ModelSelectorCheckbox, self).__init__()
        self.model_name = model_name
        self.configs = configs
        layout = StyledHBoxLayout()


        model_settings = configs.get_application_setting('configuration_panel', 'model_selector')
        checkbox_label = model_settings[model_name]['label']
        self.checkbox = StyledCheckbox(checkbox_label)

        if self.configs.get_model_state(model_name):
            self.checkbox.setCheckState(Qt.Checked)
        else:
            self.checkbox.setCheckState(Qt.Unchecked)

        self.checkbox.stateChanged.connect(self.change_state)
        layout.addWidget(self.checkbox)

        self.tooltip = InfoTooltip(configs, tooltip_text=model_settings[model_name]['tooltip'])
        layout.addWidget(self.tooltip)

        self.setLayout(layout)

    def change_state(self) -> None:
        #calls the toggle function to update the state for this model
        self.configs.toggle_model_state(self.model_name)