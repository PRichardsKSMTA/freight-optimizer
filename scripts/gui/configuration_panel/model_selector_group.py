
from PySide6.QtWidgets import  QWidget
from PySide6.QtCore import Qt

from ..widgets.common.styled_checkbox import StyledCheckbox
from ..widgets.common.info_tooltip import InfoTooltip
from ..widgets.common.styled_groupbox import StyledGroupBox
from ..widgets.common.disableable_widget import DisableableWidget
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout
from ..widgets.common.styled_hbox_layout import StyledHBoxLayout

class ModelSelectorGroup(DisableableWidget): 
    """This class is responsible for displaying the model selector groupbox, which
    allows the user to choose one or more models to run.

    """    

    def __init__(self, configs, width:int, parent: QWidget=None, enabled: bool=True):
        """This function initializes the ModelSelectorGroup widget.

        Args:
            configs (Configuration): The model configuration object.
            width (int): The width of the groupbox.
            parent (QWidget, optional): The parent widget for this widget. Defaults to None.
            enabled (bool, optional): The initial enabled state for this widget. Defaults to True.
        """        
        self.configs = configs
        self.width = width
        self.groupbox_configs = configs.get_application_setting('configuration_panel', 'model_selector')
        self.group_box = self.generate_groupbox()
        super(ModelSelectorGroup, self).__init__(parent=parent, enabled=enabled, width=width)
        

    def load_ui(self) -> None:
        """This function loads the enabled UI. It will create all widgets needed when
        this widget is enabled.
        """        
        self.clear_ui()
        self.group_box = self.generate_groupbox()

        two_tour_limit_checkbox = ModelSelectorCheckbox('two_trip_limit', self.configs)
        tsp_checkbox = ModelSelectorCheckbox('tsp', self.configs)
        self.vbox = StyledVBoxLayout()
        self.vbox.addWidget(two_tour_limit_checkbox)
        self.vbox.addWidget(tsp_checkbox)
        self.group_box.setLayout(self.vbox)
        self.layout.addWidget(self.group_box)


    def load_disabled_ui(self) -> None:
        """This function loads the disabled UI. It will remove all widgets and set the
        view to the disabled view.
        """        
        self.clear_ui()
        self.group_box = self.generate_groupbox()
        self.layout.addWidget(self.group_box)

    
    def generate_groupbox(self) -> StyledGroupBox:
        """This function generates the groupbox for this widget.

        Returns:
            StyledGroupBox: The groupbox for this widget.
        """        
        group_box = StyledGroupBox(self.groupbox_configs['title'])
        group_box.setFixedSize(self.width, self.groupbox_configs['height'])
        return group_box



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
        layout = StyledHBoxLayout(margins=(1,1,1,1))

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
