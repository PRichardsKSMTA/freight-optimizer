from PySide6.QtWidgets import QCheckBox

class StyledCheckbox(QCheckBox):
    '''
    This is a common checkbox that will maintain the same style 
    across the application
    '''

    def __init__(self, text, parent=None):
        super(StyledCheckbox, self).__init__(text, parent)
        self.setStyleSheet('''
            QCheckBox {
                font-size: 12px;
                font-weight:500;
                border-radius: 5px;
                padding: 0px;
                padding-left: 5px;
                padding-right: 5px;
                margin: 0px;
                
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
        ''')
