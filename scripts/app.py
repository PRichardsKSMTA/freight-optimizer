'''
Author: Daniel Kinn
Date: 2023-10-15

This it the "main" file for the application. This file is responsible for initializing the application.

'''


from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThreadPool

import gui.configuration as configuration
import gui.data_configuration.data_filter as data_filter
import gui.window_main as window_main
import os
import sys
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
sys.argv += ['--style', 'fusion']

if __name__ == '__main__':

    nullfile = open(os.devnull, 'w')
    nullfile = open('test.txt', 'w')
    sys.stdout = nullfile
    sys.stderr = nullfile
    app = QApplication(sys.argv)
    # default_param_filename = os.path.join('./scripts/gui/default_params.json')
    default_param_filename = os.path.join('.', 'scripts', 'gui', 'default_params.json')
    gui_configuration_filename = './configurations/gui_configurations.json'
    app_threadpool = QThreadPool()
    app_threadpool.setMaxThreadCount(4)
    model_configs = configuration.ModelConfiguration(default_param_filename, gui_configuration_filename, app_threadpool=app_threadpool)


    data_filter = data_filter.DataFilter(model_configs.get_setting('database_configurations'), model_configs)
    window = window_main.MainWindow(model_configs, data_filter=data_filter, parent=app)
    window.show()
    app.exec()