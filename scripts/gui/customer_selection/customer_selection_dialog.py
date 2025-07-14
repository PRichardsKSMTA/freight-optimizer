from typing import Callable

from PySide6.QtWidgets import QWidget

from ..widgets.common.styled_dialog import StyledDialog
from ..widgets.common.styled_button import StyledButton
from ..widgets.common.styled_hbox_layout import StyledHBoxLayout
from ..widgets.common.styled_combobox import StyledComboBox
from gui.data_configuration.data_filter import DataFilter
from gui.configuration import ModelConfiguration


class CustomerSelectionDialog(StyledDialog):
	'''
	This dialog is the first thing users will see when opening the app. The user will select
	a customer from a dropdown list of customers.
	'''
	def __init__(self, 
			  data_filter: DataFilter,
			  model_configs: ModelConfiguration,
			  on_load: Callable,
			  parent: QWidget,
			  initial_load: bool=False):
		"""This is a dialog box for selecting the customer and other filters for pulling in the dataset.

		Args:
			data_filter (DataFilter): a DataFilter object for this instance
			model_configs (Configuration): a ModelConfiguration object for this instance
			on_load (Callable): a function to call when the user clicks the load button
			initial_load (bool, optional): Whether this is the initial customer load screen or
				is opened to change the initial selection. If it is the initial screen, then
				user will be required to make a selection. Otherwise, the user will be able to
				cancel and return to their current scenario. Defaults to False.
		"""
		self.dialog_configs = model_configs.get_application_setting(
			'configuration_panel',
			'configuration_customer_information'
			)['customer_selection_dialog']
		super(CustomerSelectionDialog, self).__init__(
			window_title=self.dialog_configs['title'],
			save_action=None,
			entry_label=None,
			model_configs=model_configs,
			parent=parent
		)
		self.on_load = on_load
		self.initial_load = initial_load
		self.data_filter = data_filter
		self.model_configs = model_configs
		self.dialog.setFixedWidth(self.model_configs.get_application_setting('dialog', 'width'))

		self.load_ui()


	def load_ui(self) -> None:
		"""Loads the UI for this dialog
		"""		
		self.customer_selector = CustomerSelector(
			configs=self.model_configs,
			data_filter=self.data_filter,
			validation_function=self.validate_customer)
		self.add_widget_main(self.customer_selector)

		if self.initial_load:
			cancel_button_style = self.model_configs.get_application_setting('dialog', 'cancel_button')
			self.cancel_button = StyledButton(
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

		load_button_style = self.model_configs.get_application_setting('configuration_panel', 'configuration_customer_information')['load_customer_button']
		self.load_button = StyledButton(
			label=load_button_style['label'],
			background_color=load_button_style['background_color'],
			text_color=load_button_style['text_color'],
			func_=self.load_function,
			hover_background_color=load_button_style['hover_background_color'],
			hover_text_color=load_button_style['hover_text_color'],
			border_color=load_button_style['border_color'],
			valid_state=self.validate_customer(set_button_state=False),
			tooltip_text=load_button_style['tooltip_text'],
			invalid_tooltip_text=load_button_style['invalid_tooltip_text']
			)
		self.add_button(self.load_button)


	def cancel_function(self) -> None:
		'''
		closes the dialog without taking any action
		'''
		self.dialog.close()


	def load_function(self) -> None:
		'''
		Loads the selected configuration
		'''
		client_id = self.customer_selector.get_selection()
		if client_id is None or client_id == '':
			return
		self.on_load(client_id)
		self.dialog.close()

	
	def validate_customer(self, set_button_state: bool=True) -> bool:
		"""Validates the customer selection

		Args:
			set_button_state (bool, optional): Whether to set the button state to valid or not. 
				Defaults to True.
		Returns:
			bool: True if the customer is valid, False otherwise
		"""		
		client_id = self.customer_selector.get_selection()
		valid = False
		if client_id in self.customer_selector.get_customer_choices()[1]:
			valid = True
		if set_button_state:
			self.load_button.set_valid_state(valid)
		return valid

	
class CustomerSelector(QWidget):
	"""The widget is used to create a label and dropdown selector for choosing the customer
	"""
	def __init__(self, configs: ModelConfiguration, data_filter: DataFilter, validation_function: Callable):
		"""Initializer for this class

		Args:
			configs (Configuration): the configuration object for this instance of the app
			data_filter (DataFilter): the data filter object for this instance of the app
			validation_function (Callable): the function to call to validate the customer selection
		"""		
		self.dialog_configs = configs.get_application_setting(
			'configuration_panel',
			'configuration_customer_information'
			)['customer_selection_dialog']
		super(CustomerSelector, self).__init__()
		self.configs = configs
		self.data_filter = data_filter
		self.validation_function = validation_function

		self._setup_ui()


	def _setup_ui(self) -> None:
		"""Adds a label and dropbox to the layout
		"""		
		self.layout = StyledHBoxLayout()
		self.setLayout(self.layout)
		dropdown_choices, dropdown_values = self.get_customer_choices()
		self.dropdown_items =  {dropdown_choices[i]: dropdown_values[i] for i in range(len(dropdown_choices))}
		self.customer_selector = StyledComboBox(
			app_configs=self.configs,
			label_text=self.dialog_configs['label'],
			dropdown_choices=dropdown_choices,
			validation_function=self.validation_function
			)
		self.layout.addWidget(self.customer_selector)


	def get_selection(self) -> str:
		"""Returns the selected customer

		Returns:
			str: the selected customer
		"""		
		customer_name = self.customer_selector.get_selection()
		client_id = self.dropdown_items[customer_name]
		return client_id


	def get_customer_choices(self) -> list:
		"""This function return a list of customer options to choose from
		for the dropdown selector

		Returns:
			list: a list of customer names that can be chosen from the dropdown selector.
		"""
		customer_df = self.data_filter.get_client_picklist()
		return customer_df[self.dialog_configs['display_field']].tolist(), customer_df[self.dialog_configs['value_field']].tolist()