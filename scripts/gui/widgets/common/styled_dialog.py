from PySide6.QtWidgets import  QDialog, QWidget, QPushButton
from typing import Callable
from PySide6.QtCore import Qt


from .styled_button import StyledButton
from . styled_label import StyledLabel
from .styled_line_edit import StyledLineEdit
from .styled_vbox_layout import StyledVBoxLayout
from .styled_button_box import StyledButtonBox

class StyledDialog(QWidget):
	"""This widget provides the styled dialog format that should be used for dialogs throughout
	this application.

	"""
	def __init__(self,
			  window_title: str,
			  model_configs, 
			  parent: QWidget,
			  header_label: str=None,
			  entry_label: str=None,
			  save_action: Callable=None,
			  default_entry: str=None,
			  allow_cancel: bool=False
		):
		super(StyledDialog, self).__init__(parent=parent)
		self.model_configs = model_configs
		self.save_action = save_action
		self.dialog = QDialog()
		self.dialog.setStyleSheet('''
			QDialog {
				background-color: %s;
				color: #000000;
				border-radius: 5px;
				padding: 5px;
			}
		''' % self.model_configs.get_application_setting('dialog', 'background_color'))

		self.dialog.setWindowTitle(window_title)
		self.layout = StyledVBoxLayout()
		
		#Dialog header
		if header_label is not None:
			self.label = StyledLabel(header_label, app_configs=self.model_configs)
			self.layout.addWidget(self.label)

		#main dialog layout
		self.main_layout = StyledVBoxLayout()

		#Dialog entry
		if entry_label is not None:
			self.entry_widget = StyledLineEdit(self.model_configs, self, entry_label, default_entry=default_entry)
			self.main_layout.addWidget(self.entry_widget)

		self.layout.addLayout(self.main_layout)

		self.button_box = StyledButtonBox()
		if allow_cancel:
			cancel_button_style = self.model_configs.get_application_setting('dialog', 'cancel_button')
			self.cancel_button = StyledButton(
				label=cancel_button_style['label'],
				background_color=cancel_button_style['background_color'],
				text_color=cancel_button_style['text_color'],
				func_=self.cancel_function)
			self.button_box.add_button(self.cancel_button)

		if not save_action is None:
			self.save_button = StyledButton('Save', func_=self.save_function)
			self.button_box.addButton(self.save_button)

		self.layout.addWidget(self.button_box, alignment=Qt.AlignBottom)
		self.dialog.setLayout(self.layout)


	def add_button(self, button: QPushButton):
		"""This function adds a button to the button box

		Args:
			button (QButton): The button to add to the button box
		"""		
		self.button_box.add_button(button)


	def add_widget_main(self, widget: QWidget):
		"""Adds a widget to the main layout of this widget

		Args:
			widget (QWidget): the widget to be added
		"""		
		self.main_layout.addWidget(widget)


	def open_dialog(self):
		self.dialog.open()


	def cancel_function(self):
		'''
		closes the dialog without taking any action
		'''
		self.dialog.close()

	
	def save_function(self):
		'''
		closes the dialog and takes the save action. If an entry_label is provided,
		then it will pass the entry as the first argument to the save_action function.
		'''
		self.save_action(self.entry_widget.get_entry())
		self.dialog.close()

	
	def get_entry(self):
		'''
		returns the entry in the entry widget
		'''
		return self.entry_widget.get_entry()
	