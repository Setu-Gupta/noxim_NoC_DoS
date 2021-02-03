"""
Author	: Setu Gupta
Email	: setu18190@iitd.ac.in
Date	: 3rd Feb 2021

This tool is used to run multiple variants of benchmarks with different PIR values.
The tool can be used via the following command
	python3 path/to/this/file path/to/benchmark/directory number_of_helper_threads
NOTE: This tool searches for noxim executable via the following path: ./../noxim
"""

import sys									# Used to read arguments
import os									# Used to run external commands
import multiprocessing as mp				# Used to parallelize workload
from queue import Empty						# Used for Empty exception

PIRs = [0.01] + [i/10 for i in range(1,11)]	# PIRs to test on
SRC = 48
DST = 7

# Dimensions of grid. It's used to calculate index of router
DIM_X = 8
DIM_Y = 8

def worker_gen(ID, jobs, root_directory):
	with open(root_directory + "/worker_logs_gen/worker_" + str(ID), "w", buffering = 1) as log:	# Open file for log
		log.write("Process #" + str(ID) + "\tStarting...\n")
		print("Process #" + str(ID) + "\tStarting...")
		
		# Compute till all jobs are done
		while True:
			try:
				job = jobs.get(timeout = 0.1) # Fetch next job

				# Log fetching job
				log.write("Process #" + str(ID) + "\tStarting job " + str(job) + "\n")
				print("Process #" + str(ID) + "\tStarting job " + str(job))
				
				# Fetch benchmark and pir
				benchmark_name = job[0]
				pir = job[1]
				#--------------------------------------------------------------------------------------------------------------------------

				# Step 1: Create traffic tables
				log.write("Process #" + str(ID) + "\tWriting traffic tables\n")
				print("Process #" + str(ID) + "\tWriting traffic tables")
				
				working_directory = root_directory + "/" + benchmark_name
				source_file_path = working_directory + "/" + benchmark_name
				baseline_file_path = working_directory + "/traffic_tables/" + str(pir) + "_baseline"
				attack_file_path = working_directory + "/traffic_tables/" + str(pir) + "_attack"
				
				attack_string = str(SRC) + "\t" + str(DST) + "\t" + str(pir) + "\t" + str(pir) + "\t1\t1000000\n"

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

				log_file_path_baseline = working_directory + "/logs/" + str(pir) + "_baseline"
				log_file_path_attack = working_directory + "/logs" + str(pir) + "_attack"
				
				cmd_baseline = "./../noxim -topology MESH -dimx " + str(DIM_X) + " -dimy " + str(DIM_Y) + " -traffic table " + baseline_file_path + "  -config ./../../personal_configs/my_config.yaml -power ./../power.yaml > " + log_file_path_baseline
				cmd_attack = "./../noxim -topology MESH -dimx " + str(DIM_X) + " -dimy " + str(DIM_Y) + " -traffic table " + attack_file_path + "  -config ./../../personal_configs/my_config.yaml -power ./../power.yaml > " + log_file_path_attack

				os.system(cmd_baseline)
				os.system(cmd_attack)
				#--------------------------------------------------------------------------------------------------------------------------

				# Log completing the job
				log.write("Process #" + str(ID) +"\tCompleted job " + str(job) + "\n")
				print("Process #" + str(ID) +"\tCompleted job " + str(job))
				#--------------------------------------------------------------------------------------------------------------------------
			
			except Empty:
				log.write("Process #" + str(ID) + "\tExiting...\n")
				print("Process #" + str(ID) + "\tExiting...")
				return

def main():
	dir_base_name = "DoS_noxim_degradation_run" # set the base name for directory to work within
	if(os.path.exists(dir_base_name)):
		print("Directory exists! Overwriting...")
		os.system("rm -rf " + dir_base_name)
	os.system("mkdir -p " + dir_base_name + "/worker_logs_gen")
	benchmark_directory = sys.argv[1] # This is the directory which stores all the benchmarks

	jobs = mp.Queue()    # Create a job queue for workers
	list_of_benchmarks = []

	processes = []

	for benchmark in os.listdir(benchmark_directory):
		print("Found benchmark:", benchmark)
		list_of_benchmarks.append(benchmark)

		# Get the benchmark name
		benchmark_name = benchmark

		# Create a directory for generated files
		print("Generating directory structure...")
		dir_name = dir_base_name + "/" + benchmark_name
		os.system("mkdir -p " + dir_name)
		os.system("cp " + benchmark_directory + "/" + benchmark + " " + dir_name + "/.") # Copy the file to working directory
		os.system("mkdir " + dir_name + "/traffic_tables")		# Traffic tables are stored here. The format is <pir>_<attack/baseline>
		os.system("mkdir " + dir_name + "/logs")				# Logs generated by noxim are stored here. The format is same as above
		print("Done!")

	# Start feature generation step
	print("Starting generation")

	# Generate jobs
	print("Generating jobs...")
	for b in list_of_benchmarks:
		for p in PIRs:
			jobs.put((b, p))
	print("Done!")

	# Create processes and generate features
	print("Starting processes")
	num_processes = int(sys.argv[2])
	for ID in range(num_processes):
		process = mp.Process(target = worker_gen, args = (ID, jobs, dir_base_name, ))
		process.start()
		processes.append(process)
	
	# Cleanup processes and jobs	
	for process in processes:
		process.join()
	processes.clear()
	print("Done!")

if __name__ == '__main__':
	main()