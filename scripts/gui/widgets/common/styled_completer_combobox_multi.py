import numpy
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox
from PySide6.QtGui import QFontMetrics, QPalette, QStandardItem


class StyledCompleterComboBoxMulti(QComboBox):

    # Subclass Delegate to increase item height
    class Delegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(20)
            return size

    def __init__(self, *args, **kwargs):
        if 'update_func_' in kwargs:
            self.update_func_ = kwargs['update_func_']
            del kwargs['update_func_']
        else:
            self.update_func_ = None
        super().__init__(*args, **kwargs)
        self.setStyleSheet('''        
            QComboBox {
                min-width: 100%;
            }
            QAbstractItemView {
                min-width: 200px;
            }        
        ''')
        self.values = []
        if 'initial_selection' in kwargs and kwargs['initial_selection'] is not None:
            initial_selection = kwargs['initial_selection']
            for entry in initial_selection:
                index = initial_selection.index(entry)
                item = self.model().item(index.row())
                item.setCheckState(Qt.Checked)
        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        # Make the lineedit the same color as QPushButton
        # palette = qApp.palette()
        palette = self.palette()
        palette.setBrush(QPalette.Base, palette.button())
        self.lineEdit().setPalette(palette)

        # Use custom delegate
        self.setItemDelegate(StyledCompleterComboBoxMulti.Delegate())

        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.updateText)

        # Hide and show popup when clicking the line edit
        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False

        # Prevent popup from closing when clicking on an item
        self.view().viewport().installEventFilter(self)

    def resizeEvent(self, event):
        # Recompute text to elide as needed
        # self.updateText()
        super().resizeEvent(event)

    def eventFilter(self, object, event):

        if object == self.lineEdit():
            if event.type() == QEvent.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return False

        if object == self.view().viewport():
            if event.type() == QEvent.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                item = self.model().item(index.row())

                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                return True
        return False

    def showPopup(self):
        super().showPopup()
        # When the popup is displayed, a click on the lineedit should close it
        self.closeOnLineEditClick = True

    def hidePopup(self):
        super().hidePopup()
        # Used to prevent immediate reopening when clicking on the lineEdit
        self.startTimer(100)
        # Refresh the display text when closing
        # print ('hide event')
        # self.updateText()

    def timerEvent(self, event):
        # After timeout, kill timer, and reenable click on line edit
        self.killTimer(event.timerId())
        self.closeOnLineEditClick = False

    def updateText(self):
        texts = []
        idcs = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                texts.append(self.model().item(i).text())
                idcs.append(i)
        text = ", ".join(texts)

        # Compute elided text (with "...")
        metrics = QFontMetrics(self.lineEdit().font())
        elidedText = metrics.elidedText(text, Qt.ElideMiddle, self.lineEdit().width())
        self.lineEdit().setText(elidedText)
        if self.update_func_ is not None:
            self.update_func_([x for x in numpy.array(self.values)[idcs]])
            # self.update_func_(texts)

    def addItem(self, text, data=None, checked=False):
        item = QStandardItem()
        item.setText(text)
        if data is None:
            self.values.append(text)
        else:
            self.values.append(data)
        if data is None:
            item.setData(text)
        else:
            item.setData(data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        if checked:
            item.setData(Qt.Checked, Qt.CheckStateRole)
        else:
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts, datalist=None, initial_selection=[]):
        for i, text in enumerate(texts):
            checked = False
            if i in initial_selection:
                checked = True
            try:
                data = datalist[i]
            except (TypeError, IndexError):
                data = None
            self.addItem(text, data, checked=checked)

        selected = []
        if initial_selection is not None:
            for i in initial_selection:
                selected.append(texts[i])
        selected = [str(x) for x in selected]
        text = ", ".join(selected)

        metrics = QFontMetrics(self.lineEdit().font())
        if text == '':
            elidedText = ' '
        else:
            elidedText = metrics.elidedText(text, Qt.ElideMiddle, self.lineEdit().width())
        self.lineEdit().setText(elidedText)
        self.setPlaceholderText('Select...')

    def currentData(self):
        # Return the list of selected items data
        res = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                res.append(self.model().item(i).data())
        return res