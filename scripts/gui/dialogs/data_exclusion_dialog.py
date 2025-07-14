
from PySide6.QtWidgets import QMessageBox

from gui.configuration_panel.data_exclusion_groupbox import DataExclusionGroupbox
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout
from ..widgets.common import styled_dialog
from ..widgets.common.styled_button import StyledButton



class DataExclusionDialog(styled_dialog.StyledDialog):
    '''
    This is a dialog box for loading a previosuly saved configuration.
    This will load the names of all previously saved configurations and allow the user to select one.
    '''

    def __init__(self, model_configs, data_filter, parent, groupbox: DataExclusionGroupbox):
        """_summary_

        Args:
            model_configs (_type_): _description_
            data_filter (_type_): _description_
            groupbox (DataExclusionGroupbox): This must be stored in the main window for thread safety
        """        
        self.dialog_configs = model_configs.get_application_setting('configuration_panel', 'data_exclusion')
        super(DataExclusionDialog, self).__init__(
            parent=parent,
            window_title=self.dialog_configs['title'],
            save_action=None,
            entry_label=None,
            model_configs=model_configs
        )
        self.data_filter = data_filter
        self.data_filter.screenshots = []
        self.data_exclusion_groupbox = groupbox
        self.model_configs = model_configs
        self.load_ui()

        self.dialog.closeEvent = lambda x: self.closeEvent(x)


    def closeEvent(self, event) -> None:
        """This function is called when the dialog is closed.
        """        
        if event.spontaneous():
            if self.data_filter.check_scenario_changed(self.data_filter.screenshots[0]):
                confirmation = QMessageBox.question(self, "Close exclusion dialog", "Close Exclusion Dialog without saving?", 
                                                    QMessageBox.Yes | QMessageBox.No)
                if confirmation == QMessageBox.Yes:
                    self.cancel_function()
                    event.accept()  # Close the app
                else:
                    event.ignore() 
            else:
                event.accept()
        else:
            event.accept()
    

    def load_ui(self) -> None:
        """This function loads the UI for this dialog box."""
        self.layout = StyledVBoxLayout()
        self.add_widget_main(self.data_exclusion_groupbox)

        #add a StyledButton to close the dialog with cancel
        cancel_button_style = self.model_configs.get_application_setting('dialog', 'cancel_button')
        self.cancel_button = StyledButton(
            label='Cancel',
            background_color=cancel_button_style['background_color'],
            text_color=cancel_button_style['text_color'],
            func_=self.cancel_function,
            hover_background_color=cancel_button_style['hover_background_color'],
            hover_text_color=cancel_button_style['hover_text_color'],
            border_color=cancel_button_style['border_color'],
            valid_state=True
        )
        self.add_button(self.cancel_button)

        #add a StyledButton to close the dialog
        submit_button_style = self.model_configs.get_application_setting('dialog', 'save_button')
        self.submit_button = StyledButton(
            label='Submit',
            background_color=submit_button_style['background_color'],
            text_color=submit_button_style['text_color'],
            func_=self.submit_function,
            hover_background_color=submit_button_style['hover_background_color'],
            hover_text_color=submit_button_style['hover_text_color'],
            border_color=submit_button_style['border_color'],
            valid_state=True
            )
        self.add_button(self.submit_button)

    
    def submit_function(self, i=None) -> None:
        '''
        closes the dialog and saves the configuration
        '''
        self.dialog.close()


    def cancel_function(self, i=None) -> None:
        '''
        closes the dialog without taking any action
        '''
        self.dialog.close()
        self.data_filter.reset_to_last_screenshot()

