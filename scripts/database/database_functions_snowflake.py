
import keyring
import numpy
import pandas
import json

import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas


REQUIRED_FIELDS = [
    'WeeksBack',
    'DataDelay',
    'CompanyOperations',
    'LaneAggregateField',
    'LaneGeographyLevel',
    'Geography',
    'BillTo',
    'OrderDivision',
    'PowerDivision',
    'DriverType',
    'MaxDeadhead',
    'MarginTarget',
    'MileageRate',
    'UseTSP',
    'UseTwoTripLimit',
    'MaxCapacity',
    'SoftDelete',
    'RUN_ID',
    'SCENARIO_NAME',
    'SCENARIO_NOTE'
]

DEFAULT_VALUES = {
    'WeeksBack': 12,
    'DataDelay': 2,
    'CompanyOperations': [],
    'LaneAggregateField': None,
    'LaneGeographyLevel': None,
    'Geography': [],
    'BillTo': [],
    'OrderDivision': [],
    'PowerDivision': [],
    'DriverType': [],
    'MaxDeadhead': None,
    'MarginTarget': 0.2,
    'MileageRate': 1.0,
    'UseTSP': False,
    'UseTwoTripLimit': True,
    'MaxCapacity': None,
    'SoftDelete': False,
    'RUN_ID': None,
    'SCENARIO_NAME': '',
    'SCENARIO_NOTE': ''
}

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.integer):
            return int(obj)
        if isinstance(obj, numpy.floating):
            return float(obj)
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


class QueryException(Exception):
    """This exception is raised when there is an issue with the database query"""
    
    def __init__(self, message):
        """This function initializes the QueryException class"""
        super().__init__(message)


def get_connection(database_configs: dict) -> snowflake.connector.connection.SnowflakeConnection:
    """gets the connection to the database.

    Args:
        database_configs (dict): the database configs, which
            should include 'username', 'account', 'schema',
            'keyring_username', and 'database' values

    Returns:
        snowflake.connector.connection.SnowflakeConnection: the connection to the database
    """    
    username = database_configs['username']
    password = keyring.get_password(database_configs['credential_account'], username)
    account = database_configs['account']
    schema = database_configs['schema']
    database = database_configs['database']
    try:
        con = snowflake.connector.connect(
            user = username,
            password = password,
            account = account,
            database = database,
            schema = schema
        )
    except Exception as e:
        raise (e)
    return con


def get_client_df(con: snowflake.connector.connection.SnowflakeConnection) -> pandas.DataFrame:
    """gets the client list from the database

    Args:
        con (snowflake.connector.connection.SnowflakeConnection): the connection to the database

    Returns:
        pandas.DataFrame: the client list as a pandas.DataFrame, as returned by the 
            GET_OPTIMIZER_CLIENTLIST() stored procedure
    """    
    proc = 'GET_OPTIMIZER_CLIENTLIST()'
    cs = con.cursor()
    cs.execute("call " + proc)
    data = cs.fetchall() 
    columns = [x[0] for x in cs.description]

    client_df = pandas.DataFrame(data, columns=columns)
    client_df = client_df.sort_values(by=['CLIENT_NAME'])
    return client_df


def get_picklist(con: snowflake.connector.connection.SnowflakeConnection, 
                 scenario_id: str,
                 client_id: str,
                 param_dict: dict,
                 data_field: str) -> pandas.DataFrame:
    """This function returns a picklist from the database for the input
    data_field

    Args:
        con (snowflake.connector.connection.SnowflakeConnection): the connection to the database
        
        start_week (int): the start week of the picklist
        client_id (str): the client id to filter on

    Returns:
        pandas.DataFrame: the picklist

    """
    if pandas.isnull(scenario_id): #scenario_id isn't used in this query so default to -1
        scenario_id = -1
    if 'WeeksBack' not in param_dict.keys():
        raise ValueError('WeeksBack is a required field')
    if 'DataDelay' not in param_dict.keys():
        raise ValueError('DataDelay is a required field')
    proc = "GET_OPTIMIZER_DATA(CLIENT_ID => {}, SCENARIO_ID => {}, DATASET_NAME => '{}', PARAM_JSON => '{}')".format(
        client_id, 
        int(scenario_id),
        data_field,
        json.dumps(param_dict, cls=NpEncoder))
    
    cs = con.cursor()
    try:
        cs.execute("call " + proc)
        data = cs.fetchall() 
        columns = [x[0] for x in cs.description]
    except Exception as e:
        print ("Exception is ", e)
        print ("Query is ", proc)
        raise QueryException('''Unable to complete query.\n\n''')

    picklist_df = pandas.DataFrame(data, columns=columns)

    return picklist_df


def add_new_scenario(
    con: snowflake.connector.connection.SnowflakeConnection,
    client_id: str,
    json_str: str,
    scenario_name: str,
    scenario_note: str,
    ) -> int:
    '''
    This function adds a new scenario based off what is currently
    in the name and note field
    '''
    json_str['SCENARIO_NAME'] = scenario_name
    json_str['SCENARIO_NOTE'] = scenario_note

    proc = "CALL PUT_OPTIMIZER_SCENARIO(CLIENT_ID => {}, JSON_STRING => '{}')".format(
        int(client_id),
        json.dumps(json_str, cls=NpEncoder)
    )

    cs = con.cursor()
    cs.execute(proc)
    scenario_id = cs.fetchall() 
    if len(scenario_id) > 0:
        scenario_id = scenario_id[0][0]
    else:
        raise ValueError('Scenario ID already exists')

    return int(scenario_id)


def update_scenario(
    con: snowflake.connector.connection.SnowflakeConnection,
    scenario_id: int,
    client_id: int,
    json_str: str,
    scenario_name: str,
    scenario_note: str
    ) -> None:
    '''
    This function updates a scenario based on the new inputs.
    '''
    json_str['SCENARIO_NAME'] = scenario_name
    json_str['SCENARIO_NOTE'] = scenario_note

    proc = "CALL PUT_OPTIMIZER_SCENARIO(SCENARIO_ID => {}, JSON_STRING => '{}', CLIENT_ID => {})".format(
        int(scenario_id),
        json.dumps(json_str, cls=NpEncoder),
        int(client_id)
    )
    cs = con.cursor()
    cs.execute(proc)


def get_scenario(con: snowflake.connector.connection.SnowflakeConnection,
    scenario_id: int,
    client_id: int) -> pandas.DataFrame:
    '''
    This function gets the scenario from the database
    '''
    proc = "CALL GET_OPTIMIZER_SCENARIO(CLIENT_ID => {}, SCENARIO_ID => {})".format(int(client_id), int(scenario_id))
    cs = con.cursor()
    cs.execute(proc)
    data = cs.fetchall() 

    return json.loads(data[0][0])


def soft_delete_scenario(con: snowflake.connector.connection.SnowflakeConnection,
    scenario_id: int,
    client_id: int,
    param_dict: str) -> None:
    '''
    This function soft deletes a scenario

    Args:
        con (snowflake.connector.connection.SnowflakeConnection): the connection to the database
        scenario_id (int): the scenario id to soft delete
        client_id (int): the client id to soft delete
    '''
    # proc = "CALL DELETE_OPTIMIZER_SCENARIO({}, {})".format(int(client_id), int(scenario_id))
    param_dict['SoftDelete'] = True
    proc = "CALL PUT_OPTIMIZER_SCENARIO (CLIENT_ID => {}, SCENARIO_ID => {}, JSON_STRING => '{}')".format(\
        int(client_id), int(scenario_id), json.dumps(param_dict, cls=NpEncoder))
    cs = con.cursor()
    cs.execute(proc)
    

def get_empty_miles(con: snowflake.connector.connection.SnowflakeConnection,
                    client_id: int,
                    scenario_id: int,
                    data_filters: dict,
                    run_id: str) -> pandas.DataFrame:
    '''
    This function gets the empty miles from the database
    '''
    if pandas.isnull(client_id):
        raise QueryException('Function get_empty_miles requires a non-null entry for client_id')
    if pandas.isnull(run_id):
        raise QueryException('Function get_empty_miles requires a non-null entry for run_id')
    data_filters['RUN_ID'] = str(run_id)
    proc = "CALL GET_OPTIMIZER_DATA(CLIENT_ID => {}, SCENARIO_ID => {}, ".format(int(client_id), scenario_id) + \
            "DATASET_NAME => 'EmptyMiles', PARAM_JSON => '{}')".format(json.dumps(data_filters, cls=NpEncoder))

    cs = con.cursor()
    cs.execute(proc)
    data = cs.fetchall() 
    columns = [x[0] for x in cs.description]

    empty_miles_df = pandas.DataFrame(data, columns=columns)
    return empty_miles_df


def get_saved_scenarios(con: snowflake.connector.connection.SnowflakeConnection, client_id: int) -> pandas.DataFrame:
    '''
    This function gets the saved scenarios from the database. The saved scenario response
    will include all non-deleted scenarios for the client_id and the json_str
    associated with each scenario.

    Args:
        con (snowflake.connector.connection.SnowflakeConnection): the connection to the database
        client_id (int): the client id to filter on

    Returns:
        pandas.DataFrame: the saved scenarios
    '''
    proc = "CALL GET_OPTIMIZER_SCENARIOS(CLIENT_ID  => {})".format(int(client_id))
    cs = con.cursor()
    cs.execute(proc)
    data = cs.fetchall()
    data_cols = cs.description
    df_rows = []

    for i in range(len(data)):
        df_rows.append({'SCENARIO_ID': data[i][0]})
        try:
            json_str = json.loads(data[i][4])
            df_rows[i].update(json_str)
        except:
            pass

    saved_scenarios_df = pandas.DataFrame(df_rows)
    if 'SCENARIO_NAME' not in saved_scenarios_df.columns.values:
        saved_scenarios_df['SCENARIO_NAME'] = ''
    if 'SCENARIO_NOTE' not in saved_scenarios_df.columns.values:
        saved_scenarios_df['SCENARIO_NOTE'] = ''
    
    col_order = ["SCENARIO_ID", 'SCENARIO_NAME', 'SCENARIO_NOTE']
    if 'SCENARIO_ID' not in saved_scenarios_df.columns.values:
        saved_scenarios_df['SCENARIO_ID'] = ''
    if 'SCENARIO_NAME' not in saved_scenarios_df.columns.values:
        saved_scenarios_df['SCENARIO_NAME'] = ''
    if 'SCENARIO_NOTE' not in saved_scenarios_df.columns.values:
        saved_scenarios_df['SCENARIO_NOTE'] = ''

    data_columns = [x.name for x in data_cols]
    if 'IS_PREFERRED' in data_columns:
        idx = data_columns.index('IS_PREFERRED')
        saved_scenarios_df['IS_PREFERRED'] = [x[idx] for x in data]
        col_order.append('IS_PREFERRED')
    if 'LAST_RUN_DTTM' in data_columns:
        idx = data_columns.index('LAST_RUN_DTTM')
        saved_scenarios_df['LAST_RUN_DTTM'] = [x[idx] for x in data]
        try:
            saved_scenarios_df['LAST_RUN_DTTM'] = saved_scenarios_df['LAST_RUN_DTTM'].dt.strftime('%Y-%m-%d %H:%M')
        except AttributeError:
            saved_scenarios_df['LAST_RUN_DTTM'] = ''
        col_order.append('LAST_RUN_DTTM')
    if 'LAST_MESSAGE_TYPE' in data_columns:
        idx = data_columns.index('LAST_MESSAGE_TYPE')
        saved_scenarios_df['LAST_MESSAGE_TYPE'] = [x[idx] for x in data]
        col_order.append('LAST_MESSAGE_TYPE')
    if 'LAST_MESSAGE' in data_columns:
        idx = data_columns.index('LAST_MESSAGE')
        saved_scenarios_df['LAST_MESSAGE'] = [x[idx] for x in data]
        col_order.append('LAST_MESSAGE')
    col_order.extend([x for x in saved_scenarios_df.columns.values if x not in col_order])
    saved_scenarios_df = saved_scenarios_df[col_order]

    col_order.extend([x for x in saved_scenarios_df.columns.values if x not in col_order])
    col_order = [x for x in col_order if x != 'SoftDelete']

    saved_scenarios_df = saved_scenarios_df[col_order]
    return saved_scenarios_df

  
def get_trip_data(con: snowflake.connector.connection.SnowflakeConnection,
                  client_id: int,
                  scenario_id: int,
                  weeks_back: int,
                  start_week: int,
                  run_id: str,
                  params: dict) -> pandas.DataFrame:
    '''
    This function gets the trip data from the database
    '''
    if pandas.isnull(client_id):
        raise QueryException('Require a non-null entry for client_id')
    if pandas.isnull(weeks_back):
        raise QueryException('Require a non-null entry for weeks_back')
    if pandas.isnull(start_week):
        raise QueryException('Require a non-null entry for start_week')
    if pandas.isnull(run_id):
        raise QueryException('Require a non-null entry for run_id')
    
    params['RUN_ID'] = str(run_id)
    params['WeeksBack'] = int(weeks_back)
    params['DataDelay'] = int(start_week)
    proc = "CALL GET_OPTIMIZER_DATA(CLIENT_ID => {}, SCENARIO_ID => {}, ".format(int(client_id), scenario_id) + \
            "DATASET_NAME => 'Dataset', PARAM_JSON => '{}')".format(json.dumps(params, cls=NpEncoder))


    cs = con.cursor()
    cs.execute(proc)
    data = cs.fetchall() 
    columns = [x[0] for x in cs.description]

    trip_data_df = pandas.DataFrame(data, columns=columns)
    return trip_data_df


def write_message_to_log(con: snowflake.connector.connection.SnowflakeConnection,
                         run_id: str,
                         message: str,
                         message_type:str) -> None:
    '''
    This function writes a message to the log

    Args:
        con (snowflake.connector.connection.SnowflakeConnection): the connection to the database
        run_id (str): the run_id
        message (str): the message to write to the log
        message_type (str): the message type
    '''
    proc = "CALL KSMTA_FREIGHTMATH.PUBLIC.PUT_OPTIMIZER_LOGGING(RUN_ID => '{}', MESSAGE_TYPE => '{}', MESSAGE => '{}')".format(
        run_id,
        message_type,
        message
    )
    cs = con.cursor()
    cs.execute(proc)


def write_output(con: snowflake.connector.connection.SnowflakeConnection,
                 run_id: str,
                 df: pandas.DataFrame) -> None:
    '''
    This function writes the output to the database

    Args:
        con (snowflake.connector.connection.SnowflakeConnection): the connection to the database
        run_id (str): the run_id
        df (pandas.DataFrame): the dataframe to write to the database
        table_name (str): the name of the table to write to
    '''
    df['RUN_ID'] = run_id
    #check that KEY, IS_ACCEPTED, TOUR_ID and TOUR_POSITION are in the dataframe
    if 'KEY' not in df.columns.values:
        raise ValueError('KEY column is required to write output to database')
    if 'IS_ACCEPTED' not in df.columns.values:
        raise ValueError('IS_ACCEPTED column is required to write output to database')
    if 'TOUR_ID' not in df.columns.values:
        raise ValueError('TOUR_ID column is required to write output to database')
    if 'TOUR_POSITION' not in df.columns.values:
        raise ValueError('TOUR_POSITION column is required to write output to database')

    cols = ['ORDER_ID', 'RUN_ID', 'KEY', 'IS_ACCEPTED', 'TOUR_ID', 'TOUR_POSITION', 'DEADHEAD_COST']
    df['IS_ACCEPTED'] = df['IS_ACCEPTED'].astype(bool)
    df['DEADHEAD_COST'] = df['DEADHEAD_COST'].astype(float).round(2)

    write_pandas(conn=con, df=df[cols], table_name='OPTIMIZER_RUN_RESULT')


def get_default_configurations(con):
    proc = 'Call GET_OPTIMIZER_DEFAULT_CONFIG()'
    cs = con.cursor()
    cs.execute(proc)
    data = cs.fetchall()
    columns = [x[0] for x in cs.description]
    df = pandas.DataFrame(data, columns=columns)

    try:
        max_deadhead = int(df.loc[df['CODE_LABEL'] == 'Maximum Deadhead', 'CODE_VALUE'].values[0])
    except:
        print ('Unable to get max deadhead from get_default_configurations()')
        max_deadhead = None
    try:
        max_capacity = int(df.loc[df['CODE_LABEL'] == 'Maximum Capacity', 'CODE_VALUE'].values[0])
    except:
        print ('Unable to get max capacity from get_default_configurations()')
        max_capacity = None
    try:
        lane_load_minimum = int(df.loc[df['CODE_LABEL'] == 'Lane Load Minimum', 'CODE_VALUE'].values[0])
    except:
        print ('Unable to get load lane minimum from get_default_configurations()')
        lane_load_minimum = None
    try:
        total_weeks = int(df.loc[df['CODE_LABEL'] == 'Total Weeks', 'CODE_VALUE'].values[0])
    except:
        print ('Unable to get total weeks from get_default_configurations()')
        total_weeks = None
    try:
        data_delay = int(df.loc[df['CODE_LABEL'] == 'Data Delay', 'CODE_VALUE'].values[0])
    except:
        print ('Unable to get data delay from get_default_configurations()')
        data_delay = None
    try:
        margin_target = float(df.loc[df['CODE_LABEL'] == 'Margin Target', 'CODE_VALUE'].values[0])
    except:
        print ('Unable to get margin threshold from get_default_configurations()')
        margin_target = None
    return {
        'max_deadhead': max_deadhead,
        'max_capacity': max_capacity,
        'lane_load_minimum': lane_load_minimum,
        'WeeksBack': total_weeks,
        'DataDelay': data_delay,
        'MarginTarget': margin_target
    }


def get_next_queue_item(con: snowflake.connector.connection.SnowflakeConnection) -> dict:
    '''
    This function checks the queue to see if the run_id is in the queue

    Args:
        con (snowflake.connector.connection.SnowflakeConnection): the connection to the database

    Returns:
        dict: the payload of the queue record, in the form of a dictionary that 
        looks like:
        {'CLIENT_ID': 16, 'SCENARIO_ID': 228, 'RUN_ID': '1d8fa3ea-7207-43c8-bc08-06cfaf811ba6', 'SCAC': 'MLXO', 'PAYLOAD': '{"SCAC": "MLXO", "WORKSPACE_GUID": "0c9092c3-9990-4fdc-82b4-c3f9babd9d62", "DATASET_GUID": "8026ee54-6748-4184-a79c-62290cf53875"}'}
    '''
    query = "SELECT * FROM v_optimizer_queue_record"
    cs = con.cursor()
    cs.execute(query)
    cs.get_results_from_sfqid(cs.sfqid)
    results = cs.fetchall()
    if len(results) == 0:
        return {}
    payload = {desc.name: val for desc, val in zip(cs.description, results[0])}
    return payload

def update_queue_item(con: snowflake.connector.connection.SnowflakeConnection, run_id: str, start=True) -> None:
    '''
    This function closes the queue item by removing it from the queue

    Args:
        con (snowflake.connector.connection.SnowflakeConnection): the connection to the database
        run_id (str): the run_id to remove from the queue
    '''
    run_dttm = pandas.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    if start:
        field = 'RUN_START_DTTM'
    else:
        field = 'RUN_END_DTTM'
    query = "UPDATE OPTIMIZER_SCHEDULE_QUEUE SET {} = '{}' WHERE RUN_ID = '{}'".format(field, run_dttm, run_id)
    cs = con.cursor()
    cs.execute(query)


if __name__ == '__main__':
    username = 'KSMTA_OPTIMIZER_USER'
    account = 'a8639454119861-ue85361'

    password = keyring.get_password("ksm", username)

    con = get_connection({
        'username': username,
        'password': password,
        'account': account,
        "credential_account": "ksm",
        'schema': 'PUBLIC',
        'database': 'KSMTA_FREIGHTMATH'
    })

    query = "SELECT * FROM OPTIMIZER_RUN_RESULT WHERE Run_Id = '5a84c98d7324460c9c7ec390550917eb'"
    cs = con.cursor()
    cs.execute(query)
    data = cs.fetchall()
    columns = [x[0] for x in cs.description]
    df = pandas.DataFrame(data, columns=columns)

    client_id = 1
    # json_str = {'max_deadhead': 1, 'margin_target': 0.25, 'WeeksBack': 4, 'start_week': 1, 'DataDelay': 5}
    client_id = 29
    scenario_id = -1
    dataset_name = 'OrderDivision'
    json_str = {"WeeksBack": 4, "DataDelay": 1, "MaxDeadhead": 500, "MarginTarget": 0.0, "MileageRate": 1.0, \
                "UseTSP": True, "UseTwoTripLimit": False, "MaxCapacity": 99999999, "lane_load_minimum": 1, 
                "CompanyOperations": [], "LaneAggregateField": None, "LaneGeographyLevel": None, "Geography": [],\
                      "BillTo": [], "OrderDivision": [], "PowerDivision": []}
    
    df = get_picklist(con, 1, 2, json_str, dataset_name)
