'''
Author: Daniel Kinn
Date: 2023-10-04

This file contains the functionality for running an optimization instance
in a distinct thread. 

Much of this code was taken from the following source:
https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/

'''

from PySide6.QtCore import QRunnable, Slot, Signal, QObject
import sys
import traceback
import uuid

from database import database_functions

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(tuple)


class ScenarioTableLoadWorker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, data_filter, client_id, database_configs, *args, **kwargs):
        super(ScenarioTableLoadWorker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.data_filter = data_filter
        self.database_configs = database_configs
        self.args = args
        self._id = uuid.uuid4()
        self.client_id = client_id
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            self.signals.progress.emit((self._id, 'queued'))
            self.data_filter.load_configuration_df = None
            self.data_filter.loading_config_table = True
            con = database_functions.get_connection(self.database_configs)
            load_configuration_df = database_functions.get_saved_scenarios(con, self.client_id)
            con.close()
            self.data_filter.load_configuration_df = load_configuration_df
            self.data_filter.loading_config_table = False
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((self._id, exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()