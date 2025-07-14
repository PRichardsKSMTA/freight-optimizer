import json
import os

from PySide6.QtCore import QThreadPool

from gui.widgets.common.styled_line_edit import StyledLineEdit


class ModelConfiguration:
	'''
	This class stores and updates model configurations. This class will be passed
	to the model starter
	'''
	def __init__(self, params_filename: str, gui_configuration_filename: str,
			  app_threadpool: QThreadPool=None):
		self.params_filename = params_filename
		self.gui_configuration_filename = gui_configuration_filename
		self.app_threadpool = app_threadpool
		self.configuration_name = None
		self.configuration_note = None
		self.configuration_name_text_edit = None
		self.configuration_note_text_edit = None
		self.initialize()


	def initialize(self, params_filename: str=None, 
				configuration_name: str=None) -> None:
		'''
		initializes the class based on the initial configuration files. 
			Moving this to a separate function so that the configuration 
			can be easily reset.
		'''
		if configuration_name is not None:
			params_filename = os.path.join('scripts', 'gui', 'saved_configurations', 
								  configuration_name + '.json')
		if params_filename is None:
			params_filename = self.params_filename
		self.read_params(params_filename, self.gui_configuration_filename)
		if 'configuration_name' in self.params.keys():
			self.configuration_name = self.params['configuration_name']
		else:
			self.configuration_name = None


	def read_params(self, params_filename: str, gui_configuration_filename: str) -> None:
		"""This function reads the parameters file at the given location and stores 
			the parameters in the self.params dictionary.

		Args:
			params_filename (str, optional): Filename for the json file with the parameters 
				specified for this optimization run. Defaults to None.
			gui_configuration_filename (str, optional): The filename for the json file 
				containing the GUI configurations. Defaults to None.

		Raises:
			ValueError: If the parameters file cannot be read
			ValueError: If the GUI configuration file cannot be read
		"""		
		try:
			json_file = open(params_filename, "r")
			self.params = json.load(json_file)
			json_file.close()
		except Exception as ee:
			message = 'Unable to read input parameters file at location: ' + \
				params_filename + ". Exception was: " + str(ee)
			raise ValueError(message)

		try:
			json_file = open(gui_configuration_filename, "r")
			self.params.update(json.load(json_file))
			json_file.close()
		except Exception as ee:
			message = 'Unable to read input parameters file at location: ' + \
				params_filename + ". Exception was: " + str(ee)
			raise ValueError(message)

	
	def get_model_state(self, model_name: str):
		return self.params["model"][model_name]
	

	def toggle_model_state(self, model_name: str):
		self.params["model"][model_name] = not self.params["model"][model_name]


	def set_model_state(self, model_name: str, state: bool):
		self.params["model"][model_name] = state


	def get_max_deadhead(self) -> int:
		"""This function returns the maximum deadhead for the model.

		Returns:
			int: The maximum deadhead for the model.
		"""		
		return self.params['max_deadhead']


	def update_max_deadhead(self, new_max_deadhead: int) -> None:
		"""This function updates the maximum deadhead for the model.

		Args:
			new_max_deadhead (int): The new maximum deadhead for the model.
		"""		
		self.params['max_deadhead'] = new_max_deadhead


	def get_max_deadhead_range(self) -> tuple:
		"""This function returns the range of values for the maximum deadhead selector.

		Returns:
			tuple: The range of values for the maximum deadhead selector, in the
				form (min_deadhead, max_deadhead)
		"""		
		min_deadhead = self.params['application_settings']['configuration_panel']\
			['model_parameters_groupbox']['max_deadhead_selector']['minimum']
		max_deadhead = self.params['application_settings']['configuration_panel']\
			['model_parameters_groupbox']['max_deadhead_selector']['maximum']
		return min_deadhead, max_deadhead
	

	def get_max_capacity(self) -> int:
		"""This function returns the maximum capacity for the model.

		Returns:
			int: The maximum capacity for the model.
		"""		
		return self.params['max_capacity']
	

	def update_max_capacity(self, new_max_capacity: int) -> None:
		"""This function updates the maximum capacity for the model.

		Args:
			new_max_capacity (int): The new maximum capacity for the model.
		"""		
		self.params['max_capacity'] = new_max_capacity


	def get_min_miles(self) -> int:
		"""This function returns the minimum miles for the model.

		Returns:
			int: The minimum miles for the model.
		"""		
		return self.params['min_miles']


	def update_min_miles(self, new_min_miles: int) -> None:
		"""This function updates the minimum miles for the model.

		Args:
			new_min_miles (int): The new minimum miles for the model.
		"""		
		self.params['min_miles'] = new_min_miles


	def get_max_capacity_range(self) -> tuple:
		"""This function returns the range of values for the maximum capacity selector.

		Returns:
			tuple: The range of values for the maximum capacity selector.
		"""		
		min_capacity = self.params['application_settings']['configuration_panel']['model_parameters_groupbox']['max_capacity_selector']['minimum']
		max_capacity = self.params['application_settings']['configuration_panel']['model_parameters_groupbox']['max_capacity_selector']['maximum']
		return min_capacity, max_capacity


	def update_mileage_rate(self, new_mileage_rate: float) -> None:
		"""This function updates the mileage rate for the model.

		Args:
			new_mileage_rate (float): The new mileage rate for the model.
		"""		
		self.params['cost_per_empty_mile'] = new_mileage_rate


	def get_mileage_rate_range(self) -> tuple:
		"""This function returns the range of values for the mileage rate selector.

		Returns:
			tuple: The range of values for the mileage rate selector, in the
				form (min_mileage, max_mileage)
		"""		
		min_mileage = self.params['application_settings']['configuration_panel']['model_parameters_groupbox']['mileage_rate_selector']['minimum']
		max_mileage = self.params['application_settings']['configuration_panel']['model_parameters_groupbox']['mileage_rate_selector']['maximum']
		return min_mileage, max_mileage
	
	def get_mileage_rate(self) -> float:
		"""This function returns the mileage rate for the model.

		Returns:
			float: The mileage rate for the model.
		"""		
		return self.params['cost_per_empty_mile']
	

	def update_margin_target(self, new_margin_target: float):
		self.params['margin_target'] = new_margin_target


	def get_margin_target_range(self):
		min_margin_target = self.params['application_settings']['configuration_panel']['model_parameters_groupbox']['margin_target_selector']['minimum']
		max_margin_target = self.params['application_settings']['configuration_panel']['model_parameters_groupbox']['margin_target_selector']['maximum']
		return min_margin_target, max_margin_target
		

	def get_margin_target(self) -> float:
		return self.params['margin_target']
	

	def get_application_setting(self, setting_name:str, subsetting_name: str=None) -> object:
		"""This function returns the value of the given application setting. 
		If a subsetting name is provided, the value of the subsetting is returned.

		Args:
			setting_name (str): The name of the setting to retrieve.
			subsetting_name (str, optional): The name of the subsetting to retrieve. 
			Defaults to None.

		Returns:
			object: The value of the specified setting or subsetting.
		"""		
		if subsetting_name is not None:
			return self.params['application_settings'][setting_name][subsetting_name]
		return self.params['application_settings'][setting_name]
	

	def bind_configuration_name_entry(self, text_edit: StyledLineEdit):
		"""This function binds the given text edit to the configuration note.

		Args:
			text_edit (QTextEdit): The text edit to bind to the configuration note.
		"""
		self.configuration_name_text_edit = text_edit

	def bind_configuration_note_entry(self, text_edit: StyledLineEdit):
		"""This function binds the given text edit to the configuration note.

		Args:
			text_edit (QTextEdit): The text edit to bind to the configuration note.
		"""
		self.configuration_note_text_edit = text_edit


	def update_configuration_name(self, new_name: str):
		"""This function updates the configuration name

		Args:
			new_name (str): the new name for this configuration
		"""		
		self.configuration_name = new_name
		if self.configuration_name_text_edit is not None:
			try:
				curr_text = self.configuration_name_text_edit.entry.text()
				if curr_text != new_name:
					self.configuration_name_text_edit.entry.setText(new_name)
			except Exception as ee:
				pass
			

	def update_configuration_note(self, new_note: str):
		"""This function updates the configuration note

		Args:
			new_note (str): the new note for this configuration
		"""		
		self.configuration_note = new_note
		if self.configuration_note_text_edit is not None:
			try:
				curr_text = self.configuration_note_text_edit.entry.text()
				if curr_text != new_note:
					self.configuration_note_text_edit.entry.setText(new_note)
			except Exception as ee:
				pass


	def get_setting(self, setting:str) -> object:
		'''
		returns the setting for the given name

		Args:
			setting (str): The name of the setting to retrieve.

		Returns:
			The value of the specified setting.
		'''
		return self.params[setting]