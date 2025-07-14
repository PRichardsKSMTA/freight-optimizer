import sys
from PySide6.QtWidgets import QComboBox, QCompleter
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem

#https://stackoverflow.com/questions/4827207/how-do-i-filter-the-pyqt-qcombobox-items-based-on-the-text-input/4829759#4829759 # noqa
class StyledCompleterComboBox( QComboBox ):
    def __init__( self, items, parent = None, update_func_=None, initial_selection=None, values=None):
        super( StyledCompleterComboBox, self ).__init__( parent )
        self.setStyleSheet('''        
            QComboBox {
                min-width: 100%;
            }
            QAbstractItemView {
                min-width: 200px;
            }            
        ''')
        model = QStandardItemModel()
        self.values = []
        for i,word in enumerate(items):
            item = QStandardItem(word)
            if values is not None:
                self.values.append(values[i])
            else:
                self.values.append(word)
            model.setItem(i, 0, item)
            if initial_selection is not None and word == initial_selection:
                self.setCurrentIndex(i)
        if initial_selection is None:
            self.setCurrentIndex(-1)
            self.text = ''

        self.setFocusPolicy( Qt.StrongFocus )
        self.setEditable( True )
        self.completer = QCompleter( self )

        # always show all completions
        self.completer.setCompletionMode( QCompleter.UnfilteredPopupCompletion )
        self.pFilterModel = QSortFilterProxyModel( self )
        self.pFilterModel.setFilterCaseSensitivity( Qt.CaseInsensitive )

        self.completer.setPopup( self.view() )
        self.setCompleter( self.completer )

        self.lineEdit().textEdited.connect( self.pFilterModel.setFilterFixedString )
        self.completer.activated.connect(self.setTextIfCompleterIsClicked)

        self.setModel(model)
        self.setModelColumn(0)

        if not update_func_ is None:
            self.currentIndexChanged.connect(lambda x: update_func_(self.values[x]))

    def setModel( self, model ):
        super(StyledCompleterComboBox, self).setModel( model )
        self.pFilterModel.setSourceModel( model )
        self.completer.setModel(self.pFilterModel)

    def setModelColumn( self, column ):
        self.completer.setCompletionColumn( column )
        self.pFilterModel.setFilterKeyColumn( column )
        super(StyledCompleterComboBox, self).setModelColumn( column )


    def view( self ):
        return self.completer.popup()

    def index( self ):
        return self.currentIndex()

    def setTextIfCompleterIsClicked(self, text):
      if text:
        index = self.findText(text)
        self.setCurrentIndex(index)
