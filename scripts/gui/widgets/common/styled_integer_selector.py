from PySide6.QtWidgets import QSpinBox, QAbstractSpinBox, QWidget, QDoubleSpinBox

from .styled_label import StyledLabel
from .info_tooltip import InfoTooltip
from .styled_hbox_layout import StyledHBoxLayout

class StyledIntegerSelector(QWidget):
    '''
    This class creates a consistently styled integer selector for the application. An integer selector is a
    entry field for entering integer values (or doubles, if desired).
    '''

    def __init__(self,
                 label_text: str,
                 min_value: float,
                 max_value: float,
                 update_func,
                 configs,
                 step_value: float=1,
                 default_value: float=None,
                 tooltip_text: str=None,
                 double: bool=False,
                 parent: QWidget=None,
                 decimals: int=2):
        '''
        label_text: label for the selector
        min_value: minimum value for the selector
        max_value: maximum value for the selector
        update_func: function to call when the value is changed
        step_value: step value for the selector
        default_value: default value for the selector
        tooltip_text: text to display when the user hovers over the selector
        double: whether the selector should be a double selector or not
        '''
        super(StyledIntegerSelector, self).__init__(parent=parent)
        self.setStyleSheet('''
            QSpinBox, QDoubleSpinBox {
                font-size: %spx;
                color: %s;
                background-color: %s;
                border-radius: 5px;
                border: 1px solid %s;
                padding-top: 2px;
                padding-bottom: 2px;
                padding-left: 5px;
                padding-right: 5px;     
            }

        ''' % (
            configs.get_application_setting('entry', 'font_size'),
            configs.get_application_setting('entry', 'text_color'),
            configs.get_application_setting('entry', 'background_color'),
            configs.get_application_setting('entry', 'border_color'),
        ))

        self.hbox_layout = StyledHBoxLayout(margins=(1,1,1,1))

        self.label = StyledLabel(text=label_text, app_configs=configs)
        self.hbox_layout.addWidget(self.label)

        if double:
            self.spinbox = QDoubleSpinBox()
            self.spinbox.setDecimals(decimals)
        else:
            self.spinbox = QSpinBox()
        if max_value is None:
            max_value = 1000000000
        self.spinbox.setRange(min_value-step_value, max_value)
        self.spinbox.setSingleStep(step_value)
        self.spinbox.setGroupSeparatorShown(True)

        self.spinbox.setValue(min_value - step_value)
        if default_value is not None:
            try:
                if double:
                    self.spinbox.setValue(float(default_value))
                else:
                    self.spinbox.setValue(int(default_value))
            except:
                pass
            
        self.spinbox.setSpecialValueText('None')

        self.spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.update_func = update_func
        self.spinbox.valueChanged.connect(self.update_func)
        self.hbox_layout.addWidget(self.spinbox)

        if tooltip_text is not None:
            self.tooltip = InfoTooltip(configs=configs, tooltip_text=tooltip_text)
            self.hbox_layout.addWidget(self.tooltip)

        self.setLayout(self.hbox_layout)

        self.valueChanged = self.spinbox.valueChanged   