'''
This file contains the DataManager class, which is the central handler of data objects for the optimizer.

author: Daniel Kinn
email: daniel.j.kinn@gmail.com
created: 25 September 2023
last modified: 09 December 2023
'''

import pandas
import pdb
import numpy
import itertools

from file_manager import FileManager
from utils import read_csv_with_log
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("__main__")

class DataManager:
	'''
	This class if responsbile for managing data objects for the optimizer. This includes any necessary pre-processing
	of the data.
	'''

	def __init__(self,
			  file_manager: FileManager,
			  trip_df: pandas.DataFrame,
			  empty_miles_df: pandas.DataFrame,
			  use_tours: bool=False,
			  max_deadhead: float=1000,
			  seed: int=None,
			  random_selection: iter=None,
			  require_trips: iter=[],
			  trip_eligibility_quantile: float=0.0, 
			  margin_target: float=0.0,

			  use_int32: bool=True,
			  min_distance: float=None,
			  max_distance: float=None):
		'''
			file_manager is an instance of the FileManager class
			tours is a boolean field indicating whether to use tours or trips
			max_deadhead is the maximum deadhead miles to allow between trips for the 
				connection to be considered. Set to None to consider all connections
			seed: a random seed to set (only used if random_selection is input). This 
				should be an integer value, or None to not use a random seed.
			random_selection: an integer indicating the number of trips to randomly 
				select from the dataset. Set to None to include all trips.
			require_trips: an iterable of trips that must be included in the dataset 
				(to be considered, not necessarily accepted). This is used when random
				trips are chosen.
			trip_eligibility_quantile: a float value between 0 and 1 indicating the minimum
				profit quantile for a trip to be considered for inclusion in the optimization.
			margin_target: a float value between 0 and 1 indicating the target margin for the
				optimization. This is used to calculate the margin improvement for each trip.
			use_int32: a boolean indicating whether to use int32 for integer columns to 
				reduce memory usage. Set to False to use int64.
			min_distance: a float value indicating the minimum distance that must be met
				by all accepted trips during optimization. Leave as None to not use a minimum
				distance.
			max_distance: a float value indicating the maximum distance that must not be 
				exceeded by all accepted trips during optimization. Leave as None to not use a
				maximum distance.
		'''
		logger.info('Initializing DataManager')
		self.use_tours = use_tours
		self.file_manager = file_manager
		self.max_deadhead = max_deadhead
		self.use_zip3 = True
		# self.use_zip3 = False
		self.min_distance = min_distance
		self.max_distance = max_distance
		self.trip_eligibility_quantile = trip_eligibility_quantile
		self.trip_cols = file_manager.params['data']['trips']['columns']
		self.margin_target = margin_target
		required_columns = [file_manager.params['data']['trips']['columns'][x[0]] for x in file_manager.params['data']['trips']['columnRequired'].items() if x[1]]
		self.trip_df = trip_df
		logger.info('Trip data read with ' + str(self.trip_df.shape[0]) + ' rows and ' + str(self.trip_df.shape[1]) + ' columns')

		must_take_flag = file_manager.params['data']['trips']['columns']['must_take_flag']
		if must_take_flag not in self.trip_df.columns.values:
			self.trip_df[must_take_flag] = False
		else:
			self.trip_df[must_take_flag] = self.trip_df[must_take_flag].apply(
				lambda x: False if pandas.isnull(x) or x in [' ', 'N', 'n', 'None', 'null'] else True)
		self.trip_df = self.trip_df.rename({
			self.trip_cols['trip_id']: 'trip_id',
			self.trip_cols['trip_revenue']: 'trip_revenue',
			self.trip_cols['trip_cost']: 'trip_cost',
			self.trip_cols['trip_distance']: 'trip_distance',
			self.trip_cols['trip_origin_zip']: 'trip_orgn_zip',
			self.trip_cols['trip_destination_zip']: 'trip_dst_zip',
			self.trip_cols['must_take_flag']: 'must_take_flag'
		}, axis=1)
		self.trip_df['trip_orgn_zip'] = self.trip_df['trip_orgn_zip'].apply(lambda x: str(x).zfill(5))
		self.trip_df['trip_dst_zip'] = self.trip_df['trip_dst_zip'].apply(lambda x: str(x).zfill(5))

		if use_int32:
			#check for any n/a values in trip_revenue, trip_cost, or trip_distance; If there are, remove them and log a warning
			na_rows = self.trip_df[['trip_revenue', 'trip_cost', 'trip_distance']].isnull().sum().sum()
			if na_rows > 0:
				logger.warning('There are ' + str(na_rows) + ' missing values in the trip_revenue column')
				self.trip_df = self.trip_df.dropna(subset=['trip_revenue', 'trip_cost', 'trip_distance'])
			self.trip_df['trip_revenue'] = self.trip_df['trip_revenue'].astype('int32')
			self.trip_df['trip_cost'] = self.trip_df['trip_cost'].astype('int32')
			self.trip_df['trip_distance'] = self.trip_df['trip_distance'].astype('int32')
		if not seed is None:
			numpy.random.seed(seed)
		if random_selection:
			if random_selection > self.trip_df.shape[0]:
				pass
			else:
				locs = [x for x in require_trips]
				locs.extend([x for x in numpy.random.choice(range(self.trip_df.shape[0]), random_selection-len(locs), replace=False)])
				self.trip_df = self.trip_df.iloc[locs].reset_index(drop=True)

		self.original_trip_df = self.trip_df.iloc[:]
		self.trip_df['trip_profit'] = self.trip_df['trip_revenue'] - self.trip_df['trip_cost']

		self.empty_miles_df = empty_miles_df
		logger.info('Empty miles data read with ' + str(self.empty_miles_df.shape[0]) + ' rows and ' + str(self.empty_miles_df.shape[1]) + ' columns')
		if use_int32:
			self.empty_miles_df['empty_miles'] = self.empty_miles_df['empty_miles'].astype('int32')
			self.empty_miles_df['empty_cost'] = self.empty_miles_df['empty_cost'].astype('float32')
		if not use_tours:
			self.get_potential_trips(quantile=trip_eligibility_quantile)
		else:
			self.get_potential_tours(quantile=trip_eligibility_quantile)
		logger.info('Potential trips calculated with ' + str(self.potential_trip_df.shape[0]) + ' rows and ' + str(self.potential_trip_df.shape[1]) + ' columns')
		logger.info('DataManager initialized')


	def get_deadhead_cost(self, origin_zip: str, destination_zip: str, field='empty_cost') -> float:
		"""calculates the deadhead cost between two zip codes, using 
		either the cost matrix or the empty miles file

		Args:
			origin_zip (str): _description_
			destination_zip (str): _description_

		Returns:
			float: the deadhead cost between two zip codes
		"""
		try:
			return self.empty_miles_df.loc[(str(origin_zip), str(destination_zip)), field]
		except:
			print('exception for ' + str(origin_zip) + ' to ' + str(destination_zip))
			return 99999



	def get_potential_trips(self, quantile: float=0, use_32bit: bool=True):
		'''
		This functions gets all possible permutations of two trip and calculates the profit of the tour.
		The profit of the trips is measured as the profit of the first trips, minus the deadhead
		cost between the first trip and second trip. This cost calculation is used for the tsp model. 
		'''

		def grouper_helper(x: int, grouper: pandas.core.groupby.generic.DataFrameGroupBy) -> list:
			"""This function is a helper function for the get_potential_tours function. It returns the indices of all trips that
			are connected to the input trip. This function is necessary to handle cases where a trip is not connected to any 
			other trips.

			Args:
				x (int): The index of the trip to check for connections
				grouper (pandas.core.groupby.generic.DataFrameGroupBy): the pandas grouper object 
					containing the trip to check for connections

			Returns:
				list: A list of indices of trips that are connected to the input trip
			"""			
			try:
				return [x for x in grouper.groups[x]]
			except:
				return []
			
		if self.use_zip3 or self.detect_zip3():
			self.trip_df['trip_orgn_zip'] = self.trip_df['trip_orgn_zip'].apply(lambda x: str(x)[:3])
			self.trip_df['trip_orgn_zip'] = self.trip_df['trip_orgn_zip'].apply(lambda x: str(x).ljust(5, '0'))
			self.trip_df['trip_dst_zip'] = self.trip_df['trip_dst_zip'].apply(lambda x: str(x)[:3])
			self.trip_df['trip_dst_zip'] = self.trip_df['trip_dst_zip'].apply(lambda x: str(x).ljust(5, '0'))
		potential_trips = [x for x in itertools.permutations(self.trip_df.index.values, 2)]
		self.potential_trip_df = pandas.DataFrame(data=potential_trips, columns=['t1', 't2'])
		if use_32bit:
			self.potential_trip_df['t1'] = self.potential_trip_df['t1'].astype('int32')
			self.potential_trip_df['t2'] = self.potential_trip_df['t2'].astype('int32')

		self.potential_trip_df = self.potential_trip_df.merge(
			self.trip_df[['trip_dst_zip', 'trip_profit', 'must_take_flag', 'trip_distance', 'trip_cost', 'trip_revenue']], left_on='t1', right_index=True)
		self.potential_trip_df = self.potential_trip_df.rename(
			{'trip_profit': 'trip_profit1', 'trip_dst_zip': 'trip_dst_zip1', 'must_take_flag': 'must_take_orgn'}
			, axis=1)
		if use_32bit:
			self.potential_trip_df['trip_profit1'] = self.potential_trip_df['trip_profit1'].astype('int32')
			self.potential_trip_df['trip_cost'] = self.potential_trip_df['trip_cost'].astype('int32')
			self.potential_trip_df['trip_distance'] = self.potential_trip_df['trip_distance'].astype('int32')
			self.potential_trip_df['trip_revenue'] = self.potential_trip_df['trip_revenue'].astype('int32')
		self.potential_trip_df = self.potential_trip_df.merge(self.trip_df[['trip_orgn_zip', 'must_take_flag']], left_on='t2', right_index=True)
		self.potential_trip_df = self.potential_trip_df.rename(
			{'trip_orgn_zip': 'trip_orgn_zip2', 'must_take_flag': 'must_take_dest'}, axis=1)

		self.potential_trip_df = self.potential_trip_df.merge(self.empty_miles_df, left_on=['trip_dst_zip1', 'trip_orgn_zip2'], right_index=True, how='left')
		#check if any of the empty miles are missing
		if self.potential_trip_df['empty_cost'].isnull().any():
			missing_rows = self.potential_trip_df[self.potential_trip_df['empty_cost'].isnull()]
			missing_rows = missing_rows[['trip_dst_zip1', 'trip_orgn_zip2']].drop_duplicates()
			message = 'Missing empty miles for ' + str(missing_rows.shape[0]) + ' rows. These rows will be removed from the optimization.'
			logger.warning(message)
			self.file_manager.add_message_to_log(message, 'warning')
			self.potential_trip_df = self.potential_trip_df.dropna(subset=['empty_cost'])
			# raise ValueError(f'Missing empty miles for ' + str(missing_rows.shape[0]) + ' rows')
		
		self.potential_trip_df['profit'] = self.potential_trip_df['trip_profit1'] \
									- self.potential_trip_df['empty_cost']
		self.potential_trip_df['distance'] = self.potential_trip_df['trip_distance'] \
									+ self.potential_trip_df['empty_miles']
		
		self.potential_trip_df = self.potential_trip_df[
			(self.potential_trip_df['must_take_dest']) |
			(self.potential_trip_df['must_take_orgn']) |
			(self.potential_trip_df['profit'] > -2000)]
		self.potential_trip_df['is_must_take'] = self.potential_trip_df.apply(lambda x: 1 if (x['must_take_orgn'] or x['must_take_dest']) else 0, axis=1)
		self.potential_trip_df['profit_adj'] = self.potential_trip_df['profit'] + self.potential_trip_df['is_must_take'] * 10000
		if use_32bit:
			self.potential_trip_df['profit'] = self.potential_trip_df['profit'].astype('float32')
			self.potential_trip_df['profit_adj'] = self.potential_trip_df['profit_adj'].astype('int32')


		if self.max_deadhead is not None:
			self.potential_trip_df = self.potential_trip_df[
				(self.potential_trip_df['empty_miles'] <= self.max_deadhead) |
				(self.potential_trip_df['must_take_orgn'] == True)]

		if quantile > 0:
			t1_quantile_df = self.potential_trip_df.groupby('t1')['profit'].quantile(quantile)
			t1_quantile_df = t1_quantile_df.rename('t1_quantile')
			t2_quantile_df = self.potential_trip_df.groupby('t2')['profit'].quantile(quantile)
			t2_quantile_df = t2_quantile_df.rename('t2_quantile')
			self.potential_trip_df = self.potential_trip_df.merge(t1_quantile_df, left_on='t1', right_index=True)
			self.potential_trip_df = self.potential_trip_df.merge(t2_quantile_df, left_on='t2', right_index=True)
			if use_32bit:
				self.potential_trip_df['t1_quantile'] = self.potential_trip_df['t1_quantile'].astype('float32')
				self.potential_trip_df['t2_quantile'] = self.potential_trip_df['t2_quantile'].astype('float32')

			self.potential_trip_df = self.potential_trip_df[
				(self.potential_trip_df['profit_adj'] >= self.potential_trip_df['t1_quantile']) |
				(self.potential_trip_df['profit_adj'] >= self.potential_trip_df['t2_quantile'])]
		
		
		self.potential_trip_df['margin_improvement'] = self.potential_trip_df['profit'] - self.potential_trip_df['trip_revenue'] * self.margin_target
		if use_32bit:
			self.potential_trip_df['margin_improvement'] = self.potential_trip_df['margin_improvement'].astype('float32')
		leg_idx_df = pandas.DataFrame({'t1': self.trip_df.index.values})
		grp_from = self.potential_trip_df.groupby('t1')
		leg_idx_df['potential_trip_idcs_from'] = leg_idx_df['t1'].apply(lambda x: grouper_helper(x, grp_from))
		del grp_from
	
		grp_to = self.potential_trip_df.groupby('t2')
		leg_idx_df['potential_trip_idcs_to'] = leg_idx_df['t1'].apply(lambda x: grouper_helper(x, grp_to))
		del grp_to

		self.leg_idx_df = leg_idx_df.set_index(['t1'])


	def get_potential_tours(self, quantile=0):
		'''
		This functions gets all possible combinations of two tours and calculates the profit of the tour.
		The profit of the tours is measured as the sum of the profit of the two trips, minus the deadhead
		cost of the two trips.
		This function considers (t1, t2) and (t2, t1) to be the same tour, since the cost will be the same.
		'''

		def grouper_helper(
					 x: int, 
					 grp1: pandas.core.groupby.generic.DataFrameGroupBy, 
					 grp2: pandas.core.groupby.generic.DataFrameGroupBy) -> list:
			"""This function is a helper function for the get_potential_tours function. It returns the 
			indices of all trips that are connected to the input trip. This function is necessary to handle 
			cases where a trip is not connected to any other trips.

			Args:
				x (int): The group from each grouper to check for connections
				grp1 (pandas.core.groupby.generic.DataFrameGroupBy): The first grouper, containing the first trip in the tour
				grp2 (pandas.core.groupby.generic.DataFrameGroupBy): The second grouper, containing the second trip in the tour

			Returns:
				list: A list of indices of trips that are connected to the input trip
			"""			
			ret_list = []
			try:
				ret_list.extend([y for y in grp1.groups[x]])
			except:
				pass

			try:
				ret_list.extend([y for y in grp2.groups[x]])
			except:
				pass
			return ret_list

		if self.use_zip3 or self.detect_zip3():
			self.trip_df['trip_orgn_zip'] = self.trip_df['trip_orgn_zip'].apply(lambda x: str(x)[:3])
			self.trip_df['trip_orgn_zip'] = self.trip_df['trip_orgn_zip'].apply(lambda x: str(x).ljust(5, '0'))
			self.trip_df['trip_dst_zip'] = self.trip_df['trip_dst_zip'].apply(lambda x: str(x)[:3])
			self.trip_df['trip_dst_zip'] = self.trip_df['trip_dst_zip'].apply(lambda x: str(x).ljust(5, '0'))
		potential_trips = [x for x in itertools.combinations(self.trip_df.index.values, 2)]

		self.potential_trip_df = pandas.DataFrame(data=potential_trips, columns=['t1', 't2'])
		del potential_trips

		self.potential_trip_df = self.potential_trip_df.merge(
			self.trip_df[['trip_orgn_zip', 'trip_dst_zip', 'trip_profit', 'must_take_flag', 'trip_revenue']], left_on='t1', right_index=True)

		self.potential_trip_df = self.potential_trip_df.rename(
			{'trip_profit': 'trip_profit1', 'trip_orgn_zip': 'trip_orgn_zip1', 'trip_dst_zip': 'trip_dst_zip1',
			'must_take_flag': 'must_take_orgn', 'trip_revenue': 'revenue1'}, axis=1)
		self.potential_trip_df = self.potential_trip_df.merge(self.trip_df[['trip_orgn_zip', 'trip_dst_zip', 'trip_profit', 'must_take_flag', 'trip_revenue']],
			left_on='t2', right_index=True)

		self.potential_trip_df = self.potential_trip_df.rename(
			{'trip_profit': 'trip_profit2',  'trip_orgn_zip': 'trip_orgn_zip2', 'trip_dst_zip': 'trip_dst_zip2',
			'must_take_flag': 'must_take_dest', 'trip_revenue': 'revenue2'}, axis=1)
		self.potential_trip_df['deadhead1'] = self.potential_trip_df.merge(
			self.empty_miles_df, left_on=['trip_dst_zip1', 'trip_orgn_zip2'], right_index=True)['empty_cost']

		self.potential_trip_df['deadhead2'] = self.potential_trip_df.merge(
			self.empty_miles_df, left_on=['trip_dst_zip2', 'trip_orgn_zip1'], right_index=True)['empty_cost']

		self.potential_trip_df['profit'] = self.potential_trip_df['trip_profit1'] \
									+ self.potential_trip_df['trip_profit2'] \
									- self.potential_trip_df['deadhead1'] \
									- self.potential_trip_df['deadhead2']

		self.potential_trip_df['revenue'] = self.potential_trip_df['revenue1'] + self.potential_trip_df['revenue2']

		if self.max_deadhead is not None:
			self.potential_trip_df = self.potential_trip_df[
				(self.potential_trip_df['must_take_dest']) |
				(self.potential_trip_df['must_take_orgn']) |
				(self.potential_trip_df['deadhead1'] < self.max_deadhead)]
			self.potential_trip_df = self.potential_trip_df[
				(self.potential_trip_df['must_take_dest']) |
				(self.potential_trip_df['must_take_orgn']) |
				(self.potential_trip_df['deadhead2'] < self.max_deadhead)]
			
		self.potential_trip_df = self.potential_trip_df[
			(self.potential_trip_df['must_take_dest']) |
			(self.potential_trip_df['must_take_orgn']) |
			(self.potential_trip_df['profit'] > -2000)]
		self.potential_trip_df['is_must_take'] = self.potential_trip_df.apply(lambda x: 1 if (x['must_take_orgn'] or x['must_take_dest']) else 0, axis=1)
		self.potential_trip_df['profit_adj'] = self.potential_trip_df['profit'] + self.potential_trip_df['is_must_take'] * 10000

		self.potential_trip_df = self.potential_trip_df.drop(columns=['deadhead1', 'deadhead2', 'must_take_orgn', 'must_take_dest', 
			'trip_orgn_zip1', 'trip_orgn_zip2', 'trip_dst_zip1', 'trip_dst_zip2', 'revenue1', 'revenue2'])

		t1_quantile_df = self.potential_trip_df.groupby('t1')['profit'].quantile(quantile).astype('int32')
		t1_quantile_df = t1_quantile_df.rename('t1_quantile').astype('int32')
		self.potential_trip_df = self.potential_trip_df.merge(t1_quantile_df, left_on='t1', right_index=True)
		self.potential_trip_df = self.potential_trip_df[
			(self.potential_trip_df['profit_adj'] >= self.potential_trip_df['t1_quantile'])]
		self.potential_trip_df = self.potential_trip_df.drop(columns=['t1_quantile'])
	
		self.potential_trip_df['margin_improvement'] = self.potential_trip_df['profit'] - self.potential_trip_df['revenue'] * self.margin_target

		leg_idx_df = pandas.DataFrame({'t1': self.trip_df.index.values})
		grp_from = self.potential_trip_df.groupby('t1')
		grp_to = self.potential_trip_df.groupby('t2')
		leg_idx_df['potential_trip_idcs'] = leg_idx_df['t1'].apply(lambda x: grouper_helper(x, grp_from, grp_to))
		del grp_to
		del grp_from

		self.leg_idx_df = leg_idx_df.set_index('t1')


	def get_accepted_trips(self,
		accepted_trips: pandas.DataFrame,
		output_full_tour: bool=False) -> pandas.DataFrame:
		"""This function writes the accepted trips to a .csv file

		Args:
			accepted_trips (pandas.DataFrame): The dataframe of accepted trips
			output_full_tour (bool, optional): A boolean indicating whether to output 
				the full tour list for each row. Defaults to False.

		Returns:
			pandas.DataFrame: The dataframe of accepted trips
		"""	
		consolidated_accepted_trips = accepted_trips.groupby('trip_idx').agg({
			'deadhead_cost': 'sum', 
			'full_tour': 'first', 
			'trip_set': 'first',
			'trip_legs': 'first'})
		consolidated_accepted_trips = consolidated_accepted_trips.rename({
			'trip_set': 'tour_id',
			'trip_legs': 'tour_position'
		}, axis='columns')
		consolidated_accepted_trips['tour_id'] = consolidated_accepted_trips['tour_id'].apply(lambda x: int(x))
		consolidated_accepted_trips['tour_position'] = consolidated_accepted_trips['tour_position'].apply(lambda x: int(x))
		try:
			consolidated_accepted_trips['prior_two_trips'] = consolidated_accepted_trips.apply(
				lambda x: numpy.array(x['full_tour'])
							[[(x['tour_position'] - 2) % len(x['full_tour']), (x['tour_position'] - 1) % len(x['full_tour'])]],
				axis=1)

			consolidated_accepted_trips['next_two_trips'] = consolidated_accepted_trips.apply(
				lambda x: numpy.array(x['full_tour'])
							[[(x['tour_position'] + 1) % len(x['full_tour']), (x['tour_position'] + 2) % len(x['full_tour'])]],
				axis=1)
		except:
			pass
		output_trip_df = self.original_trip_df.merge(
			consolidated_accepted_trips,
			left_index=True,
			right_index=True,
			how='left')

		output_trip_df['prior_zip'] = output_trip_df.apply(
			lambda x: None if pandas.isnull(x['deadhead_cost']) else output_trip_df[output_trip_df['trip_id'] == \
							x['full_tour'][int((x['tour_position'] - 1) % len(x['full_tour']))]]
							['trip_dst_zip'].values[0],
			axis=1)
		output_trip_df['next_zip'] = output_trip_df.apply(
			lambda x: None if pandas.isnull(x['deadhead_cost']) else output_trip_df[output_trip_df['trip_id'] == \
							x['full_tour'][int((x['tour_position'] + 1) % len(x['full_tour']))]]
							['trip_orgn_zip'].values[0],
			axis=1)

		output_trip_df['accepted'] = output_trip_df['deadhead_cost'].apply(lambda x: 0 if pandas.isnull(x) else 1)
		if not output_full_tour:
			output_trip_df = output_trip_df.drop(columns=['full_tour'])
		return output_trip_df