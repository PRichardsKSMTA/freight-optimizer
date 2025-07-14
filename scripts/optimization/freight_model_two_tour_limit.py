'''
Author: Daniel Kinn
Date: 2023-23-09

This file contains the FreightModelTwoTourLimit class, which is a subclass of FreightModel.
This class is responsible for building the freight optimization model that determines 
which trips to accept by accepting pairs of trips that increase network profitabillty
when assigned together
'''

import pyomo.environ as pe
from . import freight_model


class FreightModelTwoTourLimit(freight_model.FreightModel):

	def define_model(self):
		'''
		This function defines the model, that is, the objective function and constraints
		'''

		self.model = pe.ConcreteModel(name="Two Trip Limit Model")
		
		self.trip_set = pe.Set(initialize=self.data_manager.trip_df.index.values, doc='Trips')
		"""Build the decision variables"""
		self.model.XX = pe.Var(self.data_manager.potential_trip_df.index.values, domain=pe.Binary)


		# Objective: maximum profit from assigned trips
		def objective_rule(model):
			if self.data_manager.margin_target <= 0:
				return sum(model.XX[idx] * int(self.data_manager.potential_trip_df.loc[idx, 'profit_adj']) for idx in self.data_manager.potential_trip_df.index.values)
			else:
				return sum(model.XX[idx] * int(self.data_manager.potential_trip_df.loc[idx, 'profit_adj']) for idx in self.data_manager.potential_trip_df.index.values) +\
					sum(model.XX[idx] * int(self.data_manager.potential_trip_df.loc[idx, 'margin_improvement']) 
						for idx in self.data_manager.potential_trip_df.index.values) * self.margin_weight
		self.model.obj = pe.Objective(rule=objective_rule, sense=pe.maximize)

		# Constraint 1: all trips can be assigned at most once (or exactly once if the trip is a "must-take")
		def trip_post_connection_limit(model, tt: int):
			trips = self.data_manager.leg_idx_df.loc[tt]['potential_trip_idcs']
			if len(trips) == 0:
				if self.data_manager.trip_df.loc[tt]['must_take_flag']:
					message = 'Trip ' + str(tt) + ' is a must-take trip, but has no potential trips to connect to that meet the deadhead threshold.'
					self.data_manager.file_manager.add_message_to_log(message, 'error')
				return pe.Constraint.Skip
			
			return sum(model.XX[x] for x in trips) <= 1
		self.model.tripPostConnectionLimit = pe.Constraint(self.trip_set, rule=trip_post_connection_limit)