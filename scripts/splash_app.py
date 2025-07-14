'''
Author: Daniel Kinn
Date: 2023-10-15

This it the "main" file for the application. This file is responsible for initializing the application.

'''


from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QCoreApplication
import gui.configuration as configuration
from gui.splash_main import SplashMain
import os
import sys
import time
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
sys.argv += ['--style', 'fusion']

if __name__ == '__main__':

    app = QApplication(sys.argv)
    default_param_filename = 'scripts/gui/default_params.json'
    gui_configuration_filename = 'configurations/gui_configurations.json'

    model_configs = configuration.ModelConfiguration(default_param_filename, gui_configuration_filename)

    window = SplashMain(model_configs, parent=app)
    window.show()
    QTimer.singleShot(5 * 1000, QCoreApplication.quit) #exit splashscreen after 5 seconds
    app.exec()
