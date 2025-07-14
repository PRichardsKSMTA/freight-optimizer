from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt


class StyledVBoxLayout(QVBoxLayout):
	'''
	class to keep the styling of the vertical layout consistent
	'''
	def __init__(self, margins=(5, 8, 5, 2)):
		"""_summary_

		Args:
			margins (tuple, optional): Margins for the layout, as a
				tuple of the form (top, left, bottom, right).
				Defaults to (5, 8, 5, 2).
		"""		
		super(StyledVBoxLayout, self).__init__()
		self.setSpacing(0)
		self.setContentsMargins(*margins)
		self.setAlignment(Qt.AlignTop)