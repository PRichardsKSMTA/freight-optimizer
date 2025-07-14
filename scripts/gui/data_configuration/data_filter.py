import datetime
from dateutil.relativedelta import relativedelta
import pandas

from database import database_functions
from gui.configuration import ModelConfiguration
from gui.runnables.scenario_load_runnable import ScenarioTableLoadWorker


class ConfigurationNameError(Exception):
    """This exception is raised when there is an issue with the database query"""
    
    def __init__(self, message):
        """This function initializes the QueryException class"""
        super().__init__(message)


class DataFilter:
    """This class is responsible for storing configurations related to data calls.
    This class will make calls to the Snowflake database to retrieve data based on input
    received through the GUI.

    This class is separate from model_configurations in that this class is responsible for
    all things input data related; whereas the model_configurations class is responsible for
    parameters related to the optimization model.

    Args:
        database_configs (dict): the database configs, which should include 'username', 
        'account', 'schema', and 'database' values

    TODO: update scenario_id when loaded or saved
    """
    def __init__(self,
                 database_configs: dict,
                 app_configs: ModelConfiguration,
                 client_id: str=None,
                 weeks_back: int=2,
                 data_delay: int=1):
        self.data_filters = {}
        self._load_configuration_df = pandas.DataFrame()
        self._loading_config_table = True
        self.app_configs = app_configs
        self.database_configs = database_configs
        self._client_id = client_id
        self._scenario_id = None
        self.screenshots = []
        if pandas.isnull(weeks_back):
            weeks_back = 1
        else:
            self.data_filters['WeeksBack'] = int(weeks_back)
        if pandas.isnull(data_delay):
            data_delay = 1
        else:
            self.data_filters['DataDelay'] = int(data_delay)
        self.last_saved_config = self.get_all_filters()


    @property
    def client_id(self) -> str:
        """This function returns the client_id

        Returns:
            str: the client_id
        """        
        return self._client_id
    

    @client_id.setter
    def client_id(self, value: str):
        """This function sets the client_id

        Args:
            value (str): the client_id
        """
        self._client_id = value

    @property
    def scenario_id(self) -> str:
        """This function returns the scenario_id

        Returns:
            str: the scenario_id
        """        
        return self._scenario_id

    @scenario_id.setter
    def scenario_id(self, value: str):
        """This function sets the scenario_id

        Args:
            value (str): the scenario_id
        """        
        self._scenario_id = value

    
    @property
    def load_configuration_df(self) -> pandas.DataFrame:
        """This function returns the load_configuration_df

        Returns:
            pandas.DataFrame: the load_configuration_df
        """        
        return self._load_configuration_df
    

    @load_configuration_df.setter
    def load_configuration_df(self, value: pandas.DataFrame):
        """This function sets the load_configuration_df

        Args:
            value (pandas.DataFrame): the load_configuration_df
        """        
        self._load_configuration_df = value

    @property
    def loading_config_table(self) -> bool:
        """This function returns the loading_config_table

        Returns:
            bool: the loading_config_table
        """        
        return self._loading_config_table

    @loading_config_table.setter
    def loading_config_table(self, value: bool):
        """This function sets the loading_config_table

        Args:
            value (bool): the loading_config_table
        """        
        self._loading_config_table = value
    
    @property
    def configuration_name(self) -> str:
        """This function returns the configuration_name

        Returns:
            str: the configuration_name
        """        
        return self.app_configs.configuration_name
    
    @configuration_name.setter
    def configuration_name(self, value: str):
        """This function sets the configuration_name

        Args:
            value (str): the configuration_name
        """        
        self.app_configs.configuration_name = value

    @property
    def configuration_note(self) -> str:
        """This function returns the configuration_note

        Returns:
            str: the configuration_note
        """        
        return self.app_configs.configuration_note
    
    @configuration_note.setter
    def configuration_note(self, value: str):
        """This function sets the configuration_note

        Args:
            value (str): the configuration_note
        """        
        self.app_configs.configuration_note = value


    def get_client_name(self) -> str:
        """This function returns the client name, if the client_id is set

        Returns:
            str: the client name
        """  
        client_id_col = self.app_configs.get_application_setting(
            'configuration_panel',
            'configuration_customer_information'
            )['customer_selection_dialog']['value_field']
        client_name_col = self.app_configs.get_application_setting(
            'configuration_panel',
            'configuration_customer_information'
            )['customer_selection_dialog']['display_field']

        if self._client_id is None:
            return None
        if self._client_id not in self.client_df[client_id_col].values:
            return None
        else:
            return self.client_df[self.client_df[client_id_col] == self._client_id][client_name_col].values[0]
        

    def set_filter(self, filter_name: str, filter_value: object):
        """This function sets a filter value in the data_filters dictionary.

        Args:
            filter_name (str): The name of the filter to set
            filter_value (object): The value of the filter to set
        """        
        self.data_filters[filter_name] = filter_value


    def get_filter(self, filter_name: str) -> object:
        """This function returns the value of the filter_name passed in.

        Args:
            filter_name (str): the name of the filter to return

        Returns:
            object: the value of this filter
        """        
        if filter_name in self.data_filters.keys():
            return self.data_filters[filter_name]
        else:
            return None
        

    def get_client_picklist(self) -> pandas.DataFrame:
        """This function returns the client picklist from the database.

        Returns:
            pandas.DataFrame: the client picklist
        """        
        con = database_functions.get_connection(self.database_configs)
        self.client_df = database_functions.get_client_df(con)
        con.close()
        return self.client_df
    
    
    def get_picklist(self, data_field: str) -> tuple[pandas.DataFrame, bool, str]:
        """This function returns a picklist from the database, using
        data_field as the lookup field.

        Args:
            data_field (str): the name of the picklist to return
        Returns:
            pandas.DataFrame: the picklist
            bool: True if there was an error, False otherwise
            str: the error message, if there was an error (else "")

        """
        err = False
        err_message = ''
        if self._client_id is None:
            err = True
            err_message = 'Client ID is not set'
            picklist_df = pandas.DataFrame()
        else:
            con = database_functions.get_connection(self.database_configs)
            try:
                picklist_df = database_functions.get_picklist(
                    con=con,
                    data_field=data_field,
                    client_id=self.client_id,
                    scenario_id=self.scenario_id,
                    param_dict=self.get_all_filters()
                    )
            except database_functions.QueryException as e:
                picklist_df = pandas.DataFrame()
                err = True
                err_message = str(e)
            con.close()
        return picklist_df, err, err_message


    def get_trial_range(self) -> tuple:
        """This function returns the trial range as a tuple

        Returns:
            tuple: the trial range
        """        

        now = datetime.datetime.now()
        week_begin_day = self.app_configs.get_application_setting("start_of_week")
        date_format = self.app_configs.get_application_setting("date_format")
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        week_begin_day_index = weekdays.index(week_begin_day.lower())

        week_begin_day_date = now - relativedelta(days=week_begin_day_index - 1)
        data_delay = self.data_filters['DataDelay']
        if pandas.isnull(data_delay):
            self.set_filter('DataDelay', 1)
            data_delay = 1
        weeks_back = self.data_filters['WeeksBack']
        if pandas.isnull(weeks_back):
            self.set_filter('WeeksBack', 2)
            weeks_back = 2
        
        trial_end_date = week_begin_day_date - relativedelta(weeks=data_delay) - relativedelta(days=1)
        trial_start_date = trial_end_date - relativedelta(weeks=weeks_back) + relativedelta(days=1)

        return (trial_start_date.strftime(date_format), trial_end_date.strftime(date_format))
    

    def get_filter_value(self, filter_name: str, ) -> object:
        """This function returns the value of the filter_name passed in.

        Args:
            filter_name (str): the name of the filter to return

        Returns:
            object: the value of this filter, or None if the filter
                has not yet been set
        """        
        if filter_name in self.data_filters.keys():
            return self.data_filters[filter_name]
        else:
            return None
        
    
    def undo_changes(self) -> None:
        """This function undoes any changes made to the data filters
        """
        if self.last_saved_config is not None:
            self.data_filters = self.last_saved_config
            self.app_configs.update_max_deadhead(self.data_filters['MaxDeadhead'])
            self.app_configs.update_margin_target(self.data_filters['MarginTarget'])
            self.app_configs.update_mileage_rate(self.data_filters['MileageRate'])
            self.app_configs.set_model_state('tsp', self.data_filters['UseTSP'])
            self.app_configs.set_model_state('two_trip_limit', self.data_filters['UseTwoTripLimit'])
        
    
    def get_all_filters(self) -> dict:
        """This function returns all of the filters

        Returns:
            dict: all of the filters
        """        
        self.data_filters['MaxDeadhead'] = self.app_configs.get_max_deadhead()
        self.data_filters['MarginTarget'] = self.app_configs.get_margin_target()
        self.data_filters['MileageRate'] = self.app_configs.get_mileage_rate()
        self.data_filters['UseTSP'] = self.app_configs.get_model_state('tsp')
        self.data_filters['UseTwoTripLimit'] = self.app_configs.get_model_state('two_trip_limit')
        self.data_filters['MaxCapacity'] = self.app_configs.get_max_capacity()
        self.data_filters['MinMiles'] = self.app_configs.get_min_miles()

        return self.data_filters


    def save_configuration(self, 
                           configuration_name: str=None, 
                           configuration_note: str=None,
                           overwrite_existing: bool=False) -> None:
        """This function submits the data filters to the database

        Args:
            configuration_name (str, optional): the name of the configuration to save.
                If None, the configuration name will be taken from the configuration_name
                attribute. Defaults to None.
            configuration_note (str, optional): the note to save with the configuration.
                If None, the configuration note will be taken from the configuration_note
                attribute. Defaults to None.
            overwrite_existing (bool, optional): if True, the configuration will be overwritten
                if it already exists. Defaults to False.

        """        
        self.data_filters = self.get_all_filters()

        if configuration_name is None:
            configuration_name = self.app_configs.configuration_name
        else:
            self.app_configs.update_configuration_name(configuration_name)
        if configuration_note is None:
            configuration_note = self.app_configs.configuration_note

        if pandas.isnull(configuration_name) or configuration_name == '':
            raise ConfigurationNameError('Configuration name must be specified')
        else:
            pass

        con = database_functions.get_connection(self.database_configs)

        if not overwrite_existing:
            scenario_id = database_functions.add_new_scenario(
                con=con,
                client_id=self._client_id,
                json_str=self.get_all_filters(),
                scenario_name=configuration_name,
                scenario_note=configuration_note
                )
            self.scenario_id = scenario_id
        else:
            database_functions.update_scenario(
                con=con,
                scenario_id=self.scenario_id,
                client_id=self._client_id,
                json_str=self.get_all_filters(),
                scenario_name=configuration_name,
                scenario_note=configuration_note
            )
            self.load_configuration_df = database_functions.get_saved_scenarios(con, self.client_id)
        con.close()
        self.last_saved_config = {k:v for k,v in self.get_all_filters().items()}


    def capture_config_screenshot(self):
        """This function captures a screenshot of the current configuration
        """
        new_filters = self.get_all_filters().copy()
        self.screenshots.append(new_filters)

    
    def reset_to_last_screenshot(self):
        """This function resets the configuration to the last screenshot.
        This is used to undo changes made to the configuration.
        """
        if len(self.screenshots) > 0:
            self.data_filters = self.screenshots[-1]
            self.app_configs.update_max_deadhead(self.data_filters['MaxDeadhead'])
            self.app_configs.update_margin_target(self.data_filters['MarginTarget'])
            self.app_configs.update_mileage_rate(self.data_filters['MileageRate'])
            if 'MinMiles' in self.data_filters.keys():
                self.app_configs.update_min_miles(self.data_filters['MinMiles'])
            self.app_configs.set_model_state('tsp', self.data_filters['UseTSP'])
            self.app_configs.set_model_state('two_trip_limit', self.data_filters['UseTwoTripLimit'])
            self.screenshots = self.screenshots[:-1]
        else:
            pass

    
    def get_configuration_load_table(self, client_id: str) -> pandas.DataFrame:
        """This function returns a table of all configurations for the specified client_id

        Args:
            client_id (str): the client_id to return configurations for

        Returns:
            pandas.DataFrame: the table of configurations
        """        
        worker = ScenarioTableLoadWorker(self, client_id, database_configs=self.database_configs)
        self.app_configs.app_threadpool.start(worker, priority=1)


    def load_configuration(self, scenario_id: str, scenario: pandas.DataFrame=None) -> None:
        '''
        Loads the configuration at the specified scenario_id
        from load_configuration_df
        '''
        self.scenario_id = scenario_id
        if scenario is None:
            scenario = self._load_configuration_df[self._load_configuration_df['SCENARIO_ID'] == scenario_id].iloc[[0]].to_dict('records')[0]
        self.app_configs.configuration_name = scenario['SCENARIO_NAME']
        self.app_configs.configuration_note = scenario['SCENARIO_NOTE']
        self.data_filters = {}
        for item in scenario:
            if item == 'SCENARIO_ID' or item == 'SCENARIO_NAME' or item == 'SCENARIO_NOTE':
                continue
            self.set_filter(item, scenario[item])

        if 'MaxDeadhead' in self.data_filters.keys() and not pandas.isnull(self.data_filters['MaxDeadhead']):
            self.app_configs.update_max_deadhead(self.data_filters['MaxDeadhead'])
        if 'MarginTarget' in self.data_filters.keys():
            self.app_configs.update_margin_target(self.data_filters['MarginTarget'])
        if 'MileageRate' in self.data_filters.keys():
            self.app_configs.update_mileage_rate(self.data_filters['MileageRate'])
        if 'MinMiles' in self.data_filters.keys():
            self.app_configs.update_min_miles(self.data_filters['MinMiles'])
        if 'MaxCapacity' in self.data_filters.keys():
            self.app_configs.update_max_capacity(self.data_filters['MaxCapacity'])
        self.app_configs.set_model_state('tsp', self.data_filters['UseTSP'])
        self.app_configs.set_model_state('two_trip_limit', self.data_filters['UseTwoTripLimit'])

        self.last_saved_config = {k:v for k,v in self.get_all_filters().items()}

    def check_scenario_changed(self, config=None):
        '''
        Checks if the current scenario has been changed
        '''
        if config is None:
            config = self.last_saved_config
        if config is None:
            return True
        else:
            current_config = self.get_all_filters()
            if 'RUN_ID' in current_config.keys():
                del current_config['RUN_ID']
            if 'RUN_ID' in config.keys():
                del config['RUN_ID']

            return config != current_config
        
    
    def delete_configuration(self, scenario_id: str) -> None:
        """This function deletes the specified scenario_id

        Args:
            scenario_id (str): the scenario_id to delete
        """        
        con = database_functions.get_connection(self.database_configs)

        param_dict = self._load_configuration_df[self._load_configuration_df['SCENARIO_ID'] == scenario_id].iloc[0].to_dict()
        del param_dict['SCENARIO_ID']
        database_functions.soft_delete_scenario(con, scenario_id=scenario_id, client_id=self._client_id, param_dict=param_dict)
        self._load_configuration_df = self._load_configuration_df[self._load_configuration_df['SCENARIO_ID'] != scenario_id]
        con.close()
