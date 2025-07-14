'''
This file contains a class that opens a dialog for saving the current scenario
when a user tries to run a new scenario or a scenario that has been modified.
'''

from gui.widgets.common.styled_dialog import StyledDialog
from gui.widgets.common.styled_button import StyledButton

class SaveConfigurationDialog(StyledDialog):
    
    def __init__(self, model_configs, parent, data_filter, start_func, undo_changes_func):
        window_title = 'Save Configuration'
        header_label = 'You must save your changes before running this scenario.'
        entry_label = 'Configuration Name'
        default_entry = data_filter.configuration_name
        self.data_filter = data_filter
        self.start_func = start_func
        self.undo_changes_func = undo_changes_func
        super().__init__(parent=parent, 
                         model_configs=model_configs,
                         window_title=window_title,
                         header_label=header_label,
                         entry_label=entry_label,
                         default_entry=default_entry,
                         allow_cancel=False
                         )
        

        cancel_button_style = self.model_configs.get_application_setting('dialog', 'cancel_button')
        save_button_style = self.model_configs.get_application_setting('dialog', 'save_button')

        self.cancel_button = StyledButton('Cancel', func_=self.dialog.close,
                                            background_color=cancel_button_style['background_color'],
                                            text_color=cancel_button_style['text_color'],
                                            hover_background_color=cancel_button_style['hover_background_color'],
                                            hover_text_color=cancel_button_style['hover_text_color'],
                                            border_color=cancel_button_style['border_color'],
                                            valid_state=True
                                            )
        self.button_box.add_button(self.cancel_button)

        if self.data_filter.scenario_id is not None:
            self.save_button = StyledButton('Overwrite existing scenario', func_=self.save_action_overwite,
                                            background_color=save_button_style['background_color'],
                                            text_color=save_button_style['text_color'],
                                            hover_background_color=save_button_style['hover_background_color'],
                                            hover_text_color=save_button_style['hover_text_color'],
                                            border_color=save_button_style['border_color'],
                                            valid_state=True
                                            )
            self.button_box.add_button(self.save_button)

        self.save_as_button = StyledButton('Save as new scenario', func_=self.save_action_no_overwrite,
                                           background_color=save_button_style['background_color'],
                                           text_color=save_button_style['text_color'],
                                           hover_background_color=save_button_style['hover_background_color'],
                                           hover_text_color=save_button_style['hover_text_color'],
                                           border_color=save_button_style['border_color'],
                                           valid_state=True
                                           )
        self.button_box.add_button(self.save_as_button)

        if self.data_filter.scenario_id is not None:
            self.undo_button = StyledButton('Undo changes', func_=self.undo_changes,
                                                background_color=cancel_button_style['background_color'],
                                                text_color=cancel_button_style['text_color'],
                                                hover_background_color=cancel_button_style['hover_background_color'],
                                                hover_text_color=cancel_button_style['hover_text_color'],
                                                border_color=cancel_button_style['border_color'],
                                                )
            self.button_box.add_button(self.undo_button)

    
    def undo_changes(self) -> None:
        """Undo changes to the data filter and close the dialog."""
        self.data_filter.undo_changes()
        self.undo_changes_func()
        self.dialog.close()

    
    def save_action_overwite(self) -> None:
        """Save the scenario and close the dialog."""
        scenario_name = self.get_entry()
        self.data_filter.save_configuration(scenario_name, overwrite_existing=True)
        self.start_func()
        self.dialog.close()

    def save_action_no_overwrite(self) -> None:
        """Save the scenario and close the dialog."""
        scenario_name = self.get_entry()
        self.data_filter.save_configuration(scenario_name, overwrite_existing=False)
        self.start_func()
        self.dialog.close()