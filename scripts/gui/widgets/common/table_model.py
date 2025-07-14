'''
This is a model for displaying data from a pandas.DataFrame in a table. This
needs to be connected to a QtWidgets.QTableView() in order to display. The
syntax for this looks like:

QtWidgets.QTableView()		

table = QtWidgets.QTableView()
model = table_model.TableModel(df)
table.setModel(model)

'''
import pandas
from PySide6 import QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class TableModel(QtCore.QAbstractTableModel):
	'''
	This is a class for managing the data in the load configuration table.
	'''

	def __init__(self, data, color_dict=None):
		super(TableModel, self).__init__()
		self._data = data
		self.color_dict = color_dict
		#set width of the last column
		

	def data(self, index, role):
		if role == Qt.DisplayRole:
			value = self._data.iloc[index.row(), index.column()]
			if pandas.isnull(value): 
				return None
			return str(value)
		if self.color_dict is not None:
			row_status = self._data.iloc[index.row()]['Status']
			if row_status in self.color_dict.keys():
				if role == Qt.BackgroundRole:
					
					background_color = self.color_dict[row_status]['background_color']
					return QColor(background_color)

				if role == Qt.ForegroundRole:
					text_color = self.color_dict[row_status]['text_color']
					return QColor(text_color)

	def rowCount(self, index) -> int:
		#returns the row count. This overwrites the default function
		#(index argument not necessary for this function, but is used in parent)
		return self._data.shape[0]

	def columnCount(self, index) -> int:
		#returns the column count. This overwrites the default function 
		#(index not necessary for this function, but is used in parent)
		return self._data.shape[1]

	def headerData(self, section, orientation, role) -> str:
		# section is the index of the column/row.
		if role == Qt.DisplayRole:
			if orientation == Qt.Horizontal:
				return str(self._data.columns[section])

			if orientation == Qt.Vertical:
				return str(self._data.index[section])