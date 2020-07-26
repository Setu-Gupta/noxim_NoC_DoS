"""
Author	: Setu Gupta
Email	: setu18190@iiitd.ac.in
Date	: 25th July 2020

This tool is use to train and test perceptrons to detect congestion in ports.
This uses the updated feature file format which has features for both Rx and Tx of local PE
The tool can be used via the following command
	python3 path/to/this/file path/to/features/unsaturated/file path/to/features/saturated/file
"""
import sys						# Used to read sys args
from copy import deepcopy as cp	# Used to copy arrays
from random import shuffle 		# Used to mix data around
import os						# Used to remove training_report file

# Definitions for directions
DIRECTIONS 		= 6
DIRECTION_NORTH = 0
DIRECTION_EAST  = 1
DIRECTION_SOUTH = 2
DIRECTION_WEST  = 3
DIRECTION_LOCAL = 4
DIRECTION_PE	= 5

# Dimensions of grid. It's used to calculate index of router
DIM_X = 8
DIM_Y = 8
# Note that the grid has origin at the top left corner and the coordinates increase in bottom right direction

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
def parse_features(feature_file, router_and_ports):
	all_info = {}	# This dictionary stores the parsed data

	# Read data from csv file
	print("Reading from file :", feature_file)
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
	print("Done!")

	# Generate output dictionary
	print("Generating router_info")
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
	print("Done!")
	return router_info



# Length of moving average window
AVG_CYCLES = 5
ENABLE_AVG_WINDOW = True
"""
Modifies the data in router info.
Currently configured to take a moving window average on various parameters. The size of window is AVG_CYCLES
Args:
	router_info	: Input data (Not preserved)
Rets:
	router_info	: Output data
The input and output formats are
	{((router_x, router_Y), port)	:	[[cycle, buffer_status, cycles_since_last_flit, stalled_flits, transmitted flits, buffer_waiting_time], ...], ...}
"""
def pre_process(router_info):
	print("Preprocessing data...")
	if(not ENABLE_AVG_WINDOW):	# Return without doing anything if not enabled
		print("Done!")
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
	print("Taking moving average of size", AVG_CYCLES)
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
	
	print("Done!")
	return router_info



# Define saturation levels
SATURATED = 1.0
UNSATURATED = 0.0
"""
Annotates the data in the following way:
	All the data points after start_cycle are labeled as SATURATED
	The rouuter_info taken as input is returned with the addition of annotation
Args:	
	router_info: router data (Not preserved)
	start_cycle	: Cycle after which the router and ports are considered SATURATED
Rets:
	router_info_annotated	: router_info with annotations with the following format
	{((router_x, router_Y), port)	:	[[cycle, buffer_status, cycles_since_last_flit, stalled_flits, transmitted flits, buffer_waiting_time, ANNOTATION], ...], ...}

"""
def annotate_data(router_info, start_cycle):
	print("Annotating data...")
	for router_port in router_info: # Iterate over all ports
		for entry_idx in range(len(router_info[router_port])):
			if(router_info[router_port][entry_idx][PARSED_CYCLE] >= start_cycle):	# Check if the cycle for current entry exceeds start_cycle and annotate accordingly
				router_info[router_port][entry_idx].append(SATURATED)
			else:
				router_info[router_port][entry_idx].append(UNSATURATED)
	print("Done!")
	return router_info


"""
Merges two data sets of tyoe router_info
Args:
	set_1, set_2	: Datasets to be merged
Rets:
	merged	: Merged dataset
"""
def merge_info(set_1, set_2):
	print("Merging....")
	merged = {}
	for router_port in set_1:
		merged[router_port] = cp(set_1[router_port])	# Add enteries from set 1
		merged[router_port].extend(cp(set_2[router_port]))	# Add enteries from set 2

	print("Done!")
	return merged


# Define training ratio
TRAINING_RATIO = 0.7
"""
Splits the incoming data into testing and training after shuffling it
Args:
	current_info	: Data regarding a particular router and port. It's of the format
	[[cycle, buffer_status, cycles_since_last_flit, stalled_flits, transmitted flits, buffer_waiting_time, ANNOTATION], ...]
Rets:
	test	: Testing part of data
	train	: Training part of data
	The format for both is same as input
"""
def test_train_splitter(current_info):
	# Split the data into satured and unsatured to ensure better mixing
	# Initialize both sets	
	saturated = [] 
	unsaturated = []

	# Add data to saturated and unsatured sets
	for info in current_info:
		if(info[PARSED_ANNOTATION] == SATURATED):
			saturated.append(cp(info))
		else:
			unsaturated.append(cp(info))

	# Make test and train sets
	test = []
	train = []

	# Add saturated datapoints
	split_index = int(TRAINING_RATIO * len(saturated))
	train += saturated[:split_index]
	test += saturated[split_index:]

	# Add unsaturated datapoints
	split_index = int(TRAINING_RATIO * len(unsaturated))
	train += unsaturated[:split_index]
	test += unsaturated[split_index:]	

	# Shuffle the test and train sets
	shuffle(test)
	shuffle(train)

	return test, train


"""
Tells whether the perceptron was activated or not
Args:
	bias	: Bias
	weights	: Weight Vector
	vector	: Input to percepton
"""
def predict(bias, weights, vector):
	activation = bias

	assert(len(vector) == len(weights))
	for idx in range(len(weights)):	# Take inner product
		activation += weights[idx] * vector[idx]

	return 1.0 if activation >= 0.0 else 0.0



# Learning parameters
EPOCHS = 5000
LEARNING_RATE = 0.00005
"""
Learns the weights for percepton
Args:
	train	: Training dataset
Rets:
	bias	: Learnt bias
	weights	: Learnt weights
"""
def train_weights(train):
	bias = 0.0
	weights = [0] * PARSED_FEATURE_COUNT
	for epoch in range(EPOCHS):	# Iterate over all epochs
		print("Running epoch:", epoch + 1, "out of", EPOCHS, end = "")
		shuffle(train)	# Shuffle dataset on each pass
		sq_error = 0.0
		for data_point in train:
			data_features = data_point[1:-1]	# Ignore the annotation and cycle count
			prediction = predict(bias, weights, data_features) # Predict based on current weights and bias
			error = data_point[-1] - prediction	# Get error
			sq_error += error ** 2	# Update squared error
			bias += LEARNING_RATE * error # Update bias
			for w_idx in range(len(weights)):	# Update weights
				weights[w_idx] += LEARNING_RATE * error * data_features[w_idx]
			# print(bias, weights)
		print(" Error:", sq_error, '\t\t\t\t\t', end = "\r")
	print()
	return bias, weights



# Define threshold for floating point comparision
FLOAT_COMPARE_ZERO = 0.0001
"""
Tests the trained weights and biases and spits out accuracy
Args:
	test	: The testing dataset
	weights	: The learnt weights
	bias 	: The learnt bias
Rets:
	Accuracy	: A value between 0 and 1000 describing the accuracy of the model
"""
def test_weights(test, weights, bias):
	# Initialize variables to keep track of correct results
	correct = 0
	total = 0

	# Start testing
	for data_point in test:
		total += 1
		data_features = data_point[1:-1] # Ignore the annotation and cycle count
		prediction = predict(bias, weights, data_features) # Predict based on current weights and bias
		if(abs(prediction - data_point[-1]) < FLOAT_COMPARE_ZERO):
			correct += 1

	# Calculate accuracy and return it
	accuracy = (correct * 100) / total
	return accuracy 




# Export data or not
EXPORT_PARAMETERS_AND_ACCURACY = True
"""
Trains a perceptron according to data and spits out accuracy
Args:
	test			: Testing dataset
	train			: Training dataset
	router_port		: Router and port for which the training and testing is to be done. The format is ((router_x, router_y), port)
	training_report	: Name of file to write learnt weights
Rets:
	accuracy	: A value between 0 and 100 indicating percentage accuracy
"""
def train_and_test(test, train, router_port, training_report):
	# Setup data structure to store learnt bias and weights
	weights_and_biases = []

	# Save router_id and port
	router_id = router_port[0][1] * DIM_Y + router_port[0][0]
	port = router_port[1]
	weights_and_biases.append(router_id)
	weights_and_biases.append(port)

	# Get learnt bias and weights
	bias, weights = train_weights(train)

	# Store weight and biases
	weights_and_biases.append(bias)
	weights_and_biases.extend(weights)
	
	# Get the accuracy acheived
	accuracy = test_weights(test, weights, bias)

	# Store the accuracy
	weights_and_biases.append(accuracy)

	# Export data to text file
	if(EXPORT_PARAMETERS_AND_ACCURACY):
		with open(training_report, 'a') as report:
			report.write(", ".join([str(x) for x in weights_and_biases]) + '\n')

	return accuracy



"""
Runs the experiment and spits out average accuracy
Args:
	router_info	: Data to run experiment on
Rets:
	accuracy		: Average accuracy across all runs
	training_report	: File to write learnt weights to
"""
def run_experiment(router_info, training_report):
	# Initialize variables to calculate accuracy for the experiment.
	net_accuracy = 0 # Accumalate the accuracy of each individual run in this variable
	total_runs = 0	# Tracks the number of runs done
	
	# Variables to track progress
	total_runs_to_be_done = len(router_info)
	
	if(os.path.exists(training_report)):
		os.remove(training_report)	# Remove training report if it already exists

	# Train and test
	for router_port in router_info: # Run training and testing for each router and port
		total_runs += 1
		print("Running for", router_port, str(total_runs) + "/" + str(total_runs_to_be_done))
		test, train = test_train_splitter(router_info[router_port])
		cur_accuracy = train_and_test(test, train, router_port, training_report)
		print("Accuracy acheived:", str(cur_accuracy) + "%" )
		net_accuracy += cur_accuracy

	accuracy = net_accuracy / total_runs	# Calculate average accuracy
	return accuracy



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
Prompts user for annotation data
Args: None
Rets:
	router_1	: First router in transpose attack
	router_2	: Second router in transpose attack
"""
def get_annotation_data():
	print("Enter annotation data:")
	print("Router #1 : ", end = "")
	router_1 = list(map(int, input().split()))
	print("Router #2 : ", end = "")
	router_2 = list(map(int, input().split()))
	print("Done!")
	return router_1, router_2



def main():
	router_1, router_2 = get_annotation_data()
	path = generate_path(router_1, router_2)
	
	# Parse data
	router_info_normal = parse_features(sys.argv[1], path)
	router_info_attack = parse_features(sys.argv[2], path)
	
	# Pre-process data
	router_info_normal = pre_process(router_info_normal)
	router_info_attack = pre_process(router_info_attack)

	# Annotate data
	router_info_normal = annotate_data(router_info_normal, 1e5)	# Since the start cycle is 1e5, all enteries are annotated as unsaturated
	router_info_attack = annotate_data(router_info_attack, -1)	# Since the start cycle is -1, all enteries are annotated as saturated

	# Merge data and run experiment
	router_info = merge_info(router_info_normal, router_info_attack)
	accuracy = run_experiment(router_info, sys.argv[3])
	print("total accuracy is:", str(accuracy) + "%")


if __name__ == '__main__':
	main()