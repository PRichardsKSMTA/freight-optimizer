'''
Author: Daniel Kinn
Date: 2023-10-04

This file contains the main window component for the optimization GUI.

'''
import pandas as pd
from PySide6.QtWidgets import QMainWindow, QGridLayout, QWidget, QSizePolicy


import datetime
import uuid
import manager
from .header.header import Header
from .configuration_panel.configuration_panel import ConfigurationPanel
from .output_panel.output_panel import OutputPanel
from .runnables import optimization_runnable as optimization_runnable
from .widgets.common.styled_scroll_area import StyledScrollArea
from .runnables.load_default_config_runnable import LoadDefaultConfigRunnable

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self, model_configs, data_filter, parent: QWidget=None):
        super().__init__()
        self.parent = parent
        self.model_configs = model_configs
        self.data_filter = data_filter
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
        self.layout.addWidget(ConfigurationPanel(model_configs=self.model_configs, data_filter=self.data_filter, start_func=self.start), 1, 0, 4, 4)
        
        self.output_panel = OutputPanel(self.model_configs)
        self.layout.addWidget(self.output_panel, 6, 0, 2, 4)
        
        load_config_runnable = LoadDefaultConfigRunnable(data_filter=self.data_filter, 
                                                         model_configs=self.model_configs, 
                                                         database_configs=self.model_configs.get_setting('database_configurations'))
        self.model_configs.app_threadpool.start(load_config_runnable)


    def reset(self, configuration_name: str=None):
        self.model_configs.initialize(configuration_name=configuration_name)
        self.initialize()

    def progress_fn(self, progress_object):
        id_ = progress_object[0]
        status = progress_object[1]
        if status == 'num_trips':
            num_trips = progress_object[2]
            self.output_panel.update_fields(id_, ['Number of Trips'], [num_trips])
        elif status == 'log':
            self.output_panel.update_fields(id_, ['Last Log Message'], [progress_object[2]])
        elif status == 'completed':
            end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.output_panel.update_fields(id_, ['End Time', 'Status'], [end_time, 'completed'])
        elif status == 'profit':
            profit = progress_object[2]
            self.output_panel.update_fields(id_, ['Gross Profit'], [profit])
        elif status == 'run_id':
            run_id = progress_object[2]
            self.output_panel.update_fields(id_, ['Run ID'], [run_id])
        else:
            self.output_panel.update_status(id_, status)


    def print_output(self, s):
        print(s)

    def thread_complete(self):
        print("THREAD COMPLETE!")

    def print_error(self, id_, exception_type, exception_value, traceback):
        print('error: ', exception_type, exception_value, traceback)
        end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.output_panel.update_fields(id_, ['End Time', 'Status'], [end_time, 'error'])


    def start(self):
        data_filters = self.data_filter.get_all_filters()
        use_tsp = data_filters['UseTSP']
        if use_tsp:
            self.start_model_run('tsp', data_filters)
        use_two_tour_limit = data_filters['UseTwoTripLimit']
        if use_two_tour_limit:
            self.start_model_run('two_tour_limit', data_filters)


    def start_model_run(self, model_type: str, data_filters: dict) -> None:
        """This function starts a model run by creating a worker and starting it in a threadpool.

        Args:
            model_type (str): The type of model to run; should be one of 'tsp' or 'two_tour_limit'
            data_filters (dict): The data filters to use for the model run

        Raises:
            ValueError: If model_type is not one of 'tsp' or 'two_tour_limit'
            ValueError: If client_id is not set
            ValueError: If scenario_id is not set
        """        
        if model_type not in ['tsp', 'two_tour_limit']:
            raise ValueError('model_type must be one of "tsp" or "two_tour_limit"')
        client_id = self.data_filter.client_id
        if pd.isnull(client_id):
            raise ValueError('Client ID is required to run optimization')
        scenario_id = self.data_filter.scenario_id
        if pd.isnull(scenario_id):
            raise ValueError('Scenario ID is required to run optimization')
        id_ = str(uuid.uuid4())
        self.output_panel.add_runnable(id_, model_type=model_type, client_name=self.data_filter.get_client_name())
        worker = optimization_runnable.Worker(
            id_=id_,
            fn=manager.run_from_config_with_error_handling,
            **{
                'client_id': self.data_filter.client_id,
                'scenario_id': self.data_filter.scenario_id,
                'data_filters': data_filters,
                'database_configs': self.model_configs.get_setting('database_configurations'),
                'progress_callback': self.progress_fn,
                'model_type': model_type,
            }
        ) 
        worker.signals.error.connect(self.print_error)
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        self.workers[id_] = worker
        self.model_configs.app_threadpool.start(worker)