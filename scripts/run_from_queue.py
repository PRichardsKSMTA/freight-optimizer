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
    client_id = queue_item['CLIENT_ID']
    scenario_id = queue_item['SCENARIO_ID']
    run_id = queue_item['RUN_ID']
    scac = queue_item['SCAC']
    payload = queue_item['PAYLOAD']

    dbf.update_queue_item(con, run_id, start=True)

    scenario = dbf.get_scenario(con, scenario_id, client_id)
    data_filter = DataFilter(model_configs.get_setting('database_configurations'), model_configs,
                                         client_id=client_id)
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
    dbf.update_queue_item(con, run_id, start=False)

    URL = "https://prod-59.eastus.logic.azure.com:443/workflows/b01dbc3814624f63a70ddb4e9dac90ce/triggers/manual/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=xP08IGwZ2r0XNJuMK7_kWz0ez5Hk25hcN5Doi9A44FI"
    json_arg = json.loads(payload)
    rr = requests.post(URL, json=json_arg)
    rr.status_code