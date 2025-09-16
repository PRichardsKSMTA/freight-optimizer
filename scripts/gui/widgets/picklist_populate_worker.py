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
import typing

from .common.styled_combobox import StyledComboBox
from gui.data_configuration.data_filter import DataFilter
if typing.TYPE_CHECKING:
    from .widget_functions import FieldConfigs

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


class PicklistPopulateWorker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''
    def __init__(self, combo_box: StyledComboBox, data_filter: DataFilter,
                 field_configs: 'FieldConfigs'):
        super(PicklistPopulateWorker, self).__init__()

        self.combo_box = combo_box
        self.data_filter = data_filter
        self.field_configs = field_configs
        self.signals = WorkerSignals()
        # self.kwargs['progress_callback'] = self.signals.progress

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        try:
            picklist_df, picklist_err, picklist_err_message = self.data_filter.get_picklist(self.field_configs.data_field)
            display_field = self.field_configs.display_field
            value_field = self.field_configs.value_field
            count_field = self.field_configs.count_field
            if picklist_df.shape[0] == 0:
                dropdown_choices = []
                dropdown_values = []
                count_values = None
            else:
                picklist_df = picklist_df.sort_values(display_field)
                dropdown_choices = picklist_df[display_field].tolist()
                dropdown_values = picklist_df[value_field].tolist()
                if not count_field is None:
                    try:
                        count_values = [
                            (str(x) if x is not None else '') + ' (' + str(y) + ')'
                            for (x, y) in zip(dropdown_choices, picklist_df[count_field])
                        ]
                    except KeyError:
                        print ('Error: column ' + count_field + ' not found in picklist dataframe for field ' + self.field_configs.data_field)
                        count_values = None
                else:
                    count_values = None
            try:
                initial_selection_values = self.data_filter.get_filter(self.field_configs.data_field)
                if type(initial_selection_values) is not list:
                    initial_selection_values = [initial_selection_values]
                
                initial_selection_idcs = [dropdown_values.index(x) for x in initial_selection_values if x in dropdown_values]
                self.combo_box.set_dropdown_choices(dropdown_choices, dropdown_values, initial_selection=initial_selection_idcs, count_values=count_values)
                
            except Exception as e:
                print (traceback.format_exc())
                print ('error: ', e)
                pass
        except:
            exctype, value = sys.exc_info()[:2]
            print (exctype, value)
            try:
                self.combo_box.set_dropdown_choices(['Error populating field'], [None])
            except:
                pass

        self.signals.finished.emit()  # Done