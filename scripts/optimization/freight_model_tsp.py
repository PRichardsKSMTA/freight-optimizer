'''
Author: Daniel Kinn
Date: 2023-23-09

This file contains the FreightModelTSP class, which is a subclass of the FreightModel class. This class
is responsible for building the freight optimization model using a modified traveling salesman problem without
tour elimination and without the requirement that all trips must be assigned. There is no minimum or
maximum limit to the number of tours that can be created.
'''
import logging
import pyomo.environ as pe
from . import freight_model

logger = logging.getLogger("__main__")

class FreightModelTSP(freight_model.FreightModel):
	'''
	This problem solves the freight optimization model using a modified traveling salesman problem without 
	tour elimination and without the requirement that all trips must be assigned. There is no minimum or
	maximum limit to the number of tours that can be created.
	'''

	def define_model(self):
		self.model = pe.ConcreteModel(name="Modified Traveling Salesman Problem")
		
		self.trip_set = pe.Set(initialize=self.data_manager.trip_df.index.values, doc='Trips')
		"""Build the decision variables"""
		self.model.XX = pe.Var(self.data_manager.potential_trip_df.index.values, domain=pe.Binary)
		
		def objective_rule(model):
			if self.data_manager.margin_target <= 0:
				return sum(model.XX[x] * int(self.data_manager.potential_trip_df.loc[x, 'profit_adj']) for x in self.data_manager.potential_trip_df.index.values)
			else:
				return sum(model.XX[x] * int(self.data_manager.potential_trip_df.loc[x, 'profit_adj']) for x in self.data_manager.potential_trip_df.index.values) +\
					sum(model.XX[x] * int(self.data_manager.potential_trip_df.loc[x, 'margin_improvement']) 
						for x in self.data_manager.potential_trip_df.index.values) * self.margin_weight
		self.model.obj = pe.Objective(rule=objective_rule, sense=pe.maximize)
		logger.info('Objective function generated: maximize profit and margin improvement added to model.')

		# Constraint 1: all trips must be connected to one other post trip
		def constraint_equal_connections(model, tt: int):
			other_trips_from = self.data_manager.leg_idx_df.loc[tt]['potential_trip_idcs_from']
			other_trips_to = self.data_manager.leg_idx_df.loc[tt]['potential_trip_idcs_to']
			if len(other_trips_from) == 0:
				return pe.Constraint.Skip
			return sum(model.XX[x] for x in other_trips_from) == sum(model.XX[x] for x in other_trips_to)
		self.model.constraint_equal_connections = pe.Constraint(self.trip_set, rule=constraint_equal_connections)
		logger.info('Constraint 1 generated: all trips must be connected to one other post trip added to model.')


		# Constraint 2: all trips must be connected to, at most, one other prior 
		# trip (or exactly once if the trip is a "must-take")
		def constraint_ticket_prior_connection(model, tt: int):
			other_trips_to = self.data_manager.leg_idx_df.loc[tt]['potential_trip_idcs_to']

			if len(other_trips_to) == 0:
				if self.data_manager.trip_df.loc[tt]['must_take_flag']:
					message = 'Trip ' + str(tt) + ' is a must-take trip, but has no potential prior trips to connect to that meet the deadhead threshold.'
					self.data_manager.file_manager.add_message_to_log(message, 'error')
				return pe.Constraint.Skip	

			return sum(model.XX[x] for x in other_trips_to) <= 1
		self.model.constraintTripPriorConnection = pe.Constraint(self.trip_set, rule=constraint_ticket_prior_connection)
		logger.info('Constraint 2 generated: all trips must be connected to, at most, one other prior trip added to model.')


		# Constraint 3: (optional) The total miles traveled must meet a minimum threshold
		def constraint_distance_minimum(model):
			return sum(model.XX[x] * self.data_manager.potential_trip_df.loc[x, 'distance'] \
			  for x in self.data_manager.potential_trip_df.index.values) >= \
				self.data_manager.min_distance
		if not self.data_manager.min_distance is None and self.data_manager.min_distance > 0:
			self.model.constraintDistanceMinimum = pe.Constraint(rule=constraint_distance_minimum)
			logger.info('Constraint 3 generated: total miles traveled must meet a minimum threshold added to model.')

		# Constraint 4: (optional) The total miles traveled must not exceed a maximum threshold
		def constraint_distance_maximum(model):
			return sum(model.XX[x] * self.data_manager.potential_trip_df.loc[x, 'distance'] \
			  for x in self.data_manager.potential_trip_df.index.values) <= \
				self.data_manager.max_distance
		if not self.data_manager.max_distance is None and self.data_manager.max_distance > 0:
			self.model.constraintDistanceMaximum = pe.Constraint(rule=constraint_distance_maximum)
			logger.info('Constraint 4 generated: total miles traveled must not exceed a maximum threshold added to model.')

		if self.write_model:
			self.model.write("model.lp")