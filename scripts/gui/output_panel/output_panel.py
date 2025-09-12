
from ..widgets.colored_widget import ColoredWidget
from ..widgets.common.styled_vbox_layout import StyledVBoxLayout
from .trial_groupbox import TrialGroupbox


class OutputPanel(ColoredWidget):
	'''
	This panel is responsible for displaying the output of the optimization. This includes a table
	showing all current trials and their status.
	'''

	def __init__(self, configs):
		panel_color = configs.get_application_setting('output_panel', 'background_color')
		super(OutputPanel, self).__init__(panel_color)
		self.configs = configs

		self.trial_groupbox = TrialGroupbox(configs)

		self.layout = StyledVBoxLayout()
		self.layout.addWidget(self.trial_groupbox)
		self.setLayout(self.layout)


	def add_runnable(self, runnable_id: str, client_name: str, model_type: str):
		self.trial_groupbox.add_runnable(runnable_id, client_name=client_name, model_type=model_type)


	def update_status(self, runnable_id, status):
		self.trial_groupbox.update_status(runnable_id, status)

	def update_fields(self, *args, **kwargs):
		self.trial_groupbox.update_fields(*args, **kwargs)


	def rebuild_model(self):
		self.trial_groupbox.rebuild_model()

