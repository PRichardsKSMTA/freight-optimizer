from PySide6.QtWidgets import QPushButton

class StyledButton(QPushButton):
    '''
    This is a styled button class. This is used to create buttons with a consistent style across
    the application.    
    '''
    def __init__(   self,
                    label,
                    func_,
                    background_color='#000000',
                    text_color='#FFFFFF',
                    hover_background_color='#FFFFFF',
                    hover_text_color='#000000',
                    border_color='#000000',
                    parent=None,
                    tooltip_text=None,
                    valid_state=True,
                    invalid_background_color='#cc0011',
                    invalid_text_color='#FFFFFF',
                    invalid_hover_background_color='#80000b',
                    invalid_hover_text_color='#FFFFFF',
                    invalid_border_color='#000000',
                    invalid_tooltip_text=None,
                    padding: int=5,
                    margins: tuple=(0,0,0,0),
                    max_width: int=None,
                ):
        super().__init__(label, parent)
        self.func_ = func_
        self.background_color = background_color
        self.text_color = text_color
        self.hover_background_color = hover_background_color
        self.hover_text_color = hover_text_color
        self.border_color = border_color
        self.tooltip_text = tooltip_text
        self.invalid_background_color = invalid_background_color
        self.invalid_text_color = invalid_text_color
        self.invalid_hover_background_color = invalid_hover_background_color
        self.invalid_hover_text_color = invalid_hover_text_color
        self.invalid_border_color = invalid_border_color
        self.invalid_tooltip_text = invalid_tooltip_text
        self.padding = padding
        self.margins = margins

        if max_width is not None:
            self.setMaximumWidth(max_width)

        # if valid_state:
        #     try:
        #         self.clicked.disconnect()
        #     except:
        #         pass
        #     self.clicked.connect(func_)

        self.set_valid_state(valid_state)

    
    def set_valid_state(self, valid_state: bool=True):
        if valid_state:
            background_color = self.background_color
            text_color = self.text_color
            hover_background_color = self.hover_background_color
            hover_text_color = self.hover_text_color
            border_color = self.border_color
            tooltip_text = self.tooltip_text
        else:
            background_color = self.invalid_background_color
            text_color = self.invalid_text_color
            hover_background_color = self.invalid_hover_background_color
            hover_text_color = self.invalid_hover_text_color
            border_color = self.invalid_border_color
            tooltip_text = self.invalid_tooltip_text

        self.setStyleSheet('''
                           
            QPushButton {
                font-size: 14px;
                font-weight: bold;
                color: %s;
                background-color: %s;
                border-radius: 5px;
                padding: %spx;
                border: 1px solid %s;
                margin-top: %spx;
                margin-bottom: %spx;
                margin-left: %spx;
                margin-right: %spx;
            }
                           
            QPushButton:hover {
                background-color: %s;
                color: %s;
            }

            QPushButton:pressed {
                background-color: #000000;
                color: #FFFFFF;
            }
        ''' % (text_color, background_color, self.padding, border_color, 
               self.margins[0], self.margins[2], self.margins[3], self.margins[1], 
               hover_background_color, hover_text_color))



        if tooltip_text is not None:
            self.setToolTip(tooltip_text)

        if valid_state:
            try :
                self.clicked.disconnect()
            except:
                pass
            self.clicked.connect(self.func_)
        else:
            try :
                self.clicked.disconnect()
            except:
                pass
            self.clicked.connect(None)