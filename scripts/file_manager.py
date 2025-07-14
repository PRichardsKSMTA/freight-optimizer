import os
import datetime 
import json
import pandas
import shutil

#this class is responsble for handling input and output to/from python.
class FileManager():

	def __init__(self, top_level_folder: str, load_id: str=None, input_dataset: str=None):
		self.load_id = load_id
		if load_id is None:
			self.load_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
		self.top_level_folder = top_level_folder
		if not os.path.isdir(top_level_folder + '/output/'):
			os.makedirs(top_level_folder + '/output/' )
		self.output_folder = top_level_folder + '/output/' + self.load_id +  '/'

		if input_dataset is None:
			self.input_folder = top_level_folder + '/input/'
		else: 
			self.input_folder = top_level_folder + '/input/' + input_dataset + '/'
		self.log_file = self.output_folder + '/log.txt'
		self.init_log()
		self.read_params()


	#checks for input/output folder existence, writes to log if successful.
	def init_log(self):
		if  not os.path.isdir(self.output_folder):
			os.makedirs(self.output_folder)
			message = "Output folder created at location: " + self.output_folder
			self.add_message_to_log(message=message, message_type='warning')            
		if  not os.path.isdir(self.input_folder):
			message = "No input folder exists. Expecting a folder named input at location: " + self.top_level_folder
			self.add_message_to_log(message=message, message_type='error')
			raise Exception(message)
		start_time = datetime.datetime.now()
		self.add_message_to_log('Optimization started at time: ' + start_time.strftime('%Y-%m-%d %H:%M:%S'), message_type='general')
	
	#appends a message to the log
	def add_message_to_log(self, message, message_type='warning'):
		fo = open(self.log_file,"a")
		if message_type.upper() == 'warning':
			fo.write("Warning: ")
		if message_type.upper() == 'ERROR':
			fo.write('ERROR! ')
		fo.write(message + '\n\n')
		fo.close()

	#reads parameters file at params.json
	def read_params(self):
		params_filename = self.input_folder + '/params.json'
		try:
			json_file = open(params_filename, "r")
			self.params = json.load(json_file)
			json_file.close()
		except Exception as ee:
			message = 'Unable to read input parameters file at location: ' + params_filename + ". Exception was: " + str(ee)
			self.add_message_to_log(message, 'error')
			raise ValueError(message)

	
	def parameter_validation(self, param_name: str):
		'''
		simple function for raising an error if an expected parameter is not available in
		self.params
		'''
		try:
			self.params[param_name]
		except Exception as ee:
			message = 'Expecting ' + param_name + ' parameter in params.json file.'
			self.add_message_to_log(message, 'error')
			raise ValueError(message)	
		

	def write_df_to_output(self, df: pandas.DataFrame, filename: str, index: bool=False):
		'''
		writes a pandas dataframe to the output folder
		'''
		df.to_csv(self.output_folder + '/' + filename + '.csv', index=index)

	
	def write_input_to_output(self, filename: str):
		"""Writes filename in the in input folder to the output folder,
		to create a record of the input files used in the optimization.

		Args:
			filename (str): name of the file to be copied
		"""		
		input_folder = self.output_folder + '/input/'
		if not os.path.isdir(input_folder):
			os.makedirs(input_folder)
		shutil.copyfile(self.input_folder + '/' + filename, input_folder + '/' + filename)


	def write_configs(self, configs):
		'''
		writes the configs from a dictionary to the output folder
		'''
		fo = open(self.output_folder + '/configs.txt',"w")
		for key in configs.keys():
			fo.write(key + ': ' + str(configs[key]) + '\n')
		fo.close()


	def write_results_to_output(self, results_df: pandas.DataFrame) -> None:
		'''
		writes a pandas dataframe to the output folder
		'''
		results_df.to_csv(self.output_folder + '/accepted_trips.csv', index=False)