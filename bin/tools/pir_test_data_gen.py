"""
Author	: Setu Gupta
Email	: setu18190@iiitd.ac.in
Date	: 24th Jan 2021

This tool is use to test perceptrons with different pir on server.
The prediction is based on router level instead of port level
The tool can be used via the following command
	python3 path/to/this/file path/to/benchmark/directory number_of_helper_gen_processes_to_use number_of_helper_merge_processes_to_use pir
NOTE: This tool searches for noxim executable via the following path: ./../noxim
"""
import sys									# Used to read arguments
import os									# Used to run external commands
import multiprocessing as mp				# Used to parallelize workload
from queue import Empty						# Used for Empty exception
from copy import deepcopy as cp				# Used to copy arrays
from random import shuffle 					# Used to mix data around
from fcntl import lockf, LOCK_EX, LOCK_UN	# Used to lock files

# Dimensions of grid. It's used to calculate index of router
DIM_X = 8
DIM_Y = 8
# Note that the grid has origin at the top left corner and the coordinates increase in bottom right direction

# Definitions for directions
DIRECTIONS 		= 6
DIRECTION_NORTH = 0
DIRECTION_EAST  = 1
DIRECTION_SOUTH = 2
DIRECTION_WEST  = 3
DIRECTION_LOCAL = 4
DIRECTION_PE	= 5

# Size of buffers in experiment
BUFFER_SIZE = 4

# Definitions for connecting ports
#	 The buffers in noxim are only available at Rx side.
#	 As a result while extracting features for a router and a port pair, we get the Rx parameters for the correct port but the Tx parameters for connected port.
#	 To make this more clear, refer to the following illustration:
#	 ---------------------		---------------------
#	 |	Router 0		|		|	Router 1		|
#	 |		  EAST_PORT |>>>>>>>| WEST_PORT			|
#	 |					|		|					|
#	 ---------------------		---------------------
#	 The Rx parameters are a.) buffer_status and b.) cycles_since_last_flit
#	 The Tx parameters are a.) stalled_flits, b.) transmitted_flits, c.) cimmalartive_latency
#	 Details on ech of these can be found in the FeatureCollector.h
#	 Router_0/EAST_PORT will collect it's own Rx parameters and Router_1/WEST_PORT's Tx parameters
#	 Note that Rx and Tx are w.r.t Router 0 in this case.
#	 Hence to get the complete set of parameters, we must look at ports of connected router as well
"""
Generates the connected router and port pair as described by above definition
Args: router_port	: The router and port for which the corresponding connected port has to calculated
Rets: connected_router_port	: The router and port connected to router_port 

The format for both input and output is:
((router_x, router_y), port)
where:
	router_x	: The x coordinate of router on grid
	router_y	: The y coordinate of router on grid
	ports		: The direction of port for which the calculation is done
"""
def get_connected_router_and_port(router_port):
	other_router = [] # Initialise as list as tuples are immutable
	other_port = -1

	other_router = list(router_port[0]) # Initialize other router

	# Handle case of local PE and local port
	if(router_port[1] == DIRECTION_LOCAL):
		other_port = DIRECTION_LOCAL
	elif(router_port[1] == DIRECTION_PE):
		other_port = DIRECTION_PE

	# Calculate the connected router
	elif(router_port[1] == DIRECTION_NORTH):
		other_router[1] -= 1 
		other_port = DIRECTION_SOUTH
	elif(router_port[1] == DIRECTION_SOUTH):
		other_router[1] += 1 
		other_port = DIRECTION_NORTH
	elif(router_port[1] == DIRECTION_EAST):
		other_router[0] += 1 
		other_port = DIRECTION_WEST
	elif(router_port[1] == DIRECTION_WEST):
		other_router[0] -= 1 
		other_port = DIRECTION_EAST

	return (tuple(other_router), other_port)



# No. of features per port in feature file
PORT_FEATURE_COUNT = 6
PORT_FEATURE_OFFSET = 2 # The index (0 based) of first port feature

# Definitions for indexes of various parameters
ROUTER_ID		= 0
CYCLE			= 1

# Definitions for index of features in feature file
CURRENT_CYCLE			= 0
BUFFER_CAPACITY			= 1
BUFFER_STATUS			= 2
CYCLES_SINCE_LAST_FLIT	= 3
STALLED_FLITS			= 4
TRANSMITTED_FLITS		= 5
CUMULATIVE_LATENCY		= 6

# Parsed features index
PARSED_FEATURE_COUNT			= 5
PARSED_CYCLE					= 0
PARSED_BUFFER_STATUS			= 1
PARSED_CYCLES_SINCE_LAST_FLIT	= 2
PARSED_STALLED_FLITS			= 3
PARSED_TRANSMITTED_FLITS		= 4
PARSED_BUFFER_WAITING_TIME		= 5
PARSED_ANNOTATION				= 6
"""
Parses the features from given file and generates data for given router and ports
Args:
	feature_file		: Name of file having feature data
	router_and_ports	: List of router and required port
	log					: File to print log to
	ID					: ID of the caller process
Rets:
	list of the following format called router_info
	{((router_x, router_Y), port)	:	[[cycle, buffer_status, cycles_since_last_flit, stalled_flits, transmitted flits, buffer_waiting_time], ...], ...}
	where:
		router_x				: x coordinate of router on the grid
		router_y				: y coordinate of router on the grid
		port					: port for which data is stored
		cycle 					: Cycle number at which data was collected (Sorted by Cycle number in ascending order)
		buffer_status			: A value between 0 and BUFFER_SIZE indicating how much of buffer is empty
		cycles_since_last_flit	: No. of cycles since the last flit was received
		stalled_flits			: No. of flits which were not able to enter this buffer because it was full
		transmitted_flits		: No. of flits which were successfully inserted in this buffer
		buffer_waiting_time		: Average waiting time for all transmitted flits at current cycle
"""
def parse_features(feature_file, router_and_ports, log, ID):
	all_info = {}	# This dictionary stores the parsed data

	# Read data from csv file
	log.write("Process #" + str(ID) + "\tReading from file: " + feature_file + "\n")
	print("Process #" + str(ID) + "\tReading from file: " + feature_file)
	with open(feature_file, 'r') as csv_in:
		current_info = csv_in.readline()
		while current_info:
			data = current_info.split(", ") # data temporarily stores the parsed features. It's of the type list
			data = list(map(int, data))	# Map everything to integers
			# Calculate the router index in the format (router_x, router_y)
			router_id = data[ROUTER_ID] 
			router_x = router_id % DIM_X
			router_y = router_id // DIM_X
			router = (router_x, router_y)

			cycle = data[CYCLE] # Extract out the cycle

			# Iterate over all ports and add data to router_info if needed
			for port in range(DIRECTIONS):
				start_index = PORT_FEATURE_OFFSET + (port * PORT_FEATURE_COUNT) # This is the index of first feature for port (inclusive)
				end_index = start_index + PORT_FEATURE_COUNT  # This is the last index for features of port (exclusive)
				value = data[start_index : end_index] # Extract out features

				# Insert data into to all_info
				router_port = (router, port) # This is used as the key in all_info
				if(router_port not in all_info):
					all_info[router_port] = [] # Create a list if one doesn't exist yet
				all_info[router_port].append([cycle] + value) # Insert the value i.e features

			current_info = csv_in.readline()	# Read next line

	# Generate output dictionary
	log.write("Process #" + str(ID) + "\tGenerating Router info\n")
	print("Process #" + str(ID) + "\tGenerating Router info")
	router_info = {}	 # Initialize output dictionary
	for router_port in router_and_ports:
		router_info[router_port] = [] # Initialize entry in all info

		other_router = get_connected_router_and_port(router_port) # Get connected router

		assert(len(all_info[other_router]) == len(all_info[router_port]))
		enteries = len(all_info[router_port])	 # Get total number of enteries
		for idx in range(enteries):
			current_cycle_entry = []
			assert(all_info[other_router][idx][CURRENT_CYCLE] == all_info[router_port][idx][CURRENT_CYCLE])
			
			# Start inserting parameters
			# Cycle
			current_cycle_entry.append(all_info[router_port][idx][CURRENT_CYCLE])
			
			# Rx features
			current_cycle_entry.append(all_info[router_port][idx][BUFFER_STATUS])
			current_cycle_entry.append(all_info[router_port][idx][CYCLES_SINCE_LAST_FLIT])
			
			# Tx features
			current_cycle_entry.append(all_info[other_router][idx][STALLED_FLITS])
			current_cycle_entry.append(all_info[other_router][idx][TRANSMITTED_FLITS])
			if(all_info[other_router][idx][TRANSMITTED_FLITS] == 0):	# Check if no flits were transmitted
				current_cycle_entry.append(0)	# No flits transmitteed i.e 0 wating time
			else:
				current_cycle_entry.append(all_info[other_router][idx][CUMULATIVE_LATENCY] / all_info[other_router][idx][TRANSMITTED_FLITS])	# Buffer waiting time = total time the flits waited / No. of flits

			router_info[router_port].append(current_cycle_entry) # Insert in router info
	return router_info



# Length of moving average window
AVG_CYCLES = 5
ENABLE_AVG_WINDOW = True
"""
Modifies the data in router info.
Currently configured to take a moving window average on various parameters. The size of window is AVG_CYCLES
Args:
	router_info	: Input data (Not preserved)
	log			: File to print log to
	ID			: ID of the caller process
Rets:
	router_info	: Output data
The input and output formats are
	{((router_x, router_Y), port)	:	[[cycle, buffer_status, cycles_since_last_flit, stalled_flits, transmitted flits, buffer_waiting_time], ...], ...}
"""
def pre_process(router_info, log, ID):
	log.write("Process #" + str(ID) + "\tPre-processing data\n")
	print("Process #" + str(ID) + "\tPre-processing data")
	if(not ENABLE_AVG_WINDOW):	# Return without doing anything if not enabled
		return router_info

	# To optimize the averaging procedure, the moving average is taken using cummaltive sum
	# Example:
	# 	Suppose we have [1, 2, 3, 4, 5, 6] and window size is 3, 
	# 	then the following windows are constructed:
	# 	[0, 0, 1] : avg is 1-0/1 = 1
	# 	[0, 1, 3] : avg is 3-0/2 =  3/2 (Notice instread of 2, we inserted 2 + window[-1])
	# 	[1, 3, 5] : avg is 5-1/3 = 4/3 (Notice instread of 3, we inserted 3 + window[-1])
	# This makes the time complexity independent of AVG_CYCLES

	# Start moving average process
	log.write("Process #" + str(ID) + "\tTaking moving average of size " + str(AVG_CYCLES) + "\n")
	print("Process #" + str(ID) + "\tTaking moving average of size " + str(AVG_CYCLES))
	for router_port in router_info:
		windows = {	# initialize windows
			PARSED_BUFFER_STATUS 			: [0] * AVG_CYCLES,
			PARSED_CYCLES_SINCE_LAST_FLIT	: [0] * AVG_CYCLES,
			PARSED_STALLED_FLITS			: [0] * AVG_CYCLES,
			PARSED_TRANSMITTED_FLITS		: [0] * AVG_CYCLES,
			PARSED_BUFFER_WAITING_TIME		: [0] * AVG_CYCLES
		}

		current_number_of_elements_in_window = 0
		for entry_idx in range(len(router_info[router_port])): # Iterate over sample points
			for feature in windows: # Iterate over every feature
				windows[feature].pop(0)	# remove the first element 
				value_to_insert = windows[feature][-1] + router_info[router_port][entry_idx][feature] # Calculate the value to be added
				windows[feature].append(value_to_insert)	# Insert the value
				current_number_of_elements_in_window += 1
				current_number_of_elements_in_window = min(current_number_of_elements_in_window, AVG_CYCLES) # This ensures that when taling average, we divide by the correct no. of elements
				avg = (windows[feature][-1] - windows[feature][0]) / current_number_of_elements_in_window	# Calculate average

				router_info[router_port][entry_idx][feature] = avg	# Update to average value
	
	return router_info



# Define saturation levels
SATURATED = 1.0
UNSATURATED = 0.0
"""
Annotates the data in the following way:
	All the data points after start_cycle are labeled as SATURATED
	The router_info taken as input is returned with the addition of annotation
Args:	
	router_info: router data (Not preserved)
	start_cycle	: Cycle after which the router and ports are considered SATURATED
	log			: File to print log to
	ID			: ID of the caller process
Rets:
	router_info_annotated	: router_info with annotations with the following format
	{((router_x, router_Y), port)	:	[[cycle, buffer_status, cycles_since_last_flit, stalled_flits, transmitted flits, buffer_waiting_time, ANNOTATION], ...], ...}

"""
def annotate_data(router_info, start_cycle, log, ID):
	log.write("Process #" + str(ID) + "\tAnnotating data\n")
	print("Process #" + str(ID) + "\tAnnotating data")
	for router_port in router_info: # Iterate over all ports
		for entry_idx in range(len(router_info[router_port])):
			if(router_info[router_port][entry_idx][PARSED_CYCLE] >= start_cycle):	# Check if the cycle for current entry exceeds start_cycle and annotate accordingly
				router_info[router_port][entry_idx].append(SATURATED)
			else:
				router_info[router_port][entry_idx].append(UNSATURATED)
	return router_info


"""
Merges two data sets of tyoe router_info
Args:
	set_1, set_2	: Datasets to be merged
	log				: File to print log to
	ID				: ID of the caller process
Rets:
	merged	: Merged dataset
"""
def merge_info(set_1, set_2, log, ID):
	log.write("Process #" + str(ID) + "\tMerging\n")
	print("Process #" + str(ID) + "\tMerging")
	merged = {}
	for router_port in set_1:
		merged[router_port] = cp(set_1[router_port])	# Add enteries from set 1
		merged[router_port].extend(cp(set_2[router_port]))	# Add enteries from set 2

	return merged


"""
Recursively calculates the routers and ports on the path between current and destination via XY routing
Args:
	router_and_ports	: This aggregates the routers and ports on the path (Not preserved)
	current 			: This is the current router. This is add to router_and_ports every time
	direction			: This is the direction from which current receives data
	destination			: This is the final router on path
Rets: None
"""
def rec_path(router_and_ports, current, destination, direction):
	router = cp(current)
	router_and_ports.append([router, direction])	# Add current router
	if(destination == current):
		return

	# Call recursively moving closer to destinition in XY routing fashion
	if(destination[0] > current[0]):
		current[0] += 1
		rec_path(router_and_ports, current, destination, DIRECTION_WEST)
		return

	if(destination[0] < current[0]):
		current[0] -= 1
		rec_path(router_and_ports, current, destination, DIRECTION_EAST)
		return

	if(destination[0] == current[0]):
		dir_next = DIRECTION_NORTH if (destination[1] > current[1]) else DIRECTION_SOUTH
		current[1] += 1 if (destination[1] > current[1]) else -1
		rec_path(router_and_ports, current, destination, dir_next)
		return


"""
Gives the cycle path between router_1 and router_2 via XY routing
Args:
	router_1	: First router on path
	router_2	: Second router on path
Rets:
	A path containing all routers and their corresponding ports. The format is
	[((router_x, router_y]), port), ...]
	where:
		router_x	: Router's x coordinate
		router_y	: Router's x coordinate
		port		: Rx port from which router will receive data
"""
def generate_path(router_1, router_2):
	if(router_1 == router_2):
		return None
	path = []
	rec_path(path, cp(router_1), cp(router_2), DIRECTION_LOCAL)	# Generate path
	
	#Convert router and ports to tuples so that they can be hashed
	path_tuples = []
	for router_port_pair in path:
		path_tuples.append((tuple(router_port_pair[0]), router_port_pair[1]))

	#Add the local ports of starting and ending router as well
	path_tuples.append((tuple(router_2), DIRECTION_PE))

	return path_tuples 



"""
Geneates string representation of router
Example: (1, 2) gives 1_2
Args:
	router	: The router the format (router_x, router_y)
	where:
		router_x	: X coordinate of router
		router_y	: y coordinate of router
"""
def get_router_name(router):
	return str(router[0]) + "_" + str(router[1])



"""
Geneates string representation of router and port
Example: ((1, 2), 3) gives 1_2.3
Args:
	router_port	: The router and port in the format ((router_x, router_y), port)
	where:
		router_x	: X coordinate of router
		router_y	: y coordinate of router
		port		: direction
"""
def get_router_port_name(router_port):
	return get_router_name(router_port[0]) + "." + str(router_port[1])


"""
Method called by processes to generate features.
The method does the following:
1.) Creates traffic tables for attack and baseline scenarios
2.) Calls noxim to generate feature files
3.) Parses the feature files
4.) Cleans and annotates feature files
5.) Writes to per_port_features
Args:
	ID					: Process ID
	jobs				: Queue of jobs to be completed
	benchmark_name		: Root name of the benchmark to use
	working_directory	: Directory to store generated files
Rets:
	None
"""
def worker_gen(ID, jobs, benchmark_name, working_directory, pir):
	with open(working_directory + "/worker_logs_gen/worker_" + str(ID), "w", buffering = 1) as log:	# Open file for log
		log.write("Process #" + str(ID) + "\tStarting...\n")
		print("Process #" + str(ID) + "\tStarting...")
		
		# Compute till all jobs are done
		while True:
			try:
				job = jobs.get(timeout = 0.1) # Fetch next job

				# Log fetching job
				log.write("Process #" + str(ID) + "\tStarting job " + str(job) + "\n")
				print("Process #" + str(ID) + "\tStarting job " + str(job))
				
				# Fetch source and destination of attack
				src = job[0]
				dst = job[1]

				src_idx = src[1] * DIM_X + src[0]
				dst_idx = dst[1] * DIM_X + dst[0]
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 1: Create traffic tables
				log.write("Process #" + str(ID) + "\tWriting traffic tables\n")
				print("Process #" + str(ID) + "\tWriting traffic tables")
				
				source_file_path = working_directory + "/" + benchmark_name
				baseline_file_path = working_directory + "/traffic_tables/" + get_router_name(src) + "_to_" + get_router_name(dst) + "_baseline"
				attack_file_path = working_directory + "/traffic_tables/" + get_router_name(src) + "_to_" + get_router_name(dst) + "_attack"
				
				attack_string = str(src_idx) + "\t" + str(dst_idx) + "\t" + str(pir) + "\t"+ str(pir) + "\t1\t1000000\n"

				with open(source_file_path, "r") as source:
					lines = source.readlines()
					with open(attack_file_path, "w") as attack_file:
						attack_file.write(attack_string)
						attack_file.writelines(lines)

				os.system("cp " + source_file_path  + " " + baseline_file_path)
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 2: Call noxim to generate features
				log.write("Process #" + str(ID) + "\tCalling noxim\n")
				print("Process #" + str(ID) + "\tCalling noxim")

				feature_file_path_baseline = working_directory + "/unparsed_features/" + get_router_name(src) + "_to_" + get_router_name(dst) + "_baseline"
				feature_file_path_attack = working_directory + "/unparsed_features/" + get_router_name(src) + "_to_" + get_router_name(dst) + "_attack"

				log_file_path_baseline = working_directory + "/logs/" + get_router_name(src) + "_to_" + get_router_name(dst) + "_baseline"
				log_file_path_attack = working_directory + "/logs/" + get_router_name(src) + "_to_" + get_router_name(dst) + "_attack"
				
				cmd_baseline = "./../noxim -topology MESH -dimx 8 -dimy 8 -traffic table " + baseline_file_path + "  -config ./../../personal_configs/my_config.yaml -power ./../power.yaml -features " + feature_file_path_baseline + " > " + log_file_path_baseline
				cmd_attack = "./../noxim -topology MESH -dimx 8 -dimy 8 -traffic table " + attack_file_path + "  -config ./../../personal_configs/my_config.yaml -power ./../power.yaml -features " + feature_file_path_attack + " > " + log_file_path_attack

				os.system(cmd_baseline)
				os.system(cmd_attack)
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 3.1: Generating path
				log.write("Process #" + str(ID) + "\tGenerating path\n")
				print("Process #" + str(ID) + "\tGenerating path")
				path = generate_path(list(src), list(dst))
				#--------------------------------------------------------------------------------------------------------------------------
				
				# Step 3.2: Parse features
				log.write("Process #" + str(ID) + "\tParsing features\n")
				print("Process #" + str(ID) + "\tParsing features")
				
				router_info_baseline = parse_features(feature_file_path_baseline, path, log, ID)
				router_info_attack = parse_features(feature_file_path_attack, path, log, ID)
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 3.3: Pre process data
				router_info_baseline = pre_process(router_info_baseline, log, ID)
				router_info_attack = pre_process(router_info_attack, log, ID)			
				#--------------------------------------------------------------------------------------------------------------------------
				
				# Step 4.1: Clean and annotate data
				router_info_baseline = annotate_data(router_info_baseline, 1e5, log, ID)	# Since the start cycle is 1e5, all enteries are annotated as unsaturated
				router_info_attack = annotate_data(router_info_attack, -1, log, ID)	# Since the start cycle is -1, all enteries are annotated as saturated
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 4.2: Merging data
				router_info = merge_info(router_info_baseline, router_info_attack, log, ID)
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 5: Write clean and annotated data
				log.write("Process #" + str(ID) + "\tWriting per port feature\n")
				print("Process #" + str(ID) + "\tWriting per port feature")
				for router_port in router_info:
					per_port_features_file_name = working_directory + "/per_port_features/" + get_router_port_name(router_port)
					with open(per_port_features_file_name, "a") as per_port_file:
						lockf(per_port_file, LOCK_EX)	# Acquire a lock
						for entry in router_info[router_port]:
							per_port_file.write(", ".join(map(str, entry)) + "\n")
						lockf(per_port_file, LOCK_UN)	# Release the lock
				#--------------------------------------------------------------------------------------------------------------------------

				# Log completing the job
				log.write("Process #" + str(ID) +"\tCompleted job " + str(job) + "\n")
				print("Process #" + str(ID) +"\tCompleted job " + str(job))
				#--------------------------------------------------------------------------------------------------------------------------
			
			except Empty:
				log.write("Process #" + str(ID) + "\tExiting...\n")
				print("Process #" + str(ID) + "\tExiting...")
				return



"""
Generates a list of input ports to a router
Args:
	router	: The router for which ports are to be generated
Rets:
	ports	: A list of router and ports which are input to the given router. The format is
	[((router_x, router_y), port), ...]
"""
def get_input_ports(router):
	ports = []
	for port in range(5): # Use the input directions: NSEW + Local
		ports.append((router, port))
	return ports

"""
Generates a list of output ports to a router
Args:
	router	: The router for which ports are to be generated
Rets:
	ports	: A list of router and ports which are output to the given router. The format is
	[((router_x, router_y), port), ...]
"""
def get_output_ports(router):
	ports = []
	
	# Start adding ports one by one
	ports.append((router, DIRECTION_PE))	# Add the local PE's input

	# Calculate other directions
	router_port_north = ((router[0], router[1] - 1), DIRECTION_SOUTH)
	router_port_south = ((router[0], router[1] + 1), DIRECTION_NORTH)
	router_port_east = ((router[0] + 1, router[1]), DIRECTION_WEST)
	router_port_west = ((router[0] - 1, router[1]), DIRECTION_EAST)

	# Add the directions
	ports.append(router_port_north)
	ports.append(router_port_south)
	ports.append(router_port_east)
	ports.append(router_port_west)

	return ports

"""
Reads the features of provided ports
Checks if these ports exist
If they exist, their features are add to a common pool
These features are then shuffled
Args:
	ports	: The ports whose data is to be merged. The format is
	[((router_x, router_y), port), ...]
	working_directory	: The directory in which the code generated files
Rets:
	Used port	: A comma seperated string which is a list of ports used. An example is:
	"1_1.2, 1_1.3"
	All data	: This is accumaled data from all ports
"""
def merge_ports(ports, working_directory):
	directory_base_name = working_directory + "/per_port_features/" # This is the path to seach individual port files in

	used_ports = "" # Initialize the list of used ports

	all_data = [] # This is the list of 

	# Accumalate data
	for port in ports: # Iterate over ports
		file_name = get_router_port_name(port)
		file_path = directory_base_name + file_name	# Generate the full name to open the file
		if(os.path.isfile(file_path)):
			used_ports += file_name + ", "
			with open(file_path, 'r') as data_file:
				lines = data_file.readlines()	# Read the data from file
				for line in lines:
					data = list(map(float, (line.split(","))))
					all_data.append(data)	 # Add lines to all data

	# Remove the last comma from used_port string
	if(len(used_ports) > 2):	# Ensure that string isn't empty
		used_ports = used_ports[:-2]

	# Shuffle all the data
	shuffle(all_data)

	return used_ports, all_data



"""
Method called by processes to merge features.
The method does the following:
1.) Finds list of all ports which are input to current router
2.) Merges the features of input ports and shuffles it
3.) Writes to router input features
4.) Finds list of all ports which are output to current router
5.) Merges the features of output ports and shuffles it
6.) Writes to router output features
Args:
	ID					: Process ID
	jobs				: Queue of jobs to be completed
	working_directory	: Directory to store generated files
Rets:
	None
"""
def worker_merge(ID, jobs, working_directory):
	with open(working_directory + "/worker_logs_merge/worker_" + str(ID), "w", buffering = 1) as log:	# Open file for log
		log.write("Process #" + str(ID) + "\tStarting...\n")
		print("Process #" + str(ID) + "\tStarting...")
		
		# Compute till all jobs are done
		while True:
			try:
				job = jobs.get(timeout = 0.1) # Fetch next job
			
				# Log fetching job
				log.write("Process #" + str(ID) + "\tStarting job " + str(job) + "\n")
				print("Process #" + str(ID) + "\tStarting job " + str(job))

				# Step 1: Get list of input ports
				log.write("Process #" + str(ID) + "\tGenerating list of input ports\n")
				print("Process #" + str(ID) + "\tGenerating list of input ports")
				input_ports = get_input_ports(job)
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 2: Merge input port features
				log.write("Process #" + str(ID) + "\tMerging input port features\n")
				print("Process #" + str(ID) + "\tMerging input port features")
				used_ports, merged_inputs = merge_ports(input_ports, working_directory)
				log.write("Process #" + str(ID) + "\tUsed ports: " + used_ports + "\n")
				print("Process #" + str(ID) + "\tUsed ports: " + used_ports)
				#--------------------------------------------------------------------------------------------------------------------------
				
				# Step 3: Write input features
				log.write("Process #" + str(ID) + "\tStoring input port features\n")
				print("Process #" + str(ID) + "\tStoring input port features")
				file_name = get_router_name(job) + "_in"
				full_path_name = working_directory + "/per_router_features/" + file_name
				with open(full_path_name, 'w') as input_features_file:
					for entry in merged_inputs:
						input_features_file.write(", ".join(map(str, entry)) + "\n")
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 4: Get list of output ports
				log.write("Process #" + str(ID) + "\tGenerating list of output ports\n")
				print("Process #" + str(ID) + "\tGenerating list of output ports")
				output_ports = get_output_ports(job)
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 5: Merge output port features
				log.write("Process #" + str(ID) + "\tMerging output port features\n")
				print("Process #" + str(ID) + "\tMerging output port features")
				used_ports, merged_outputs = merge_ports(output_ports, working_directory)
				log.write("Process #" + str(ID) + "\tUsed ports: " + used_ports + "\n")
				print("Process #" + str(ID) + "\tUsed ports: " + used_ports)
				#--------------------------------------------------------------------------------------------------------------------------
				
				# Step 6: Write output features
				log.write("Process #" + str(ID) + "\tStoring output port features\n")
				print("Process #" + str(ID) + "\tStoring output port features")
				file_name = get_router_name(job) + "_out"
				full_path_name = working_directory + "/per_router_features/" + file_name
				with open(full_path_name, 'w') as output_features_file:
					for entry in merged_outputs:
						output_features_file.write(", ".join(map(str, entry)) + "\n")
				#--------------------------------------------------------------------------------------------------------------------------
				
				# Log completing the job
				log.write("Process #" + str(ID) +"\tCompleted job " + str(job) + "\n")
				print("Process #" + str(ID) +"\tCompleted job " + str(job))
				#--------------------------------------------------------------------------------------------------------------------------
			
			except Empty:
				log.write("Process #" + str(ID) + "\tExiting...\n")
				print("Process #" + str(ID) + "\tExiting...")
				return

"""
Method called by processes to meta merge features.
The method iterates over all benchmark's per_router_features and creates meta merge feature files.
Args:
	ID                  : Process ID
	jobs                : Queue of jobs to be completed
	list_of_benchmarks  : List of benchmarks to iterate over
	working_directory   : Directory to store generated files
Rets:
	None
"""
def worker_meta_merge(ID, jobs, list_of_benchmarks, working_directory):
	with open(working_directory + "/worker_logs_meta_merge/worker_" + str(ID), "w", buffering = 1) as log: # Open file for log
		log.write("Process #" + str(ID) + "\tStarting...\n")
		print("Process #" + str(ID) + "\tStarting...")
		
		# Compute till all jobs are done
		while True:
			try:
				job = jobs.get(timeout = 0.1) # Fetch next job

				# Log fetching job
				log.write("Process #" + str(ID) + "\tStarting job " + job + "\n")
				print("Process #" + str(ID) + "\tStarting job " + job)

				merged_file_name = working_directory + "/per_router_features/" + job
				for benchmark in list_of_benchmarks:
					benchmark_feature_file = working_directory + "/" + benchmark + "/per_router_features/" + job
					if(os.path.isfile(benchmark_feature_file)):
						cmd = "cat " + benchmark_feature_file + " >> " + merged_file_name
						os.system(cmd)

				# Log completing the job
				log.write("Process #" + str(ID) +"\tCompleted job " + str(job) + "\n")
				print("Process #" + str(ID) +"\tCompleted job " + str(job))
				#--------------------------------------------------------------------------------------------------------------------------
				
			except Empty:
				log.write("Process #" + str(ID) + "\tExiting...\n")
				print("Process #" + str(ID) + "\tExiting...")
				return


def main():
	dir_base_name = "DoS_noxim_data_router" # set the base name for directory to work within
	if(os.path.exists(dir_base_name)):
		print("Directory exists! Overwriting...")
		os.system("rm -rf " + dir_base_name)
	benchmark_directory = sys.argv[1] # This is the directory which stores all the benchmarks

	jobs = mp.Queue()    # Create a job queue for workers
	list_of_benchmarks = []

	processes = []

	for benchmark in os.listdir(benchmark_directory):
		print("Running generation for", benchmark)
		list_of_benchmarks.append(benchmark)

		# Get the benchmark name
		benchmark_name = benchmark

		# Create a directory for generated files
		print("Generating directory structure...")
		dir_name = dir_base_name + "/" + benchmark_name
		os.system("mkdir -p " + dir_name)
		os.system("cp " + benchmark_directory + "/" + benchmark + " " + dir_name + "/.") # Copy the file to working directory
		os.system("mkdir " + dir_name + "/traffic_tables")		# Traffic tables are stored here. The format is <from>_to_<to>_<attack/baseline>
		os.system("mkdir " + dir_name + "/unparsed_features")	# Raw featues generated by noxim are stored here. The format is same as above
		os.system("mkdir " + dir_name + "/per_port_features")	# Features related to a single router port pair. The format is <router>.<port>
		os.system("mkdir " + dir_name + "/per_router_features")	# Features related to a single router I/O pair. The format is <router>_<in/out>
		os.system("mkdir " + dir_name + "/logs")				# Logs generated by noxim are stored here. The format is same as above
		os.system("mkdir " + dir_name + "/worker_logs_gen")		# Logs generated by workers who create features are stored here. The format is worker_<ID>
		os.system("mkdir " + dir_name + "/worker_logs_merge")	# Logs generated by workers who merge features are stored here. The format is worker_<ID>
		print("Done!")

		print("Working directory is: " + dir_name)

		# Start feature generation step
		print("Starting feature generation")

		# Create files to lock onto later
		print("Creating per port feature files")

		feature_file_names = set()
		# Initially add all ports
		for router_x in range(DIM_X):
			for router_y in range(DIM_Y):
				for port in range(DIRECTIONS):
					feature_file_name = str(router_x) + "_" + str(router_y) + "." + str(port)
					feature_file_names.add(feature_file_name)

		# Remove invalid ports
		for router_x in range(DIM_X):   # Remove north ports from top row
			feature_file_name_to_be_removed = str(router_x) + "_0." + str(DIRECTION_NORTH)
			feature_file_names.remove(feature_file_name_to_be_removed)

		for router_x in range(DIM_X):   # Remove south ports from bottom row
			feature_file_name_to_be_removed = str(router_x) + "_" + str(DIM_Y - 1) + "." + str(DIRECTION_SOUTH)
			feature_file_names.remove(feature_file_name_to_be_removed)

		for router_y in range(DIM_Y):   # Remove east ports from leftmost row
			feature_file_name_to_be_removed = str(DIM_X - 1) + "_" + str(router_y) + "." + str(DIRECTION_EAST)
			feature_file_names.remove(feature_file_name_to_be_removed)

		for router_y in range(DIM_Y):   # Remove west ports from rightmost row
			feature_file_name_to_be_removed = "0_" + str(router_y) + "." + str(DIRECTION_WEST)
			feature_file_names.remove(feature_file_name_to_be_removed)

		for feature_file_name in feature_file_names:
			cmd = "touch " + dir_name + "/per_port_features/" + feature_file_name
			os.system(cmd)

		# Generate jobs
		print("Generating jobs...")
		for router_x in range(DIM_X):
			for router_y in range(DIM_Y):
				# Generate the four pair to simulate attack between
				pairs = []
				pairs.append((0, router_y))			# west pair
				pairs.append((DIM_X - 1, router_y))	# east pair
				pairs.append((router_x, 0))			# north pair
				pairs.append((router_x, DIM_Y - 1))	# south pair

				router = (router_x, router_y)
				for pair in pairs:
					if(router != pair):	# Prevent pairs on edges
						jobs.put((router, pair))
						jobs.put((pair, router))
		print("Done!")

		# Create processes and generate features
		print("Starting processes")
		num_processes = int(sys.argv[2])
		pir = sys.argv[4]
		for ID in range(num_processes):
			process = mp.Process(target = worker_gen, args = (ID, jobs, benchmark_name, dir_name, pir, ))
			process.start()
			processes.append(process)
		
		# Cleanup processes and jobs	
		for process in processes:
			process.join()
		processes.clear()
		print("Done!")

		# Merge port level features to create router level features
		print("Starting merging")

		# Generate jobs
		print("Generating jobs")
		for router_x in range(DIM_X):
			for router_y in range(DIM_Y):
				jobs.put((router_x, router_y))
		print("Done!")

		# Create processes and start merging
		num_processes = int(sys.argv[3])
		for ID in range(num_processes):
			process = mp.Process(target = worker_merge, args = (ID, jobs, dir_name, ))
			process.start()
			processes.append(process)

		# Cleanup processes and jobs
		for process in processes:
			process.join()
		processes.clear()
		print("Done!")

		print("Compressing logs")
		log_dir = dir_name + "/logs"
		compress_cmd = "tar -cf - " + log_dir + " | pv | pigz -9 -p 41  > " + dir_name + "/logs.tar.gz"
		remove_cmd = "rm -rf " + log_dir
		print(compress_cmd)
		os.system(compress_cmd)
		print("Removing uncompressed data")
		print(remove_cmd)
		os.system(remove_cmd)
		print("Done")

	# Meta merge per port features
	print("Meta merging features...")

	print("Generating directory structure")
	os.system("mkdir " + dir_base_name + "/per_router_features")      # Logs generated by workers who create features are stored here. The format is worker_<ID>
	os.system("mkdir " + dir_base_name + "/worker_logs_meta_merge")
	
	# generate jobs for workers
	print("Generating jobs")
	for router_x in range(DIM_X):
		for router_y in range(DIM_Y):
			router = (router_x, router_y)
			jobs.put(get_router_name(router) + "_in")
			jobs.put(get_router_name(router) + "_out")

	# Create processes and meta merge features
	print("Starting processes")
	num_processes = int(sys.argv[3])
	for ID in range(num_processes):
		process = mp.Process(target = worker_meta_merge, args = (ID, jobs, list_of_benchmarks, dir_base_name, ))
		process.start()
		processes.append(process)
	
	# Cleanup processes and jobs  
	for process in processes:
		process.join()
	processes.clear()
	print("Done!")

if __name__ == '__main__':
	main()
