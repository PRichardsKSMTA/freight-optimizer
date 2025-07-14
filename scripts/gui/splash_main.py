'''
Author: Daniel Kinn
Date: 2023-10-04

This file contains the main window component for the optimization GUI.

'''

from PySide6.QtWidgets import QMainWindow, QGridLayout, QWidget, QSizePolicy

from .header.header import Header
from .runnables import optimization_runnable as optimization_runnable
from .widgets.common.styled_scroll_area import StyledScrollArea
from .widgets.colored_widget import ColoredWidget

# Subclass QMainWindow to customize your application's main window
class SplashMain(QMainWindow):
    def __init__(self, model_configs, parent: QWidget=None):
        super().__init__()
        self.parent = parent
        self.model_configs = model_configs
        self.workers = {} #track the workers so that we can collect output and output statuses

        screen_height = self.screen().size().height()
        self.setMinimumHeight(min(self.model_configs.get_application_setting('window', 'minimum_height'), screen_height))
        self.setMaximumHeight(max(self.model_configs.get_application_setting('window', 'maximum_height'), screen_height))
        self.setFixedWidth(self.model_configs.get_application_setting('window', 'width'))
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setWindowTitle(self.model_configs.get_application_setting('window', 'title'))

        self.resize(self.model_configs.get_application_setting('window', 'width'), 
                    min(screen_height, self.model_configs.get_application_setting('window', 'starting_height')))
        self.show()

        self.layout = QGridLayout()
        widget = QWidget()
        widget.setLayout(self.layout)
        scrollArea = StyledScrollArea()
        scrollArea.setWidget(widget)
        self.setCentralWidget(scrollArea)
        self.initialize()


    def initialize(self):
    
        self.layout.addWidget(Header(self.model_configs), 0, 0, 1, 4)
        self.layout.addWidget(FillPanel(model_configs=self.model_configs), 1, 0, 4, 4)


class FillPanel(ColoredWidget):
    """This panel is responsible for maintaining the form components that allow the user to modify configurations.
    The panel is a vertical box layout that contains the following widgets:
        - CustomerGroupBox
        - ConfigurationMetaData
        - model_selector_group.ModelSelectorGroup
        - configuration_entries_group.ConfigurationEntryGroup
        - configuration_date_groupbox.ConfigurationDateGroupbox
    """
    def __init__(self, model_configs):
        self.model_configs = model_configs
        panel_color = self.model_configs.get_application_setting('configuration_panel', 'background_color')
        super(FillPanel, self).__init__(panel_color)
