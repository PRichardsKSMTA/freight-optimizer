'''
Author: Daniel Kinn
Date: 2023-10-04
Last Updated: 2023-11-24

This file contains code for creating the configuration metadata groupbox. This is a
groupbox that contains the configuration name entry, date created, and last modified.

'''
import pandas
from PySide6.QtWidgets import QWidget


from gui.configuration import ModelConfiguration
from gui.data_configuration.data_filter import DataFilter
from ..customer_selection.customer_selection_dialog import CustomerSelectionDialog
from ..widgets.common import styled_groupbox
from ..widgets.common import styled_label
from ..widgets.common import styled_vbox_layout
from ..widgets.common import styled_button


class CustomerGroupBox(QWidget): 
    """This class displays the customer information selected for this scenario and allows the user to change it by
    opening the intro dialog.
    """    

    def __init__(self, model_configs: ModelConfiguration, data_filter: DataFilter, parent: QWidget, width: float):
        super(CustomerGroupBox, self).__init__()

        self.parent = parent
        self.model_configs = model_configs
        self.data_filter = data_filter
        self.groupbox_settings = self.model_configs.get_application_setting('configuration_panel', 'configuration_customer_information')
        self.group_box = styled_groupbox.StyledGroupBox(self.groupbox_settings['groupbox_title'], app_configs=self.model_configs)
        self.group_box.setFixedSize(width, self.groupbox_settings['height'] - 20)
        self.group_box.set_ui(enabled=True)
        self.load_ui()


    def load_ui(self):
        """loads the ui for this widget
        """        

        self.customer_dialog = CustomerSelectionDialog(data_filter=self.data_filter,
                                                       model_configs=self.model_configs,
                                                       on_load=self.load_client,
                                                       initial_load=False,
                                                       parent=self.parent)
        vbox = styled_vbox_layout.StyledVBoxLayout()

        button_style = self.groupbox_settings['change_customer_button']
        customer_name = self.data_filter.get_client_name()
        customer_button_label = button_style['label_selected']
        if pandas.isnull(customer_name):
            customer_name = 'None selected'
            customer_button_label = button_style['label_unselected']
        self.customer_name_label = styled_label.StyledLabel(
            text=self.groupbox_settings['groupbox_title'] + ': ' + customer_name,
            app_configs=self.model_configs
        )
        vbox.addWidget(self.customer_name_label)

        self.change_customer_button = styled_button.StyledButton(
            label=customer_button_label,
            func_=self.open_customer_dialog,
			background_color=button_style['background_color'],
			text_color=button_style['text_color'],
			hover_background_color=button_style['hover_background_color'],
			hover_text_color=button_style['hover_text_color'],
			border_color=button_style['border_color'],
			valid_state=True
            )
        vbox.addWidget(self.change_customer_button)
        self.group_box.setLayout(vbox)

        layout = styled_vbox_layout.StyledVBoxLayout()
        self.setLayout(layout)
        layout.addWidget(self.group_box)
    

    def open_customer_dialog(self):
        """opens the customer dialog box
        """        
        self.customer_dialog.open_dialog()


    def load_client(self, client_id: str):
        """passes this function to the configuration panel so that it can be called when the client_id is changed

        Args:
            client_id (str): the client_id to load
        """
        self.parent.load_client(client_id)
        client_name = self.data_filter.get_client_name()
        if pandas.isnull(client_name):
            client_name = 'None selected'
        new_text = self.groupbox_settings['groupbox_title'] + ': ' + client_name
        self.customer_name_label.setText(new_text)
        self.change_customer_button.setText(self.groupbox_settings['change_customer_button']['label_selected'])