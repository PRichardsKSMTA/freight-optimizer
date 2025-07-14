from PySide6.QtWidgets import QWidget, QLineEdit

from .styled_label import StyledLabel
from .info_tooltip import InfoTooltip
from .styled_hbox_layout import StyledHBoxLayout

class StyledLineEdit(QWidget):
    """This is a simple line edit widget that is styled consistently with the rest of the application.
    """    

    def __init__(self, configs, parent, label, on_change=None, default_entry: str=None, tooltip_text: str=None):
        """Initializes this class

        Args:
            configs (Configuration): a Configuration object for this application.
            parent (QWidget): the parent widget for this widget.
            label (str): The text label for this widget
            on_change (func, optional): Function to call when line edit changes. Defaults to None.
            default_entry (str, optional): The default entry for the line edit. Defaults to None.
            tooltip_text (str, optional): The text to display in the tooltip. Defaults to None.
        """        
        super(StyledLineEdit, self).__init__()
        self.setStyleSheet('''
            QLineEdit {
                font-size: %spx;
                color: %s;
                background-color: %s;
                border: 1px solid %s;
                border-radius: 5px;
                padding: 5px;
                padding-top: 2px;
                padding-bottom: 2px;
            }
        ''' % (
            configs.get_application_setting('entry', 'font_size'),
            configs.get_application_setting('entry', 'text_color'),
            configs.get_application_setting('entry', 'background_color'),
            configs.get_application_setting('entry', 'border_color')))

        self.configs = configs
        self.parent = parent

        self.layout = StyledHBoxLayout(margins=(1,1,1,1))
        self.label = StyledLabel(text=label, app_configs=configs)
        self.layout.addWidget(self.label)

        self.entry = QLineEdit()
        if default_entry is not None:
            self.entry.setText(str(default_entry))
        if on_change is not None:
            self.entry.textChanged.connect(on_change)
        self.layout.addWidget(self.entry)

        if not tooltip_text is None:
            self.tooltip = InfoTooltip(configs, tooltip_text=tooltip_text)
            self.layout.addWidget(self.tooltip)

        self.setLayout(self.layout)


    def get_entry(self) -> str:
        """returns the text in the line edit

        Returns:
            str: the text in the line edit.
        """        
        return self.entry.text()