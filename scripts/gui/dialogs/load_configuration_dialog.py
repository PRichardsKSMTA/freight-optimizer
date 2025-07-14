from PySide6.QtWidgets import QTableView, QAbstractItemView
from PySide6 import QtWidgets

from ..data_configuration.data_filter import DataFilter
from ..widgets.common.styled_dialog import StyledDialog
from ..widgets.common import styled_button
from ..widgets.common.table_model import TableModel
from ..widgets.common.styled_label import StyledLabel
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout

class LoadConfigurationDialog(StyledDialog):
    '''
    This is a dialog box for loading a previosuly saved configuration.
    This will load the names of all previously saved configurations and allow the user to select one.
    '''
    def __init__(self, model_configs, data_filter: DataFilter, on_load, parent=None):
        super(LoadConfigurationDialog, self).__init__(
            window_title='Load Configuration',
            save_action=None,
            entry_label=None,
            model_configs=model_configs,
            parent=parent
        )
        self.data_filter = data_filter
        self.on_load = on_load
        self.model_configs = model_configs
        self.dialog.setMinimumWidth(self.model_configs.get_application_setting('dialog', 'width'))
        self.selection = None 
        self.load_table()


    def set_table(self):
        '''
        Sets the table for the dialog
        '''
        try:
            self.table.setParent(None)
        except:
            pass
        try:
            self.table_label.setParent(None)
        except:
            pass
        try:
            self.main_widget.setParent(None)
            self.layout.setParent(None)
        except:
            pass
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setMinimumHeight(self.model_configs.get_application_setting('dialog', 'minimum_height'))
        self.layout = StyledVBoxLayout()

        self.saved_configuration_df = self.data_filter.load_configuration_df
        if self.data_filter.loading_config_table:
            self.table_label = StyledLabel('Loading... press refresh to update.', self.model_configs)
            self.layout.addWidget(self.table_label)
            # self.add_widget_main(self.table_label)
        elif self.saved_configuration_df is None:
            self.table_label = StyledLabel('No saved configurations found.', self.model_configs)
            self.layout.addWidget(self.table_label)
            # self.add_widget_main(self.table_label)
        elif self.saved_configuration_df.shape[0] == 0:
            self.table_label = StyledLabel('No saved configurations found.', self.model_configs)
            self.layout.addWidget(self.table_label)
            # self.add_widget_main(self.table_label)
        else:
            self.table = QtWidgets.QTableView()
            self.table.setSelectionBehavior(QTableView.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SingleSelection)
            self.model = TableModel(self.saved_configuration_df)
            self.table.setModel(self.model)
            self.table.setColumnWidth(0, 150)
            self.table.setColumnWidth(1, 150)
            self.table.setColumnWidth(2, 150)
            self.table.clicked.connect(self.update_selection)
            self.table.selectionModel().selectionChanged.connect(self.update_selection)
            self.layout.addWidget(self.table)
        
        self.main_widget.setLayout(self.layout)
        self.add_widget_main(self.main_widget)



    def load_table(self):

        self.set_table()
        reset_button_style = self.model_configs.get_application_setting('dialog', 'refresh_button')
        self.reset_button = styled_button.StyledButton(
            label=reset_button_style['label'],
            background_color=reset_button_style['background_color'],
            text_color=reset_button_style['text_color'],
            func_=lambda: self.set_table(),
            hover_background_color=reset_button_style['hover_background_color'],
            hover_text_color=reset_button_style['hover_text_color'],
            border_color=reset_button_style['border_color'],
            valid_state=True
            )
        self.add_button(self.reset_button)

        cancel_button_style = self.model_configs.get_application_setting('dialog', 'cancel_button')
        self.cancel_button = styled_button.StyledButton(
            label=cancel_button_style['label'],
            background_color=cancel_button_style['background_color'],
            text_color=cancel_button_style['text_color'],
            func_=self.cancel_function,
            hover_background_color=cancel_button_style['hover_background_color'],
            hover_text_color=cancel_button_style['hover_text_color'],
            border_color=cancel_button_style['border_color'],
            valid_state=True
            )
        self.add_button(self.cancel_button)

        delete_button_style = self.model_configs.get_application_setting('dialog', 'delete_button')
        self.delete_button = styled_button.StyledButton(
            label=delete_button_style['label'],
            background_color=delete_button_style['background_color'],
            text_color=delete_button_style['text_color'],
            func_=self.delete_function,
            hover_background_color=delete_button_style['hover_background_color'],
            hover_text_color=delete_button_style['hover_text_color'],
            border_color=delete_button_style['border_color'],
            valid_state=False,
            tooltip_text=delete_button_style['tooltip_text'],
            invalid_tooltip_text=delete_button_style['invalid_tooltip_text']
            )
        self.add_button(self.delete_button)

        load_button_style = self.model_configs.get_application_setting('dialog', 'load_button')
        self.load_button = styled_button.StyledButton(
            label=load_button_style['label'],
            background_color=load_button_style['background_color'],
            text_color=load_button_style['text_color'],
            func_=self.load_function,
            hover_background_color=load_button_style['hover_background_color'],
            hover_text_color=load_button_style['hover_text_color'],
            border_color=load_button_style['border_color'],
            valid_state=False,
            tooltip_text=load_button_style['tooltip_text'],
            invalid_tooltip_text=load_button_style['invalid_tooltip_text']
            )
        self.add_button(self.load_button)


    def cancel_function(self):
        '''
        closes the dialog without taking any action
        '''
        self.dialog.close()


    def load_function(self):
        '''
        Loads the selected configuration
        '''
        selection = self.get_selection()
        if selection is None:
            return
        scenario_id = selection['SCENARIO_ID']
        self.data_filter.load_configuration(scenario_id)
        self.dialog.close()
        self.on_load()

    
    def delete_function(self):
        '''
        Deletes the selected configuration
        '''
        selection = self.get_selection()
        if selection is None:
            return
        scenario_id = selection['SCENARIO_ID']
        self.data_filter.delete_configuration(scenario_id)
        self.selection = None
        self.set_table()


    def update_selection(self, index):
        '''
        Updates the selected configuration based on the last row selected.
        '''
        try:
            index.row()
        except Exception as e:
            self.selection = None
            self.load_button.set_valid_state(False)
            self.delete_button.set_valid_state(False)
            return
        self.selection = index.row()
        self.load_button.set_valid_state(True)
        self.delete_button.set_valid_state(True)


    def get_selection(self):
        if self.selection is None:
            return None
        return self.saved_configuration_df.iloc[self.selection]
    
    
    def clear_ui(self):
        """This function clears the UI for the widget
        """        
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)