import os
import datetime 
import json
import pandas

import database.database_functions as dbf


#this class is responsble for handling input and output to/from the database.
class DBFileManager():

	def __init__(self, database_configs: dict, run_id: str):
		"""Initializes the DBFileManager

		Args:
			database_configs (dict): The database configurations
			run_id (str): The run_id for this optimization run
		"""		
		self.run_id = run_id
		self.use_zip3 = False
		self.database_configs = database_configs
		self.empty_miles_df = None
		if run_id is None:
			self.run_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

		self.init_log()
		print("DBFileManager init: CWD =", os.getcwd())
		print("Files here:", os.listdir(os.getcwd()))
		self.read_params()


	#checks for input/output folder existence, writes to log if successful.
	def init_log(self):
		pass
	
	#appends a message to the log
	def add_message_to_log(self, message, message_type='warning'):
		con = dbf.get_connection(self.database_configs)
		try:
			dbf.write_message_to_log(con=con, run_id=self.run_id, message=message, message_type=message_type)
		except Exception as ee:
			print ('Error writing message to log: ' + str(ee))
		con.close()


	def init_trip_df(self, con, client_id: int, scenario_id: int, data_filters: dict, run_id: str) -> None:
		'''
		This function initializes the trip_df

		Args:
			con (psycopg2.connection): the database connection
			client_id (int): the client_id
			scenario_id (int): the scenario_id
			data_filters (dict): the data filters
			run_id (str): the run_id
		'''
		trip_df = dbf.get_trip_data(
			con=con,
			client_id=client_id,
			scenario_id=scenario_id,
			weeks_back=data_filters['WeeksBack'],
			start_week=data_filters['DataDelay'],
			run_id=run_id,
			params=data_filters
		)
		
		trip_df = trip_df.rename({
			self.params['data']['trips']['columns']['trip_id']: 'trip_id',
			self.params['data']['trips']['columns']['trip_revenue']: 'trip_revenue',
			self.params['data']['trips']['columns']['trip_cost']: 'trip_cost',
			self.params['data']['trips']['columns']['trip_distance']: 'trip_distance',
			self.params['data']['trips']['columns']['trip_origin_zip']: 'trip_orgn_zip',
			self.params['data']['trips']['columns']['trip_destination_zip']: 'trip_dst_zip',
			self.params['data']['trips']['columns']['must_take_flag']: 'must_take_flag'
		}, axis=1)
		if self.use_zip3:
			trip_df['trip_orgn_zip'] = trip_df['trip_orgn_zip'].apply(lambda x: str(x)[:3])
			trip_df['trip_orgn_zip'] = trip_df['trip_orgn_zip'].apply(lambda x: str(x).ljust(5, '0'))
			trip_df['trip_dst_zip'] = trip_df['trip_dst_zip'].apply(lambda x: str(x)[:3])
			trip_df['trip_dst_zip'] = trip_df['trip_dst_zip'].apply(lambda x: str(x).ljust(5, '0'))
		
		self.trip_df = trip_df


	def init_empty_miles_df(self,
						 con,
						 client_id: str,
						 scenario_id: str,
						 data_filters: dict,
						 run_id: str) -> None:
		"""Initializes the empty miles dataframe

		Args:
			con (psycopg2.connection): the database connection
			client_id (str): The client_id to use when querying the database
			scenario_id (str): The scenario_id to use when querying the database
			data_filters (DataFilter): The data filters to use when querying the database
			run_id (str): The run_id to use when querying the database

		Modifies:
			self.empty_miles_df (pandas.DataFrame): The empty miles dataframe
		"""	
		self.empty_miles_df = dbf.get_empty_miles(
			con=con,
			client_id=client_id,
			scenario_id=scenario_id,
			data_filters=data_filters,
			run_id = run_id,
			weeks_back=data_filters['WeeksBack'],
			data_delay=data_filters['DataDelay']
		)

		self.empty_miles_df = self.empty_miles_df.rename({
				self.params['data']['empty_miles']['columns']['origin_zip']: 'origin_zip',
				self.params['data']['empty_miles']['columns']['destination_zip']: 'destination_zip',
				self.params['data']['empty_miles']['columns']['empty_miles']: 'empty_miles',
				self.params['data']['empty_miles']['columns']['empty_cost']: 'empty_cost',
		}, axis=1)
		self.empty_miles_df['empty_cost'] = self.empty_miles_df['empty_miles'].astype(float) * float(data_filters['MileageRate'])
		if len(self.empty_miles_df) == 0:
			return
		if len(self.empty_miles_df['origin_zip'].iloc[0]) == 3:
			self.use_zip3 = True
			self.empty_miles_df['origin_zip'] = self.empty_miles_df['origin_zip'].apply(lambda x: str(x).ljust(5, '0'))
		self.empty_miles_df['origin_zip'] = self.empty_miles_df['origin_zip'].apply(lambda x: str(x).zfill(5))
		self.empty_miles_df['destination_zip'] = self.empty_miles_df['destination_zip'].apply(lambda x: str(x).ljust(5, '0'))
		self.empty_miles_df['destination_zip'] = self.empty_miles_df['destination_zip'].apply(lambda x: str(x).zfill(5))
		self.empty_miles_df.set_index(['origin_zip', 'destination_zip'], inplace=True)


	def read_params(self) -> None:
		'''
		reads the database parameters from the params.json file in the input folder
		'''
		json_file = open('Input/db_params.json', "r")
		self.params = json.load(json_file)
		json_file.close()

		
	def write_results_to_output(self, results_df: pandas.DataFrame) -> None:
		'''
		writes a pandas dataframe to the database
		'''
		results_df = results_df.rename({
			'trip_id': "ORDER_ID",
			'accepted': 'IS_ACCEPTED',
			'tour_id': 'TOUR_ID',
			'tour_position': 'TOUR_POSITION',
			'deadhead_cost': 'DEADHEAD_COST',
		}, axis=1)
		# con = dbf.get_connection(self.database_configs)
		engine= dbf.get_engine(self.database_configs)
		dbf.write_output(
			engine=engine,
			run_id=self.run_id,
			df = results_df
		)
		engine.dispose()