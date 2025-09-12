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


class LoadDefaultConfigRunnable(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, data_filter, model_configs, database_configs):
        super(LoadDefaultConfigRunnable, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.data_filter = data_filter
        self.model_configs = model_configs
        self.database_configs = database_configs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            con = database_functions.get_connection(self.database_configs)
            default_configs = database_functions.get_default_configurations(con)
            self.model_configs.update_max_capacity(default_configs['max_capacity'])
            self.model_configs.update_max_deadhead(default_configs['max_deadhead'])
            self.model_configs.update_margin_target(default_configs['MarginTarget'])
            self.data_filter.set_filter('WeeksBack', default_configs['WeeksBack'])
            self.data_filter.set_filter('DataDelay', default_configs['DataDelay'])
            self.data_filter.set_filter('lane_load_minimum', default_configs['lane_load_minimum'])

        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            print (exctype, value)
        finally:
            self.signals.finished.emit()