"""
This file is used to run an optimization item from the queue. The intention is for this file
to be called by the Task Manager on a regular basis to run any items in the queue. Once an
item is pulled from the queue, the start time is updated in the database, the optimization
is run, and the end time is updated in the database. The item is then removed from the queue.
"""

import json
import requests


import database.database_functions as dbf
from gui.configuration import ModelConfiguration
from gui.data_configuration.data_filter import DataFilter
from manager import run_from_configuration


if __name__ == '__main__':

    default_param_filename = 'scripts/gui/default_params.json'
    gui_configuration_filename = 'configurations/gui_configurations.json'

    model_configs = ModelConfiguration(default_param_filename, gui_configuration_filename)
    db_configs = model_configs.get_setting('database_configurations')
    con = dbf.get_connection(db_configs)

    queue_item = dbf.get_next_queue_item(con)
    if len(queue_item) == 0:
        con.close()
        print ('No items in queue')
        exit()
    queue_id = queue_item['QUEUE_ID']
    client_id = queue_item['CLIENT_ID']
    scenario_id = queue_item['SCENARIO_ID']
    run_id = queue_item['RUN_ID']
    scac = queue_item['SCAC']
    # payload = queue_item['PAYLOAD']

    dbf.update_queue_item(con, queue_id, start=True)

    run_error = None
    try:
        scenario = dbf.get_scenario(con, scenario_id, client_id)
        data_filter = DataFilter(
            model_configs.get_setting('database_configurations'),
            model_configs,
            client_id=client_id
        )
        data_filter.load_configuration(scenario_id, scenario=scenario)

        model_type = 'tsp'
        if not scenario['UseTSP']:
            model_type = 'two_tour_limit'

        run_from_configuration(
            **{
            'client_id': data_filter.client_id,
            'scenario_id': data_filter.scenario_id,
            'data_filters': data_filter.get_all_filters(),
            'database_configs': model_configs.get_setting('database_configurations'),
            'model_type': model_type,
            'run_id': run_id
            }
        )
    except Exception as exc:
        run_error = exc
        print(f"Failed to run scenario for queue item {queue_id}: {exc}")
    finally:
        update_error = None
        try:
            dbf.update_queue_item(con, queue_id, start=False)
        except Exception as update_exc:
            update_error = update_exc
            print(f"Failed to update queue item {queue_id} after run: {update_exc}")

        close_error = None
        try:
            con.close()
        except Exception as close_exc:
            close_error = close_exc
            print(f"Failed to close connection for queue item {queue_id}: {close_exc}")

        if run_error is not None:
            raise run_error
        if update_error is not None:
            raise update_error
        if close_error is not None:
            raise close_error
