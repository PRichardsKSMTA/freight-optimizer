'''
This is a superclass for the optimization modeler. The initial set-up 
and many of the functions for children classes are the same, so this
class is used to avoid code duplication.
'''
import logging
import pandas
from pyomo.opt import SolverFactory
from file_manager import FileManager
from data_manager import DataManager

logging.basicConfig(level=logging.INFO)

class FreightModel:

	def __init__(self,
		data_manager: DataManager,
		file_manager: FileManager,
		verbose: bool=True,
		margin_weight=0,
		write_model: bool=False):
		"""Initializes the FreightModel class

		Args:
			data_manager (DataManager): The DataManager object for this model
			file_manager (FileManager): The FileManager object for this model
			verbose (bool, optional): Whether or not to print the solver output. 
				Defaults to False.
			margin_weight (int, optional): The weight to apply to the margin 
				improvement portion of the objective function
			write_model (bool, optional): Whether or not to write the model to
				an MPS file. Defaults to False.
		"""		
		self.data_manager = data_manager
		self.file_manager = file_manager
		self.verbose = verbose
		self.margin_weight = margin_weight
		self.write_model = write_model
		logging.info('FreightModel object created.')
				

	def define_model(self):
		'''
		this function defines the objective and constraints for optimization. This function will
		be specific to each child.
		'''
		pass


	def get_human_readable_results(self) -> tuple[pandas.DataFrame, pandas.DataFrame]:
		'''
		once solved, this function iterates through the model and returns a human readable
		table of results.
		'''
		self.accepted_trips = []
		self.accepted_idcs = []
		for x in self.data_manager.potential_trip_df.index.values:
			if round(self.model.XX[x].value) == 1:
				trip = self.data_manager.potential_trip_df.loc[x]['t1']
				trip_ = self.data_manager.potential_trip_df.loc[x]['t2']
				self.accepted_idcs.append(x)
				if (trip_, trip) not in self.accepted_trips or not self.data_manager.use_tours:
					self.accepted_trips.append((trip, trip_))
		self.accepted_trips_df = pandas.DataFrame(self.accepted_trips, columns=['t1', 't2'])

		if self.data_manager.use_tours: #if we are using tours, then we have the tours as our accepted trips
			all_connected_trips = self.accepted_trips
		else: #otherwise, we need to construct the tours from our accepted trips
			all_connected_trips = []
			unhandled_trips = [x for x in self.accepted_trips_df['t1'].values if x in self.accepted_trips_df['t2'].values]
			while len(unhandled_trips) > 0:
				connected_trip = []
				trip = unhandled_trips.pop()
				connected_trip.append(trip)
				next_trip = self.accepted_trips_df[self.accepted_trips_df['t1'] == trip]['t2'].values[0]
				while next_trip not in connected_trip:
					connected_trip.append(next_trip)
					unhandled_trips.remove(next_trip)
					trip = next_trip
					next_trip = self.accepted_trips_df[self.accepted_trips_df['t1'] == trip]['t2'].values[0]
				all_connected_trips.append(connected_trip)

		trip_sets = []
		froms = []
		tos = []
		trip_ids = []
		trip_idcs = []
		is_deadheads = []
		deadhead_costs = []
		revenues = []
		trip_costs = []
		trip_miles = []
		deadhead_miles = []
		trip_legs = []
		full_tours = []

		for connected_trip_idx, connected_trip in enumerate(all_connected_trips):
			full_tour = [self.data_manager.trip_df.loc[x]['trip_id'] for x in connected_trip]
			for leg, trip_idx in enumerate(connected_trip):
				trip = self.data_manager.trip_df.loc[trip_idx]
				trip_id = trip['trip_id']
				from_ = trip['trip_orgn_zip']
				
				#check to see if we need a deadhead trip from the prior trip
				if leg > 0 and (from_ != tos[-1]):
					deadhead_costs.append(self.data_manager.get_deadhead_cost(destination_zip=str(from_), origin_zip=str(tos[-1])))
					deadhead_miles.append(self.data_manager.get_deadhead_cost(destination_zip=str(from_), origin_zip=str(tos[-1]), field='empty_miles'))
					trip_sets.append(connected_trip_idx)
					froms.append(tos[-1])
					tos.append(from_)
					is_deadheads.append(True)
					trip_ids.append(trip_id)
					revenues.append(0)
					trip_costs.append(0)
					trip_miles.append(0)
					trip_idcs.append(trip_idx)
					trip_legs.append(leg)
					full_tours.append(full_tour)

				revenues.append(self.data_manager.trip_df.loc[trip_idx]['trip_revenue'])
				trip_costs.append(self.data_manager.trip_df.loc[trip_idx]['trip_cost'])
				trip_miles.append(self.data_manager.trip_df.loc[trip_idx]['trip_distance'])
				trip_sets.append(connected_trip_idx)
				froms.append(from_)
				tos.append(trip['trip_dst_zip'])
				is_deadheads.append(False)
				trip_ids.append(trip_id)
				trip_idcs.append(trip_idx)
				deadhead_costs.append(0)
				deadhead_miles.append(0)
				trip_legs.append(leg)
				full_tours.append(full_tour)
			
			orgn = self.data_manager.trip_df.loc[connected_trip[0]]['trip_orgn_zip']

			if orgn != tos[-1]:
				deadhead_costs.append(self.data_manager.get_deadhead_cost(origin_zip=str(tos[-1]), destination_zip=str(orgn)))
				deadhead_miles.append(self.data_manager.get_deadhead_cost(origin_zip=str(tos[-1]), destination_zip=str(orgn), field='empty_miles'))
				trip_sets.append(connected_trip_idx)
				froms.append(tos[-1])
				tos.append(orgn)
				is_deadheads.append(True)
				trip_ids.append(self.data_manager.trip_df.loc[connected_trip[0]]['trip_id'])
				revenues.append(0)
				trip_costs.append(0)
				trip_miles.append(0)
				trip_idcs.append(connected_trip[0])
				trip_legs.append(0)			
				full_tours.append(full_tour)

		trip_df = pandas.DataFrame({
			'trip_set': trip_sets,
			'trip_idx': trip_idcs,
			'from': froms,
			'to':tos,
			'is_deadhead': is_deadheads,
			'trip_id': trip_ids,
			'revenue': revenues,
			'cost': trip_costs,
			'deadhead_cost': deadhead_costs,
			'trip_distance': trip_miles,
			'deadhead_distance': deadhead_miles,
			'trip_legs': trip_legs,
			'full_tour': full_tours
		})
		trip_df['total_distance'] = trip_df['trip_distance'] + trip_df['deadhead_distance']

		consolidated_fields = ['revenue', 'cost', 'deadhead_cost', 'trip_distance', 'deadhead_distance', 'total_distance', 'trip_legs']
		consolidated_trip_df = trip_df.groupby('trip_set')[consolidated_fields].agg({
			'revenue': 'sum',
			'cost': 'sum',
			'deadhead_cost': 'sum',
			'trip_distance': 'sum',
			'deadhead_distance': 'sum',
			'total_distance': 'sum',
			'trip_legs': pandas.Series.nunique,
		})
		consolidated_trip_df['profit'] = consolidated_trip_df['revenue'] - consolidated_trip_df['cost'] - consolidated_trip_df['deadhead_cost']
		consolidated_trip_df['margin'] = consolidated_trip_df['profit'] / consolidated_trip_df['revenue']

		return consolidated_trip_df, trip_df
	

	def consolidate_trip_df(self, trip_df: pandas.DataFrame) -> pandas.DataFrame:
		"""This function takes the trip_df with individual trip legs and consolidates it into a
		dataframe with one row per trip set.

		Args:
			trip_df (pandas.DataFrame): A dataframe with one row per trip leg

		Returns:
			pandas.DataFrame: A consolidated view of the trip_df with one row per trip set
		"""		
		consolidated_trip_df = trip_df.groupby('trip_set')[['revenue','cost', 'deadhead_cost', 'trip_legs']].agg({
			'revenue': 'sum',
			'cost': 'sum',
			'deadhead_cost': 'sum',
			'trip_legs': pandas.Series.nunique
		})
		consolidated_trip_df['profit'] = consolidated_trip_df['revenue'] - consolidated_trip_df['cost'] - consolidated_trip_df['deadhead_cost']
		consolidated_trip_df['margin'] = consolidated_trip_df['profit'] / consolidated_trip_df['revenue']

		return consolidated_trip_df


	def solve(self,
		solver_name: str,
		solver_time_limit=None,
		optimality_gap=None,
		warm_start_values=[]
		) -> tuple[pandas.DataFrame, pandas.DataFrame]:
		'''
		attempts to solver the model with the input parameters. If it cannot solve the model 
		feasibly, code will raise an Exception.

		Args:
			solver_name: name of the solver as a string (i.e. 'glpk', 'gurobi', 'cplex', 'mosek', etc.) 
				Solver must be installed on system and the executable should be in your system's PATH environment variable
			solver_time_limit: the maximum amount of time to allow the solver to search for an optimal solution, in seconds. 
				If no time limit is desired, enter None. After the time limit, the solver will either terminate with its 
				best feasible solution or will raise an exception if none is produced.
			optimality_gap: an float value indicating the minimum optimality gap for terminating the solver. This should be 
				a value >= 0. A value of 0.01, for example, indicates a minimum optimality gap of 1.00%.
			warm_start_values: a list of trip indices to use as a warm start for the solver. If no warm start is desired,
				use an empty list. If a warm start is desired, enter a list of trip indices to use as a warm start.
		
		Returns:
			tuple[pandas.DataFrame, pandas.DataFrame]: A tuple containing two pandas DataFrames. The first DataFrame contains
				the consolidated results of the optimization, with one row per trip set. The second DataFrame contains the
				results of the optimization, with one row per trip leg.
		'''
		logging.info('Solving model.')
		self.define_model()
		logging.info('Model defined.')
		if len(warm_start_values) > 0:
			for xx in self.data_manager.potential_trip_df.index.values:
				self.model.XX[xx].value = 0
			for yy in warm_start_values:
				if yy in self.data_manager.potential_trip_df.index.values:
					self.model.XX[yy].value = 1

		solver_name = solver_name.lower()
		self.solver = SolverFactory(solver_name)

		if solver_time_limit is None or solver_time_limit == 'none' or solver_time_limit == 'None':
			solver_time_limit = None
		else:
			solver_time_limit = int(solver_time_limit)
		if not solver_time_limit is None:
			if solver_name.lower() == 'glpk':
				self.solver.options['tmlim'] = solver_time_limit
			elif solver_name == 'cplex':
				self.solver.options['timelimit'] = solver_time_limit
			elif solver_name == 'gurobi':
				self.solver.options['TimeLimit'] = solver_time_limit
			elif solver_name.lower() == 'ipopt':
				self.solver.options['max_cpu_time'] = solver_time_limit
			elif solver_name.lower() == 'xpress':
				self.solver.options['TIMELIMIT'] = solver_time_limit
			elif solver_name.lower() == 'mosek':
				self.solver.options['dparam.optimizer_max_time'] = solver_time_limit

		if not optimality_gap is None:
			if solver_name.lower() == 'glpk':
				self.solver.options['mipgap'] = optimality_gap
			elif solver_name == 'cplex':
				self.solver.options['mipgap'] = optimality_gap
			elif solver_name == 'gurobi':
				self.solver.options['MIPGap'] = optimality_gap
			elif solver_name.lower() == 'ipopt':
				self.solver.options['tol'] = optimality_gap
			elif solver_name.lower() == 'mosek':
				self.solver.options['dparam.mio_rel_gap_const'] = optimality_gap

		self.results = self.solver.solve(self.model, tee=self.verbose)
		logging.info('Model solved.')
		if self.results['Solver'][0]['Termination condition'] == 'feasible':
			message = 'Solver terminated with a feasible solution.'
		
		elif self.results['Solver'][0]['Termination condition'] == 'optimal':
			message = 'Solver terminated with an optimal solution.'
		
		else:
			import pdb
			pdb.set_trace()
			message = 'Solver was unable to find a feasible solution. Increase maximum solve time or decrease problem size.'
			raise ValueError(message)
		
		consolidated_trip_df, trip_df = self.get_human_readable_results()
		logging.info(message)
		return consolidated_trip_df, trip_df