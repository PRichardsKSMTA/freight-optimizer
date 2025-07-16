"""This file contains the code for managing an optimization run.

Author: Daniel Kinn (daniel.j.kinn@gmail.com)
Date: 2023-11-27
"""
import json
import logging
import numpy
import pandas
import os
import pdb
import sys
import time
import uuid
from typing import Callable
import traceback

import database.database_functions as dbf
import file_manager as fm
import db_file_manager as dfm
import data_manager as dm
from optimization.freight_model_two_tour_limit import FreightModelTwoTourLimit
from optimization.freight_model_tsp import FreightModelTSP
from utils import read_csv_with_log, read_empty_miles

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.getLogger('snowflake.connector').setLevel(logging.WARNING)

# Create a file handler and set the log level
init_datetime = time.strftime('%Y%m%d%H%M%S')
logger_folder = './logs'
if not os.path.exists(logger_folder):
    os.makedirs(logger_folder)
file_handler = logging.FileHandler(os.path.join('logs', 'optimization_' + init_datetime + '.log'))
file_handler.setLevel(logging.INFO)

# Create a formatter and add it to the file handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

# Log a message
logger.info('Logging initialized')

def run_from_config_with_error_handling(**run_params):
    '''
    runs the code from the configuration object. The configuration object
    must be of type Conguration. This is the main entry point for the
    optimization code from the GUI.

    Args:
        run_params (dict): The parameters called for run_optimization
    '''
    progress_callback = run_params['progress_callback']
    id_ = run_params['id_']
    try:
        if not progress_callback is None:
            progress_callback.emit([id_, 'log', 'Starting run'])
        run_from_configuration(**run_params)
    except Exception as ee:
        traceback.print_exc() 
        print ('\n\nException: ', ee, '\n\n')
        if not progress_callback is None:
            progress_callback.emit([id_, 'error', 'Error: ' + str(ee)])
            progress_callback.emit([id_, 'log', 'Error: ' + str(ee)])

def run_from_configuration(
        client_id: int,
        scenario_id: int,
        data_filters: dict,
        database_configs: dict,
        model_type: str,
        id_: str=None, 
        progress_callback: Callable=None,
        run_id: str=None):
    '''
    runs the code from the configuration object. The configuration object
    must be of type Conguration. This is the main entry point for the
    optimization code from the GUI.

    Args:
        params (dict): The parameters called for run_optimization
        id_ (str, optional): The id of the runnable.
        progress_callback (Callable, optional): The callback function to call
            when sending a progress update signal. Defaults to None.
    '''

    if run_id is None:
        run_id = uuid.uuid4().hex
    try:
        if not progress_callback is None:
            progress_callback.emit([id_, 'running'])
            progress_callback.emit([id_, 'run_id', run_id])
        file_manager = dfm.DBFileManager(database_configs, run_id)
    except Exception as ee:
        _, _, exc_tb = sys.exc_info()
        traceback = exc_tb.tb_frame.f_code.co_filename + ' line ' + str(exc_tb.tb_lineno)
        if not progress_callback is None:
            progress_callback.emit([id_, 'log', 'Error initializing file manager.'])
            progress_callback.emit([id_, 'error', 'Error initializing file manager.'])

    try:
        con = dbf.get_connection(database_configs)
        file_manager.init_trip_df(con, client_id, scenario_id, data_filters, run_id)
        if file_manager.trip_df is None or len(file_manager.trip_df) == 0:
            message = 'No trip data found.'
            file_manager.add_message_to_log(message, 'error')
            if not progress_callback is None:
                progress_callback.emit([id_, 'log', 'No trip data found.'])
                progress_callback.emit([id_, 'error'])
            return
        if not progress_callback is None:
            progress_callback.emit([id_, 'num_trips', len(file_manager.trip_df)])
            progress_callback.emit([id_, 'log', 'Loaded ' + str(len(file_manager.trip_df)) + ' trip entries.'])


        file_manager.init_empty_miles_df(con, client_id, scenario_id, data_filters, run_id)
        if file_manager.empty_miles_df is None or len(file_manager.empty_miles_df) == 0:
            message = 'No empty miles data found.'
            file_manager.add_message_to_log(message, 'error')
            if not progress_callback is None:
                progress_callback.emit([id_, 'log', 'No empty miles data found.'])
                progress_callback.emit([id_, 'error'])
            return
        con.close()
        if not progress_callback is None:
            progress_callback.emit([id_, 'log', 'Loaded ' + str(len(file_manager.empty_miles_df)) + ' empty miles entries.'])

        
        file_manager.trip_df.to_csv('output/trip_df.csv', index=True)
        file_manager.empty_miles_df.to_csv('output/empty_miles_df.csv', index=True)

        SEED = 50
        NUM_POINTS = None
        MAX_DEADHEAD = data_filters['MaxDeadhead']
        if pandas.isnull(MAX_DEADHEAD):
            MAX_DEADHEAD = None
        SOLVER_TIME_LIMIT = 1200
        SOLVER_OPTIMALITY_GAP = 0.001

        SOLVER_NAME = file_manager.params['solver']['solverName']
        # SOLVER_NAME = 'glpk'
        MARGIN_TARGET = data_filters['MarginTarget']
        if pandas.isnull(MARGIN_TARGET):
            MARGIN_TARGET = 0.00
        elif MARGIN_TARGET > 1: #if this is the case, then the user has entered a percentage
            MARGIN_TARGET /= 100
        if model_type == 'two_tour_limit':
            MODEL = 'two_tour_limit'
        elif model_type == 'tsp':
            MODEL = 'tsp'
        else:
            raise ValueError('Model must be either "two_tour_limit" or "tsp"')

        if 'MinMiles' in data_filters:
            MINIMUM_DISTANCE = data_filters['MinMiles']
        else:
            MINIMUM_DISTANCE = None
        if 'MaxCapacity' in data_filters:
            MAXIMUM_DISTANCE = data_filters['MaxCapacity']

        try:
            if file_manager.trip_df.shape[0] < 500:
                TRIP_ELIGIBLITY_QUANTILE = 0.0
            elif file_manager.trip_df.shape[0] < 1000:
                TRIP_ELIGIBLITY_QUANTILE = 0.5
            elif file_manager.trip_df.shape[0] < 2000:
                TRIP_ELIGIBLITY_QUANTILE = 0.75
            elif file_manager.trip_df.shape[0] < 4000:
                TRIP_ELIGIBLITY_QUANTILE = 0.85
            elif file_manager.trip_df.shape[0] < 6000:
                TRIP_ELIGIBLITY_QUANTILE = 0.9
            elif file_manager.trip_df.shape[0] < 8000:
                TRIP_ELIGIBLITY_QUANTILE = 0.95
            elif file_manager.trip_df.shape[0] < 10000:
                TRIP_ELIGIBLITY_QUANTILE = 0.97
            else:
                TRIP_ELIGIBLITY_QUANTILE = 0.98
            
            res = run_optimization(trial_name=None,
                            seed=SEED,
                            num_points=NUM_POINTS,
                            max_deadhead=MAX_DEADHEAD,
                            solver_name=SOLVER_NAME,
                            solver_time_limit=SOLVER_TIME_LIMIT,
                            solver_optimality_gap=SOLVER_OPTIMALITY_GAP,
                            margin_target=MARGIN_TARGET,
                            file_manager=file_manager,
                            model=MODEL,
                            trip_df=file_manager.trip_df,
                            empty_miles_df=file_manager.empty_miles_df,
                            trip_eligibility_quantile=TRIP_ELIGIBLITY_QUANTILE,
                            min_distance=MINIMUM_DISTANCE,
                            max_distance=MAXIMUM_DISTANCE
                            )
            if not progress_callback is None:
                (file_manager, trip_df, consolidated_trip_df, data_prep_time, optimization_time, output_df) = res
                progress_callback.emit([id_, 'profit', consolidated_trip_df['profit'].sum()])
                progress_callback.emit([id_, 'completed'])
        except Exception as ee:
            _, _, exc_tb = sys.exc_info()
            traceback = exc_tb.tb_frame.f_code.co_filename + ' line ' + str(exc_tb.tb_lineno)
            print ('Traceback: ', traceback)
            print ('\n\nException: ', ee, '\n\n')
            if not progress_callback is None:
                progress_callback.emit([id_, 'error', 'Error: ' + str(ee)])
                progress_callback.emit([id_, 'log', 'Error: ' + str(ee)])
                
    except Exception as ee:
        _, _, exc_tb = sys.exc_info()
        traceback = exc_tb.tb_frame.f_code.co_filename + ' line ' + str(exc_tb.tb_lineno)
        print ('Traceback: ', traceback)
        print ('\n\nException: ', ee, '\n\n')
        file_manager.add_message_to_log(message='Unknown error during optimization. Traceback: ' + traceback, message_type='error')
        if not progress_callback is None:
            progress_callback.emit([id_, 'error'])


def validate_optimization_parameters(params: dict, file_manager: fm.FileManager) -> None:
    """This function validates the optimization parameters

    Args:
        params (dict): The parameters called for run_optimization
        file_manager (fm.FileManager): The file manager object for this trial
    """
    solver_optimality_gap = params['solver_optimality_gap']
    if solver_optimality_gap < 0:
        err_msg = 'solver_optimality_gap must be greater than or equal to 0'
        file_manager.add_message_to_log(err_msg, 'error')
        raise ValueError(err_msg)
    
    if solver_optimality_gap > 1:
        err_msg = 'solver_optimality_gap must be less than or equal to 1'
        file_manager.add_message_to_log(err_msg, 'error')
        raise ValueError(err_msg)
    
    max_deadhead = params['max_deadhead']
    if max_deadhead is not None:
        if max_deadhead < 0:
            err_msg = 'max_deadhead must be greater than or equal to 0'
            file_manager.add_message_to_log(err_msg, 'error')
            raise ValueError(err_msg)
    
    margin_target = params['margin_target']
    if margin_target < 0:
        err_msg = 'margin_target must be greater than or equal to 0'
        file_manager.add_message_to_log(err_msg, 'error')
        raise ValueError(err_msg)
    if margin_target > 1:
        warning_msg = 'margin_target is greater than 1.'
        file_manager.add_message_to_log(warning_msg, 'warning')

    solver_time_limit = params['solver_time_limit']
    if solver_time_limit < 0:
        err_msg = 'solver_time_limit must be greater than or equal to 0'
        file_manager.add_message_to_log(err_msg, 'error')
        raise ValueError(err_msg)
    
    if solver_time_limit > 3600*24:
        warning_msg = 'solver_time_limit is greater than 24 hours.'
        file_manager.add_message_to_log(warning_msg, 'warning')


def split_dataset(trip_df: pandas.DataFrame,
                num_splits: int=1) -> list:
    """This function splits the dataset into num_splits parts. For
    now, it just randomly samples the dataset into num_splits parts,
    that are mutually exclusive and fully exhaustive.
    #TODO: Implement a more sophisticated splitting algorithm

    Args:
        trip_df (pandas.DataFrame): The trip dataframe to split
        empty_miles_df (pandas.DataFrame): The empty miles dataframe
            split. Only entries in empty_miles_df that appear in the
            corresponding trip_df will be included in each split
        num_splits (int): The number of splits to use

    Returns:
        list: A list of dataframes, each representing a split
    """
    trip_dfs = []
    remaining_indices = trip_df.index.tolist()
    random_seed = 1
    numpy.random.seed(random_seed)
    for i in range(num_splits):
        if i == num_splits - 1:
            split_indices = remaining_indices
        else:
            split_indices = trip_df.sample(frac=1/num_splits).index.tolist()
        iter_trip_df = trip_df.loc[split_indices]
        trip_dfs.append(iter_trip_df)
        remaining_indices = [x for x in remaining_indices if x not in split_indices]
        
    return trip_dfs



def run_optimization(trial_name: str,
                     solver_name: str,
                     seed: int=None,
                     num_points: int=None,
                     max_deadhead: int=None,
                     solver_time_limit: int=3600, 
                     solver_optimality_gap: float=0.0001, 
                     margin_target: float=0.,
                     trip_eligibility_quantile: float=0.,
                     model: str='two_tour_limit',
                     verbose: bool=False,
                     data_manager: dm.DataManager=None,
                     write_model: bool=False,
                     file_manager: fm.FileManager=None,
                     trip_df: pandas.DataFrame=None,
                     empty_miles_df: pandas.DataFrame=None,
                     min_distance: int=None,
                     max_distance: int=None,
                     split: int=1):
    """This function runs the optimization, using the input parameters

    Args:
        trial_name (str): The name of the trial. This trial should be located at
            input/{trial_name}
        solver_name (str): The name of the solver to use for optimization. This 
            solver must be installed on the machine and accessible via the name
            used
        seed (int, optional): A seed to use for randomization. Defaults to None.
        num_points (int, optional): The number of points to use from the input
            dataset. Defaults to None, meaning all points will be used.
        max_deadhead (int, optional): The maximum deadhead parameter for this 
            trial. Defaults to None.
        solver_time_limit (int, optional): The solver time limit. Defaults to 3600.
        solver_optimality_gap (float, optional): The solver optimality gap. Defaults to 0.0001.
        margin_target (float, optional): The margin target for this trial. Defaults to 0.
        trip_eligibility_quantile (float, optional): The trip eligibility
            quantile to use for cutting out unlikely connections. Setting this
            parameter to higher values will speed up run-times. Maximum value
            is 1. Defaults to 0.
        model (str, optional): The model to be used; must be one of
            ['tsp', 'two_tour_limit']. Defaults to 'two_tour_limit'.
        verbose (bool, optional): Whether to print debugging messages to
            console. Defaults to False.
        data_manager (dm.DataManager, optional): A DataManager instance
            to use for this problem. Defaults to None, meaning the DataManager
            class will be instantiated from this function.
        split: int, optional: The number of splits to use for the optimization. Defaults to 1,
            meaning no splits are used. 
    """   

    if file_manager is None:
        file_manager = fm.FileManager(top_level_folder='./', input_dataset=trial_name)
        file_manager.write_configs({
            'TRIAL_NAME': trial_name,
            'SEED': seed,
            'NUM_POINTS': num_points,
            'MAX_DEADHEAD': max_deadhead,
            'SOLVER_NAME': solver_name,
            'SOLVER_TIME_LIMIT': solver_time_limit,
            'SOLVER_OPTIMALITY_GAP': solver_optimality_gap,
            'MARGIN_TARGET': margin_target,
            'MODEL': model,
            'TRIP_ELIGIBILITY_QUANTILE': trip_eligibility_quantile
        })

    validate_optimization_parameters({
        'solver_optimality_gap': solver_optimality_gap,
        'max_deadhead': max_deadhead,
        'margin_target': margin_target,
        'solver_time_limit': solver_time_limit
    }, file_manager)

    start = time.time()
    use_tours = model == 'two_tour_limit' #use_tours parameter is only used in the two_tour_limit model
    optimization_time = 0
    data_prep_time = 0
    if trip_df is None or empty_miles_df is None:
        required_columns = [file_manager.params['data']['trips']['columns'][x[0]] for x in \
                            file_manager.params['data']['trips']['columnRequired'].items() if x[1]]
        trip_df = read_csv_with_log(
					filename='trips',
					unique_columns=[file_manager.params['data']['trips']['columns']['trip_id']], 
					required_columns=required_columns,
					identifier='Trips',
					file_manager=file_manager
        		)
    if empty_miles_df is None:
        empty_miles_df = read_empty_miles(file_manager)

    trip_dfs = split_dataset(trip_df, split)
    all_output_df = []
    all_consolidated_trip_df = []
    if min_distance is not None:
        iter_min_distance = int(min_distance / split)
    else:
        iter_min_distance = None
    if max_distance is not None:
        iter_max_distance = int(max_distance / split)
    else:
        iter_max_distance = None
    for iter_trip_df in trip_dfs:

        if iter_trip_df.shape[0] < 500:
            trip_eligibility_quantile = 0.0
        elif iter_trip_df.shape[0] < 1000:
            trip_eligibility_quantile = 0.5
        elif iter_trip_df.shape[0] < 2000:
            trip_eligibility_quantile = 0.75
        elif iter_trip_df.shape[0] < 4000:
            trip_eligibility_quantile = 0.85
        elif iter_trip_df.shape[0] < 6000:
            trip_eligibility_quantile = 0.9
        elif iter_trip_df.shape[0] < 8000:
            trip_eligibility_quantile = 0.95
        elif iter_trip_df.shape[0] < 10000:
            trip_eligibility_quantile = 0.97
        else:
            trip_eligibility_quantile = 0.98
        if data_manager is None:
            data_manager = dm.DataManager(file_manager, use_tours=use_tours, seed=seed, random_selection=num_points, max_deadhead=max_deadhead, 
                                        trip_eligibility_quantile=trip_eligibility_quantile, margin_target=margin_target,
                                        trip_df=iter_trip_df, empty_miles_df=empty_miles_df, min_distance=iter_min_distance, 
                                        max_distance=iter_max_distance)
        end = time.time()
        data_prep_time += end-start
        start = time.time()
        iters = 0
        warm_start_values = []
        margin_weight = 0
        while iters < 30:
            iters += 1
            if model == 'two_tour_limit':
                opt = FreightModelTwoTourLimit(data_manager,
                                                file_manager,
                                                verbose=verbose,
                                                margin_weight=margin_weight,
                                                write_model=write_model)
            elif model == 'tsp':
                opt = FreightModelTSP(data_manager,
                                    file_manager,
                                    verbose=verbose,
                                    margin_weight=margin_weight,
                                    write_model=write_model)
            else: 
                raise ValueError('model must be either "two_tour_limit" or "tsp"')
            consolidated_trip_df, out_trip_df = opt.solve(warm_start_values=warm_start_values,
                                                    solver_name=solver_name,
                                                    solver_time_limit=solver_time_limit,
                                                    optimality_gap=solver_optimality_gap)
            
            if consolidated_trip_df['revenue'].sum() == 0:
                if consolidated_trip_df['profit'].sum() == 0:
                    current_margin = 0
                else:
                    current_margin = 1
            else:
                current_margin = consolidated_trip_df['profit'].sum() / consolidated_trip_df['revenue'].sum()

            if verbose:
                print ('Margin for iteration ', iters, ' is ', current_margin)
            if margin_target > 0 and current_margin < margin_target:
                warm_start_values = [x for x in opt.accepted_idcs]
                target_off_by = data_manager.potential_trip_df.loc[warm_start_values]
                current_objective = consolidated_trip_df['profit'].sum()
                off_by = -(target_off_by['profit'] - target_off_by['trip_revenue'] * margin_target).sum() / current_objective
                # off_by = -target_off_by['margin_improvement'].sum()  / float(current_objective)
                margin_weight *= (1+iters/100)
                margin_weight += off_by * (2*iters)
        
            else:
                break

        if current_margin < margin_target:
            message = 'Unable to meet margin threshold. Please try again with a lower margin target or higher margin trips.'
            if data_manager.trip_df['must_take_flag'].sum() > 0:
                message += ' It is possible that some of the must-take trips are preventing the margin target from being met.'
            file_manager.add_message_to_log(message, 'error')

        end = time.time()
        optimization_time += end-start
        # if verbose:
        #     print ("data prep time: ", data_prep_time)
        #     print ("optimization time: ", optimization_time)

        #     print('total time: ', end-start)
        #     print ('total profit: ', consolidated_trip_df['profit'].sum())
        #     print ('total time: ', end-start)   
        
        iter_output_df = data_manager.get_accepted_trips(out_trip_df)
        all_output_df.append(iter_output_df)
        all_consolidated_trip_df.append(consolidated_trip_df)

    output_df = pandas.concat(all_output_df)
    consolidated_trip_df = pandas.concat(all_consolidated_trip_df)
    file_manager.write_results_to_output(output_df)
    file_manager.add_message_to_log('Total profit: ' + str(consolidated_trip_df['profit'].sum()), message_type='general')
    file_manager.add_message_to_log('Total time: ' + str(end-start), message_type='general')
    file_manager.add_message_to_log('Total trips: ' + str(len(trip_df)), message_type='general')
    file_manager.add_message_to_log('Total run time: ' + str(end-start), message_type='general')
    file_manager.add_message_to_log('Total data prep time: ' + str(data_prep_time), message_type='general')
    file_manager.add_message_to_log('Total optimization time: ' + str(optimization_time), message_type='general')
    return file_manager, trip_df, consolidated_trip_df, data_prep_time, optimization_time, output_df


def run_from_input(trial_name, run_params):
    '''
    This function runs optimization based on an input fileset located at
    input/{trial_name}; this should not be called from within the GUI.
    '''


    # MINIMUM_DISTANCE = 955000

    # margin = 1
    # while margin > MARGIN_TARGET and MINIMUM_DISTANCE <= MAXIMUM_DISTANCE:
    file_manager = fm.FileManager(top_level_folder='./', input_dataset=trial_name)
    res = run_optimization(
        trial_name=None,
        file_manager=file_manager,
        **run_params
    )
    # (file_manager, trip_df, consolidated_trip_df, data_prep_time, optimization_time, output_df) = res
    # margin = consolidated_trip_df['profit'].sum() / consolidated_trip_df['revenue'].sum()
    return res


if __name__ == '__main__':

    '''
    This is the main entry point for the optimization code. It is called
    from the command line with the following command:
    python manager.py <trial_name>

    Where <trial_name> is the name of the trial to run. This trial should be
    '''

    
    SEED = 50
    NUM_POINTS = None
    MAX_DEADHEAD = 500
    SOLVER_TIME_LIMIT = 60*60
    SOLVER_OPTIMALITY_GAP = 0.001
    SOLVER_NAME = 'mosek'
    MARGIN_TARGET = 0.0
    # TRIAL_NAME = sys.argv[1]
    MODEL = 'tsp'
    TRIP_ELIGIBLITY_QUANTILE = 0
    MINIMUM_DISTANCE = None
    MAXIMUM_DISTANCE = None

    run_params = {
        'seed': SEED,
        'num_points': NUM_POINTS,
        'max_deadhead': MAX_DEADHEAD,
        'solver_time_limit': SOLVER_TIME_LIMIT,
        'solver_optimality_gap': SOLVER_OPTIMALITY_GAP,
        'solver_name': SOLVER_NAME,
        'margin_target': MARGIN_TARGET,
        'model': MODEL,
        'trip_eligibility_quantile': TRIP_ELIGIBLITY_QUANTILE,
        'min_distance': MINIMUM_DISTANCE,
        'max_distance': MAXIMUM_DISTANCE
    }

    trial_splits = []
    trial_run_times = []
    trial_revenues = []
    trial_costs = []
    trial_deadhead_costs = []
    trial_profits = []
    trial_margins = []
    trial_num_trips = []
    trial_solvers = []
    

    output_filename = os.path.join('.', 'output', 'stress_results.csv')
    if not os.path.exists(os.path.join('.', 'output')):
        os.makedirs(os.path.join('.', 'output'))
    solvers = ['mosek', 'gurobi']
    if os.path.exists(output_filename):
        df = pandas.read_csv(output_filename)
    else:
        df = pandas.DataFrame()
    
    for trial_name in ['trial10', 'trial11', 'trial12']:
        for split in [4, 2, 1]:
            for solver in solvers:
                # try:
                if df.shape[0] > 0 and df[(df['trial_name'] == trial_name) &\
                                        (df['split'] == split) &\
                                            (df['solver'] == solver)].shape[0] > 0:
                    continue

                run_params['split'] = split
                run_params['solver_name'] = solver
                run_time = time.time()
                file_manager, trip_df, consolidated_trip_df, data_prep_time, optimization_time, output_df = run_from_input(trial_name, run_params=run_params)
                    
                total_run_time = time.time() - run_time
                revenue = consolidated_trip_df['revenue'].sum()
                cost = consolidated_trip_df['cost'].sum()
                deadhead_cost = consolidated_trip_df['deadhead_cost'].sum()
                profit = consolidated_trip_df['profit'].sum()
                margin = profit / revenue

                # trial_splits.append(split)
                # trial_run_times.append(total_run_time)
                # trial_revenues.append(revenue)
                # trial_costs.append(cost)
                # trial_deadhead_costs.append(deadhead_cost)
                # trial_profits.append(profit)
                # trial_margins.append(margin)
                # trial_num_trips.append(len(trip_df))
                # trial_solvers.append(solver)
            
                trial_results = pandas.DataFrame({
                    'split': [split],
                    'run_time': [total_run_time],
                    'revenue': [revenue],
                    'cost': [cost],
                    'deadhead_cost': [deadhead_cost],
                    'profit': [profit],
                    'margin': [margin],
                    'num_trips': [len(trip_df)],
                    'solver': [solver],
                    'trial_name': [trial_name]
                })

                if os.path.exists(output_filename):
                    all_trial_results = pandas.concat([pandas.read_csv(output_filename), trial_results])
                else:
                    all_trial_results = trial_results
                all_trial_results.to_csv(output_filename, index=False)
                # except:
                #     continue

    
    # trial_results.to_csv('output/' + TRIAL_NAME + '_' + timestamp + '_results.csv', index=False)
    import pdb
    pdb.set_trace()




    # SEED = 50
    # NUM_POINTS = None
    # MAX_DEADHEAD = 500
    # SOLVER_TIME_LIMIT = 60*60*3
    # SOLVER_OPTIMALITY_GAP = 0.0001
    # SOLVER_NAME = 'glpk'
    # MARGIN_TARGET = 0.3
    # MAX_CAPACITY = 3650000
    # # TRIAL_NAME = sys.argv[1]
    # # MODEL = 'two_tour_limit'
    # MODEL = 'tsp'
    # TRIP_ELIGIBLITY_QUANTILE = 0.5
    # trip_df = pandas.read_csv('output/trip_df.csv')
    # empty_miles_df = pandas.read_csv('output/empty_miles_df.csv')
    # empty_miles_df['origin_zip'] = empty_miles_df['origin_zip'].apply(lambda x: str(x).zfill(5))
    # empty_miles_df['destination_zip'] = empty_miles_df['destination_zip'].apply(lambda x: str(x).zfill(5))
    # empty_miles_df.set_index(['origin_zip', 'destination_zip'], inplace=True)
    # db_configs = json.load(open('configurations/gui_configurations.json', 'r'))['database_configurations']
    # file_manager = dfm.DBFileManager(database_configs=db_configs, run_id=uuid.uuid4().hex)

    # # file_manager = fm.FileManager(top_level_folder='./', input_dataset=TRIAL_NAME)

    # res = run_optimization(
    #         trial_name=None,
    #         seed=SEED,
    #         num_points=NUM_POINTS,
    #         max_deadhead=MAX_DEADHEAD, 
    #         solver_name=SOLVER_NAME,
    #         solver_time_limit=SOLVER_TIME_LIMIT,
    #         solver_optimality_gap=SOLVER_OPTIMALITY_GAP,
    #         margin_target=MARGIN_TARGET,
    #         verbose=True,
    #         model=MODEL,
    #         trip_eligibility_quantile=TRIP_ELIGIBLITY_QUANTILE,
    #         trip_df=trip_df,
    #         empty_miles_df=empty_miles_df,
    #         file_manager=file_manager
    # )
    # (file_manager, trip_df, consolidated_trip_df, data_prep_time, optimization_time, output_df) = res