from PySide6.QtWidgets import QHBoxLayout
from PySide6.QtCore import Qt


class StyledHBoxLayout(QHBoxLayout):
	'''
	class to keep the styling of the vertical layout consistent
	'''
	def __init__(self, margins=(5, 5, 5, 5)):
		super(StyledHBoxLayout, self).__init__()
		self.setSpacing(5)
		self.setContentsMargins(*margins)
		self.setAlignment(Qt.AlignLeft)