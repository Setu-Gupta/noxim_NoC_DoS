"""
Author	: Setu Gupta
Email	: setu18190@iiitd.ac.in
Date	: 24th Aug 2020

This tool is use to test perceptrons on server to detect congestion in ports.
The tool can be used via the following command
	python3 path/to/this/file path/to/data/directory number_of_helper_gen_processes_to_use
"""

import os									# Used to iterate over directories
import sys									# Used to get command line arguments
import multiprocessing as mp				# Used to parallelize workload
from queue import Empty						# Used for Empty exception
from fcntl import lockf, LOCK_EX, LOCK_UN	# Used to lock files


# Dimensions of grid. It's used to calculate index of router
DIM_X = 8
DIM_Y = 8
# Note that the grid has origin at the top left corner and the coordinates increase in bottom right direction



"""
Tells whether the perceptron was activated or not
Args:
	bias	: Bias
	weights	: Weight Vector
	vector	: Input to percepton
"""
def predict(bias, weights, vector):
	used_idx = [0,1,4] # Use only buffer status, cycles since last flit and buffer waiting time

	activation = bias

	assert(len(vector) == len(weights))
	# for idx in range(len(weights)):	# Take inner product
	for idx in used_idx:	# Take inner product
		activation += weights[idx] * vector[idx]

	return 1.0 if activation >= 0.0 else 0.0



# Define threshold for floating point comparision
FLOAT_COMPARE_ZERO = 0.0001
"""
Gives the accuracy by running the test cases.
Args:	
	weights_and_bias	: (bias, weight1, ..., weight5)
	path				: Path of feature file
Rets:
	accuracy			: Accuracy achieved
	false_positive		: False positive in %
	false_negative		: False negative in %	
"""
def get_accuracy(weights_and_bias, path):
	
	# Initialize variables to keep track of correct results
	correct = 0
	total = 0

	# Calculate false positives and negatives
	false_positives = 0
	false_negatives = 0

	bias = weights_and_bias[0]
	weights = weights_and_bias[1:]

	# Iterate over every test case
	for line in open(path):
		data_str = line.split(",")
		data = [float(d) for d in data_str]	 # Convert to float
		
		parsed_features = data[1:-1]
		annotation = data[-1]

		total += 1
		prediction = predict(bias, weights, parsed_features) # Predict based on current weights and bias
		if(abs(prediction - annotation) < FLOAT_COMPARE_ZERO):
			correct += 1
		else:
			if(prediction > annotation):
				false_positives += 1
			else:
				false_negatives += 1

	# Calculate accuracy and false +ve, -ve and return it
	if(total == 0):
		return 0, 0, 0

	accuracy = (correct * 100) / total
	false_positives = (false_positives * 100) / total
	false_negatives = (false_negatives * 100) / total

	return accuracy, false_positives, false_negatives



"""
Worker to run tests and calculate accuracy
Args:
	ID						: ID of the worker
	jobs					: Queue of jobs
		This has elements like "0_0_in"
	benchmark_path			: Path of benchmark directory
	accuracy_report_file	: Path of file to write detailed accuracy
	weights_dict			: Dict of weights and bias
	benchmark_accuracy		: Shared dictionary to store accuracy
	lock					: Lock to access becnhmark_accuracy
Rets:
	None
"""
def worker_test(ID, jobs, benchmark_path, accuracy_report_file, weights_dict, benchmark_accuracy, lock):
	print("Process #" + str(ID) + "\tStarting...")

	# Continue till all jobs are done
	while True:
		try:
			job = jobs.get(timeout = 0.1) # Fetch next job

			# Log fetching job
			print("Process #" + str(ID) + "\tStarting job " + str(job))

			wb = weights_dict[job]
			router_feature_file_path = benchmark_path + "/per_router_features/" + job
			accuracy, false_positives, false_negatives = get_accuracy(wb, router_feature_file_path)

			string_to_write = job + "\t:\t" + str(accuracy) + ", " + str(false_positives) + ", " + str(false_negatives) + "\n"

			with lock:
				benchmark_accuracy[job] = (accuracy, false_positives, false_negatives)
				with open(accuracy_report_file, "a") as arf:
					arf.write(string_to_write)

			# Log finishing job
			print("Process #" + str(ID) + "\tCompleted job " + str(job))
	
		except Empty:
			print("Process #" + str(ID) + "\tExiting...")
			return


def main():

	base_dir = "./feature_tester"
	if(os.path.exists(base_dir)):
		print("Directory exists! Overwriting...")
		os.system("rm -rf " + base_dir)
	os.system("mkdir " + base_dir)

	# Step 1: Get list of benchmarks
	root_directory = sys.argv[1] # Get the directory to work with

	list_of_benchmarks = []

	for benchmark in os.listdir(root_directory):	# Iterate over all benchmarks
		benchmark_path = root_directory + "/" + benchmark # Get the full relative path
		if (not os.path.isfile(benchmark_path)):
			if benchmark == "per_router_features":	# Skip code generated files
				continue
			if benchmark == "worker_logs_train":
				continue
			if benchmark == "worker_logs_meta_merge":
				continue
			list_of_benchmarks.append(benchmark)

	# Step 2: Extract weights from report
	manager = mp.Manager()
	weights_file = root_directory + "/weights"
	weights_dict = manager.dict()
	for line in open(weights_file):
		parsed_data_str = line.split(",")
		parsed_data = [float(p) for p in parsed_data_str]	# Convert to float

		# Generate name of the router file for this weights set
		router_name = ""
		router_x = str(int(parsed_data[0]) % DIM_Y)
		router_y = str(int(parsed_data[0]) // DIM_Y)
		router_name += router_x + "_" + router_y + "_"
		router_name += "in" if int(parsed_data[1]) == 1 else "out"

		bw = parsed_data[2:]	# Weights and biases
		weights_dict[router_name] = bw
	
	# Step 3: Iterate over benchmarks and test 
	jobs = mp.Queue()

	for benchmark in list_of_benchmarks:

		print("Running benchmark: ", benchmark)

		benchmark_accuracy = manager.dict()   # A dict to store individual accuracies
		lock = mp.Lock() # A lock to synchronize access to bench_mark_accuracy dict

		benchmark_path = root_directory + "/" + benchmark
		accuracy_report_file = base_dir + "/" + benchmark + "_report"

		os.system("touch " + accuracy_report_file)	# Create report file

		router_feature_file_path = benchmark_path + "/per_router_features"
		print(router_feature_file_path)
		for file in weights_dict:
			jobs.put(file)

		# Create processes and get accuracy
		processes = []
		print("Starting processes")
		num_processes = int(sys.argv[2])
		for ID in range(num_processes):
			process = mp.Process(target = worker_test, args = (ID, jobs, benchmark_path, accuracy_report_file, weights_dict, benchmark_accuracy, lock, ))
			process.start()
			processes.append(process)
		
		# Cleanup processes and jobs	
		for process in processes:
			process.join()
		processes.clear()
		print("Done!")

		# Get net accuracy and store to accuracy file
		print("Calculating net accuracy")
		total_jobs = 0
		accuracy_net = 0
		false_positives_net = 0
		false_negatives_net = 0
		for job in benchmark_accuracy:
			total_jobs += 1
			accuracy_net += benchmark_accuracy[job][0]
			false_positives_net += benchmark_accuracy[job][1]
			false_negatives_net += benchmark_accuracy[job][2]
		if(total_jobs != 0):
			accuracy_net = accuracy_net / total_jobs
			false_positives_net = false_positives_net / total_jobs
			false_negatives_net = false_negatives_net / total_jobs
		print("Accuracy achieved is: " + str(accuracy_net) + "%")
		print("False positives: " + str(false_positives_net) + "%")
		print("False negatives: " + str(false_negatives_net) + "%")

		string_to_write = "\nNet:\t" + str(accuracy_net) + ", " + str(false_positives_net) + ", " + str(false_negatives_net) + "\n"	# Data to write to report file
		with open(accuracy_report_file, "a") as arf:
			arf.write(string_to_write)

		print("Done!")



if __name__ == '__main__':
	main()