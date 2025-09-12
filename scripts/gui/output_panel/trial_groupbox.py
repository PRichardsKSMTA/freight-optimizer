
from PySide6.QtWidgets import QWidget , QTableView, QAbstractItemView
import pandas
import datetime

from ..widgets.common.table_model import TableModel
from ..widgets.common.styled_groupbox import StyledGroupBox
from ..widgets.common.styled_hbox_layout import StyledHBoxLayout
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout

class TrialGroupbox(QWidget): 
	'''
	This class is a widget that displays the status of the trials for this instance of the application.
	This trial box will show completed, queued, running, and failed trials.
	'''

	def __init__(self, configs, parent=None):

		super(TrialGroupbox, self).__init__(parent)
		self.setStyleSheet('''QGroupBox { }''')

		group_box = StyledGroupBox("Optimization Runs", app_configs=configs)
		self.selection = None
		self.configs = configs

		self.display_columns = ['Client', 'Status', 'Start Time', 'End Time', 'Last Log Message', 
						  'Run ID', 'Model', 'Number of Trips', 'Gross Profit']
		vbox = StyledVBoxLayout()
		vbox.setContentsMargins(10, 20, 10, 10)
		self.run_df = pandas.DataFrame(columns=['runnable_id', 'Run ID', 'Model', 'Client', 'Status', 
			'Start Time', 'End Time', 'Number of Trips', 'Gross Profit', 'Last Log Message'])

		self.table = QTableView()
		self.table.setSelectionBehavior(QTableView.SelectItems)
		self.table.setSelectionMode(QAbstractItemView.SingleSelection)
		self.model = TableModel(self.run_df[self.display_columns], 
						  color_dict=self.configs.params['application_settings']['output_panel']['run_table'])
		self.table.setModel(self.model)
		self.table.clicked.connect(self.update_selection)
		self.table.selectionModel().selectionChanged.connect(self.update_selection)

		vbox.addWidget(self.table)

		self.init_button_group()
		vbox.addWidget(self.button_group)

		group_box.setLayout(vbox)

		layout = StyledVBoxLayout()
		layout.addWidget(group_box)
		self.setLayout(layout)


	def add_runnable(self, runnable_id: str, client_name: str, model_type: str) -> None:
		'''
		Adds a runnable to the table of runnables	

		Args:
			runnable_id (str): The id of the runnable to add to the table	
		'''
		runnable_df = pandas.DataFrame({
			'runnable_id': [runnable_id],
			'Run ID': [None],
			'Model': [model_type],
			'Client': [client_name],
			'Status': ['queued'],
			'Start Time': [datetime.datetime.now().strftime('%I:%M %p')],
			'End Time': [None],
			'Number of Trips': [None],
			'Gross Profit': [None],
			'Last Log Message': [None]
		})
		self.run_df = pandas.concat([self.run_df, runnable_df], ignore_index=True).reset_index(drop=True)
		self.rebuild_model()


	def update_fields(self, runnable_id, field_names, new_values):
		'''
		Updates a field in the table of runnables
		'''
		for field_name, new_value in zip(field_names, new_values):
			if field_name in ['Start Time', 'End Time']:
				new_value = pandas.to_datetime(new_value).strftime('%I:%M %p')
			if field_name == 'Gross Profit':
				new_value = '{:,}'.format(int(new_value))
			self.run_df.loc[self.run_df['runnable_id'] == runnable_id, field_name] = new_value
		self.rebuild_model()


	def update_status(self, runnable_id: str, status: str) -> None:
		'''
		Updates the status of a given row, identified by the runnable_id

		Args:
			runnable_id (str): The id of the runnable to update
			status (str): The new status of the runnable
		'''
		self.run_df.loc[self.run_df['runnable_id'] == runnable_id, 'Status'] = status
		self.rebuild_model()


	def rebuild_model(self) -> None:
		'''
		rebuilds the table model (for updates)
		'''
		self.model = TableModel(self.run_df[self.display_columns], 
			color_dict=self.configs.params['application_settings']['output_panel']['run_table'])
		self.table.setModel(self.model)
		if self.selection is not None:
			self.table.selectRow(self.selection)


	def get_selected_runnable_id(self) -> str:
		'''
		returns the runnable_id of the selected row

		Returns:
			str: the runnable_id of the selected row
		'''
		selected_index = self.table.selectedIndexes()[0]
		selected_runnable_id = self.run_df.loc[selected_index.row(), 'runnable_id']
		return selected_runnable_id
	

	def update_selection(self, index: int) -> None:
		'''
		Updates the selected configuration based on the last row selected.

		Args:
			index (int): The index of the row selected
		'''
		try:
			index.row()
		except Exception as e:
			self.selection = None
			self.button_group.update_selection(None)
			return
		self.selection = index.row()
		self.button_group.update_selection(self.selection)


	def init_button_group(self) -> None:
		'''
		Initializes the button group
		'''
		self.button_group = TrialButtonGroup(configs=self.configs, selection=self.selection)


class TrialButtonGroup(QWidget):
	'''
	This class allows for actions on a selected trial
	'''

	def __init__(self, configs, selection):
		super(TrialButtonGroup, self).__init__()
		self.configs = configs
		self.layout = StyledHBoxLayout()
		self.selection = selection

		self.setLayout(self.layout)


	def update_selection(self, new_selection):
		if new_selection == self.selection:
			self.selection = None
		self.selection = new_selection