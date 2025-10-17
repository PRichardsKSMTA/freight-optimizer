
"""This file contains functions that interact with the database. The functions
in this file are used to get data from the database, write data to the database,
and update data in the database.
"""
import logging
import keyring
import numpy
import pandas
import json

import pyodbc
import sqlalchemy


logger = logging.getLogger(__name__)


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


def prepare_dict_for_sql(input_dict: dict) -> dict:
    """This function replaces any null values in the input dictionary
    with None. Additionally, this replaces any time stamp values
    with a string representation of the time stamp.

    Args:
        input_dict (dict): the input dictionary

    Returns:
        dict: the dictionary with any null values replaced with None
    """
    for key, value in input_dict.items():
        if type(value) is list:
            continue
        if pandas.isnull(value):
            input_dict[key] = None
        if isinstance(value, pandas.Timestamp):
            input_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        if type(value) is dict:
            input_dict[key] = prepare_dict_for_sql(value)
    return input_dict


def get_connection(database_configs: dict) -> pyodbc.Connection:
    """gets the connection to the database.

    Args:
        database_configs (dict): the database configs, which
            should include 'username',
            'keyring_username', and 'database' values

    Returns:
        pyodbc.Connection: the connection to the database
    """    
    username = database_configs['username']
    password = database_configs['password']

    database = database_configs['database']
    server = 'ksm-ksmta-sqlsrv-001.database.windows.net'
    username = keyring.get_password(database_configs['credential_account'], username)
    password = keyring.get_password(database_configs['credential_account'], password)

    missing_credentials = []
    if username is None:
        missing_credentials.append('username')
    if password is None:
        missing_credentials.append('password')

    if missing_credentials:
        missing_creds_str = ', '.join(missing_credentials)
        message = (
            "Missing database credential(s) for account "
            f"'{database_configs['credential_account']}': {missing_creds_str}"
        )
        logger.error(message)
        raise ValueError(message)
    cnxn = pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    return cnxn


def get_engine(database_configs: dict) -> pyodbc.Connection:
    """gets the connection to the database.

    Args:
        database_configs (dict): the database configs, which
            should include 'username',
            'keyring_username', and 'database' values

    Returns:
        pyodbc.Connection: the connection to the database
    """
    username = database_configs['username']
    password = database_configs['password']
    database = database_configs['database']
    server = 'ksm-ksmta-sqlsrv-001.database.windows.net'
    username = keyring.get_password(database_configs['credential_account'], username)
    password = keyring.get_password(database_configs['credential_account'], password)
    engine = sqlalchemy.create_engine(f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server')
    return engine


def get_client_df(con: pyodbc.Connection) -> pandas.DataFrame:
    """Gets the client list from the database
    COMPLETED

    Args:
        con (pyodbc.Connection): the connection to the database

    Returns:
        pandas.DataFrame: the client list as a pandas.DataFrame, as returned by the 
            GET_OPTIMIZER_CLIENTLIST() stored procedure
    """    
    proc = 'EXEC GET_OPTIMIZER_CLIENTLIST;'
    client_df = execute_proc_with_return(con, proc)
    client_df = client_df.sort_values(by=['CLIENT_NAME'])
    return client_df


def execute_proc_with_return(con: pyodbc.Connection, query: str) -> pandas.DataFrame:
    """This function executes a query and returns the results as a pandas.DataFrame.
    It is used for queries that return data. The input query should be a string
    that is a valid SQL procedure

    Args:
        con (pyodbc.Connection): the connection to the database
        query (str): the query to execute, beginning with 'EXEC'

    Returns:
        pandas.DataFrame: the results of the query
    """
    init_proc = 'SET NOCOUNT ON; DECLARE @rv int;'
    select_proc = 'SELECT @rv AS return_value;'
    full_proc = init_proc + query + select_proc
    cs = con.cursor()
    cs.execute(full_proc)
    data = cs.fetchall()
    cs.commit()
    columns = [x[0] for x in cs.description]
    return pandas.DataFrame([numpy.array(x) for x in data], columns=columns)


def get_picklist(con: pyodbc.Connection, 
                 scenario_id: str,
                 client_id: str,
                 param_dict: dict,
                 data_field: str) -> pandas.DataFrame:
    """This function returns a picklist from the database for the input
    data_field

    Args:
        con (pyodbc.Connection): the connection to the database
        scenario_id (int): the scenario id to filter on
        client_id (str): the client id to filter on
        data_field (str): the data field to filter on
        start_week (int): the start week of the picklist
        
    Returns:
        pandas.DataFrame: the picklist
    """
    if pandas.isnull(scenario_id): #scenario_id isn't used in this query so default to -1
        scenario_id = -1
    if 'WeeksBack' not in param_dict.keys():
        raise ValueError('WeeksBack is a required field')
    if 'DataDelay' not in param_dict.keys():
        raise ValueError('DataDelay is a required field')
    
    try:
        param_json = json.dumps(param_dict, cls=NpEncoder).replace("'", "'")
        query = f"EXEC GET_OPTIMIZER_DATA @CLIENT_ID = {client_id}, @SCENARIO_ID = {scenario_id}, @DATASET_NAME = {data_field}, @PARAM_JSON = '{param_json}'"
        picklist_df = execute_proc_with_return(con, query)
        return picklist_df
    except Exception as e:
        msg = f'Error in get_picklist: {e}'
        raise QueryException(msg)


def add_new_scenario(
    con: pyodbc.Connection,
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
    
    #replace any null values with None
    json_str = prepare_dict_for_sql(json_str)

    proc = "EXEC PUT_OPTIMIZER_SCENARIO @CLIENT_ID = {}, @SCENARIO_ID = NULL, @JSON_STRING = '{}'".format(
        int(client_id),
        json.dumps(json_str, cls=NpEncoder).replace("'", "'").replace("NaN", '""')
    )

    return_val = execute_proc_with_return(con, proc)
    if return_val.shape[0] == 0:
        raise ValueError('Scenario ID already exists')
    
    scenario_id = int(return_val['UPDATED_SCENARIO_ID'].values[0])
    return scenario_id


def update_scenario(
    con: pyodbc.Connection,
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
    json_str = prepare_dict_for_sql(json_str)

    proc = "EXEC PUT_OPTIMIZER_SCENARIO @SCENARIO_ID = {}, @JSON_STRING = '{}', @CLIENT_ID = {}".format(
        int(scenario_id),
        json.dumps(json_str, cls=NpEncoder).replace("'", "'"),
        int(client_id)
    )
    cs = con.cursor()
    cs.execute(proc)
    cs.commit()


def get_scenario(con: pyodbc.Connection,
    scenario_id: int,
    client_id: int) -> dict:
    '''
    This function gets the scenario from the database

    Args:
        con (pyodbc.Connection): the connection to the database
        scenario_id (int): the scenario id to filter on
        client_id (int): the client id to filter on
    '''
    proc = "EXEC GET_OPTIMIZER_SCENARIO @CLIENT_ID = {}, @SCENARIO_ID = {};".format(int(client_id), int(scenario_id))
    df = execute_proc_with_return(con, proc)

    if df.shape[0] == 0:
        raise ValueError(f'Scenario ID {scenario_id} does not exist for client ID {client_id}')

    return json.loads(df['PARAMETER_JSON'].values[0])


def soft_delete_scenario(con: pyodbc.Connection,
    scenario_id: int,
    client_id: int,
    param_dict: str) -> None:
    '''
    This function soft deletes a scenario

    Args:
        con (pyodbc.Connection): the connection to the database
        scenario_id (int): the scenario id to soft delete
        client_id (int): the client id to soft delete
    '''

    param_dict['SoftDelete'] = True
    param_dict = prepare_dict_for_sql(param_dict)
    proc = "EXEC PUT_OPTIMIZER_SCENARIO @CLIENT_ID = {}, @SCENARIO_ID = {}, @JSON_STRING = '{}'".format(\
        int(client_id), int(scenario_id), json.dumps(param_dict, cls=NpEncoder))

    cs = con.cursor()
    cs.execute(proc)
    cs.commit()
    

def get_empty_miles(con: pyodbc.Connection,
                    client_id: int,
                    scenario_id: int,
                    data_filters: dict,
                    weeks_back: int,
                    data_delay: int,
                    run_id: str) -> pandas.DataFrame:
    '''
    This function gets the empty miles from the database

    Args:
        con (pyodbc.Connection): the connection to the database
        client_id (int): the client id to filter on
        scenario_id (int): the scenario id to filter on
        data_filters (dict): the data filters to apply
        run_id (str): the run id to filter on

    Returns:
        pandas.DataFrame: the empty miles
    '''
    if pandas.isnull(client_id):
        raise QueryException('Function get_empty_miles requires a non-null entry for client_id')
    if pandas.isnull(run_id):
        raise QueryException('Function get_empty_miles requires a non-null entry for run_id')
    data_filters['RUN_ID'] = str(run_id)
    data_filters['WeeksBack'] = int(weeks_back)
    data_filters['DataDelay'] = int(data_delay)
    if 'PARAMETER_JSON' in data_filters.keys():
        del data_filters['PARAMETER_JSON']
    data_filters = prepare_dict_for_sql(data_filters)
    query = "EXEC GET_OPTIMIZER_DATA @CLIENT_ID = {}, @SCENARIO_ID = {}, ".format(int(client_id), scenario_id) + \
            "@DATASET_NAME = 'EmptyMiles', @PARAM_JSON = '{}'".format(json.dumps(data_filters, cls=NpEncoder).replace("'", "'"))
    empty_miles_df = execute_proc_with_return(con, query)

    return empty_miles_df


def get_saved_scenarios(con: pyodbc.Connection, client_id: int) -> pandas.DataFrame:
    '''
    This function gets the saved scenarios from the database. The saved scenario response
    will include all non-deleted scenarios for the client_id and the json_str
    associated with each scenario.

    Args:
        con (pyodbc.Connection): the connection to the database
        client_id (int): the client id to filter on

    Returns:
        pandas.DataFrame: the saved scenarios
    '''
    proc = "EXEC GET_OPTIMIZER_SCENARIOS @CLIENT_ID  = {}".format(int(client_id))
    saved_scenarios_df = execute_proc_with_return(con, proc)

    saved_scenarios_df['PARAMETER_JSON'] = saved_scenarios_df['PARAMETER_JSON'].apply(lambda x: x.replace("NULL", '""'))
    saved_scenarios_df['PARAMETER_JSON'] = saved_scenarios_df['PARAMETER_JSON'].apply(lambda x: x.replace("none", '""'))
    saved_scenarios_df['PARAMETER_JSON'] = saved_scenarios_df['PARAMETER_JSON'].apply(lambda x: x.replace("None", '""'))

    def load_json(x):
        try:
            return json.loads(x)
        except:
            return dict()
    saved_scenarios_df['PARAMETER_JSON'] = saved_scenarios_df['PARAMETER_JSON'].apply(lambda x: load_json(x))

    #get all unique keys from the json_str
    keys = set()
    for i in range(saved_scenarios_df.shape[0]):
        keys.update(saved_scenarios_df['PARAMETER_JSON'].iloc[i].keys())
    #add the keys to the dataframe
    if "PARAMETER_JSON" in keys:
        keys.remove("PARAMETER_JSON")
    for key in keys:
        try:
            saved_scenarios_df[key] = saved_scenarios_df['PARAMETER_JSON'].apply(lambda x: x.get(key, None))
        except:
            saved_scenarios_df[key] = None

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

    col_order.extend([x for x in saved_scenarios_df.columns.values if x not in col_order])
    saved_scenarios_df = saved_scenarios_df[col_order]

    col_order.extend([x for x in saved_scenarios_df.columns.values if x not in col_order])
    col_order = [x for x in col_order if x != 'SoftDelete']

    saved_scenarios_df = saved_scenarios_df[col_order]
    return saved_scenarios_df

  
def get_trip_data(con: pyodbc.Connection,
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
    if 'PARAMETER_JSON' in params.keys():
        del params['PARAMETER_JSON']
    params = prepare_dict_for_sql(params)
    proc = "EXEC GET_OPTIMIZER_DATA @CLIENT_ID = {}, @SCENARIO_ID = {}, ".format(int(client_id), scenario_id) + \
            "@DATASET_NAME = 'Dataset', @PARAM_JSON = '{}'".format((json.dumps(params, cls=NpEncoder).replace("'", "'")))
    trip_data_df = execute_proc_with_return(con, proc)
    trip_data_df['AGGTOTALREV'] = trip_data_df['AGGTOTALREV'].astype(float)
    trip_data_df['AGGLOADEDCOST'] = trip_data_df['AGGLOADEDCOST'].astype(float)
    trip_data_df['AGGLOADEDMILES'] = trip_data_df['AGGLOADEDMILES'].astype(float)
    trip_data_df['MUST_TAKE'] = trip_data_df['MUST_TAKE'].apply(lambda x: False if str(x).upper() == 'FALSE' else x)
    trip_data_df['MUST_TAKE'] = trip_data_df['MUST_TAKE'].astype(bool)
    return trip_data_df


def write_message_to_log(con: pyodbc.Connection,
                         run_id: str,
                         message: str,
                         message_type:str) -> None:
    '''
    This function writes a message to the log

    Args:
        con (pyodbc.Connection): the connection to the database
        run_id (str): the run_id
        message (str): the message to write to the log
        message_type (str): the message type
    '''
    proc = "EXEC PUT_OPTIMIZER_LOGGING @RUN_ID = '{}', @MESSAGE_TYPE = '{}', @MESSAGE = '{}'".format(
        run_id,
        message_type,
        message
    )
    cs = con.cursor()
    cs.execute(proc)
    cs.commit()


def write_output(engine: sqlalchemy.engine.base.Connection,
                 run_id: str,
                 df: pandas.DataFrame) -> None:
    '''
    This function writes the output to the database

    Args:
        engine (sqlalchemy.engine.base.Connection): the connection to the database
        run_id (str): the run_id
        df (pandas.DataFrame): the dataframe to write to the database
    '''
    df['RUN_ID'] = run_id
    #check that KEY, IS_ACCEPTED, TOUR_ID and TOUR_POSITION are in the dataframe
    if 'KEY_FIELD' not in df.columns.values:
        raise ValueError('KEY column is required to write output to database')
    if 'IS_ACCEPTED' not in df.columns.values:
        raise ValueError('IS_ACCEPTED column is required to write output to database')
    if 'TOUR_ID' not in df.columns.values:
        raise ValueError('TOUR_ID column is required to write output to database')
    if 'TOUR_POSITION' not in df.columns.values:
        raise ValueError('TOUR_POSITION column is required to write output to database')

    cols = ['ORDER_ID', 'RUN_ID', 'KEY_FIELD', 'IS_ACCEPTED', 'TOUR_ID', 'TOUR_POSITION', 'DEADHEAD_COST']
    df['IS_ACCEPTED'] = df['IS_ACCEPTED'].astype(bool)
    df['DEADHEAD_COST'] = df['DEADHEAD_COST'].astype(float).round(2)

    df = df[cols]
    df.to_sql('OPTIMIZER_RUN_RESULT', engine, if_exists='append', index=False)


def get_default_configurations(con: pyodbc.Connection) -> dict:
    """This function gets the default configurations from the database
    COMPLETED 
    Args:
        con (pyodbc.Connection): the connection to the database

    Returns:
        dict: the default configurations, in the form of a dictionary that looks like:
        {'max_deadhead': 500, 'max_capacity': 99999999, 'lane_load_minimum': 1, 'WeeksBack': 4, 'DataDelay': 1, 'MarginTarget': 0.0}
    """
    proc = 'EXEC GET_OPTIMIZER_DEFAULT_CONFIG;'
    df = execute_proc_with_return(con, proc)
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


def get_next_queue_item(con: pyodbc.Connection) -> dict:
    '''
    This function checks the queue to see if the run_id is in the queue

    Args:
        con (pyodbc.Connection): the connection to the database

    Returns:
        dict: the payload of the queue record, in the form of a dictionary that 
        looks like:
        {
            'QUEUE_ID': '1502',
            'CLIENT_ID': 16,
            'SCENARIO_ID': 228,
            'RUN_ID': '1d8fa3ea-7207-43c8-bc08-06cfaf811ba6',
            'SCAC': 'MLXO',
            'PAYLOAD': '{"SCAC": "MLXO", "WORKSPACE_GUID": "0c9092c3-9990-4fdc-82b4-c3f9babd9d62", "DATASET_GUID": "8026ee54-6748-4184-a79c-62290cf53875"}'
        }
    '''
    query = "SELECT * FROM v_optimizer_queue_record"
    df = pandas.read_sql(query, con)
    if df.shape[0] == 0:
        return {}
    payload = {col: df[col].values[0] for col in df.columns}
    return payload


def update_queue_item(con: pyodbc.Connection, queue_id: str, start=True) -> None:
    '''
    This function closes the queue item by removing it from the queue

    Args:
        con (pyodbc.Connection): the connection to the database
        queue_id (str): the queue_id for the item being processed
    '''
    process = 'OPTIMIZER-BEGIN' if start else 'OPTIMIZER-END'
    query = "EXEC dbo.UPDATE_OPTIMIZER_QUEUE_STATUS @QueueID = ?, @Process = ?"
    cs = con.cursor()
    cs.execute(query, (queue_id, process))
    cs.commit()


if __name__ == '__main__':
    username = 'KSMTA_OPTIMIZER_USER'
    account = 'a8639454119861-ue85361'

    password = keyring.get_password("ksm", username)

    db_configs = {
        "server": "ksm-ksmta-sqlsrv-001.database.windows.net",
        "database": "KSMTA",
        "username": "AZURE_SQL_USERNAME",
        "password": "AZURE_SQL_PASSWORD",
        "credential_account": "ksm"
    }
    con = get_connection(db_configs)
    dataset_name = 'OrderDivision'
    json_str = {"WeeksBack": 4, "DataDelay": 1, "MaxDeadhead": 500, "MarginTarget": 0.0, "MileageRate": 1.0, \
                "UseTSP": True, "UseTwoTripLimit": False, "MaxCapacity": 99999999, "lane_load_minimum": 1, 
                "CompanyOperations": [], "LaneAggregateField": None, "LaneGeographyLevel": None, "Geography": [],\
                "BillTo": [], "OrderDivision": [], "PowerDivision": []}
    
    client_id = 1
    scenario_id = 227
    json_str = {"WeeksBack": 1, "DataDelay": 1, "MaxDeadhead": 500, 
                "MarginTarget": 30, "MileageRate": 1.556, "UseTSP": True, "UseTwoTripLimit": False, 
                "MaxCapacity": 99999999, "lane_load_minimum": 1, "CompanyOperations": [6], "LaneAggregateField": "BillToID", 
                "LaneGeographyLevel": "Zip5", "Geography": [], "BillTo": [], "OrderDivision": [], "PowerDivision": []}

    client_df = get_client_df(con)
