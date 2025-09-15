'''
Author: Daniel Kinn
Date: 2023-10-15

This it the "main" file for the application. This file is responsible for initializing the application.

'''


import argparse
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThreadPool

import gui.configuration as configuration
import gui.data_configuration.data_filter as data_filter
import gui.window_main as window_main
import os
import sys
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        "--redirect-logs",
        action="store_true",
        help="Redirect stdout and stderr to a file (default: disabled).",
    )
    parser.add_argument(
        "--log-file",
        default="test.txt",
        help="Path to write redirected logs when --redirect-logs is supplied.",
    )
    args, qt_args = parser.parse_known_args()

    sys.argv[:] = [sys.argv[0]] + qt_args + ["--style", "fusion"]

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    log_file_handle = None

    try:
        if args.redirect_logs:
            log_file_handle = open(args.log_file, "w")
            sys.stdout = log_file_handle
            sys.stderr = log_file_handle

        app = QApplication(sys.argv)
        # default_param_filename = os.path.join('./scripts/gui/default_params.json')
        default_param_filename = os.path.join('.', 'scripts', 'gui', 'default_params.json')
        gui_configuration_filename = './configurations/gui_configurations.json'
        app_threadpool = QThreadPool()
        app_threadpool.setMaxThreadCount(4)
        model_configs = configuration.ModelConfiguration(
            default_param_filename,
            gui_configuration_filename,
            app_threadpool=app_threadpool,
        )

        data_filter_instance = data_filter.DataFilter(
            model_configs.get_setting('database_configurations'),
            model_configs,
        )
        window = window_main.MainWindow(
            model_configs,
            data_filter=data_filter_instance,
            parent=app,
        )
        window.show()
        app.exec()
    finally:
        if log_file_handle:
            log_file_handle.close()
            sys.stdout = original_stdout
            sys.stderr = original_stderr


if __name__ == '__main__':
    main()
