"""
Author	: Setu Gupta
Email	: setu18190@iiitd.ac.in
Date	: 24th Aug 2020

This tool is used generate a CSV file from accuracy_report.
The tool can be used via the following command
	python3 path/to/this/accuracy_report
"""

"""
NOTE: accuracvy_setup format
router_id, port (refer DIRECTIONS below), operation (1 if AND and 0 if OR)
"""

import os	# Used to check if file exists
import sys	# Used to read arguments

DIM_X = 8
DIM_Y = 8

# Definitions for directions
DIRECTIONS 		= 6
DIRECTION_NORTH = 0
DIRECTION_EAST  = 1
DIRECTION_SOUTH = 2
DIRECTION_WEST  = 3
DIRECTION_LOCAL = 4
DIRECTION_PE	= 5

"""
Calculates the neighbouring and port
Args:
	router_port	: ((router_x, router_y), port) of the input side
Rets
	((router_x, router_y), port) for output side
"""
def get_neighbour(router_port):
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



"""
Given a router and port, this gives the router and direction for input side
Args:
	router_port	: ((router_x, router_y), port)
Rets:
	(router_x, router_y, direction)
"""
def get_input_side(router_port):
	input_side = (router_port[0][0], router_port[0][1], 1)	# 1 stands for input
	return input_side


"""
Given a router and port, this gives the router and direction for output side
Args:
	router_port	: ((router_x, router_y), port)
Rets:
	(router_x, router_y, direction)
"""
def get_output_side(router_port):
	neighbour = get_neighbour(router_port)
	output_side = (neighbour[0][0], neighbour[0][1], 0)	# 0 stands for input
	return output_side



"""
Parses accuracy report and stores data in a dictionary
Args: None
Rets:
	{(router_x, router_y, direction), (false +ve, false -ve)}
	Where:
		direction	: input or output
		false +ve	: No of false +ve's encountered, normalized between 0 and 1
		false -ve	: No of false +ve's encountered, normalized between 0 and 1
"""
def get_accuracy_data():
	parsed_data = {}

	# Read from accuracy report
	for line in open(sys.argv[1]):
		data = []
		data.append(line.split(":")[0])
		data.extend(line.split(":")[1].split(","))

		router_x = int(data[0].split('_')[0])
		router_y = int(data[0].split('_')[1])

		direction = 1 if data[0].split('_')[2].find("in") else 0

		key = (router_x, router_y, direction)
		accuracy_values = (float(data[-2])/100, float(data[-1])/100)

		parsed_data[key] = accuracy_values

	return parsed_data



ALPHA = 0.5	# Relative number of samples which were positive (Ground truth)
"""
Calculated opertion depending on false +ve and -ve
Args:	
	a	: False +ve 1
	b	: False -ve 1
	c	: False +ve 2
	d	: False -ve 2
Rets:
	True or False
	True is AND is better
"""
def compute_choice(a, b, c, d):
	value = (a-b+c-d) + ((2*b*d)/(ALPHA*(1-ALPHA))) - ((2*((a*c)+(b*d)))/(1-ALPHA))
	return value > 0.0



"""
Calculates choice of operation
Args:
	parsed data	: False +ve and -ve data. Format is: {(router_x, router_y, direction), (false +ve, false -ve)}
Rets:
	Choice:
		[[router_id, port, operation]]	The router_id and port are of the input side
		operations is 1 if and and 0 if or
"""
def get_choice(parsed_data):

	choices = []

	for x in range(DIM_X):
		for y in range(DIM_Y):
			for port in range(DIRECTIONS):
				cur_choice = []

				if(port == DIRECTION_LOCAL or port == DIRECTION_PE):	# In case of loacl ports, we only consult ourselves. So opertion doesn't matter
					cur_choice = [x, y, 1]
					continue

				# Find the input and output side of this router
				cur_rp = ((x, y), port)
				ip = get_input_side(cur_rp)
				op = get_output_side(cur_rp)

				# Handle boundary of mesh network
				if(ip[0] < 0 or ip[0] >= DIM_X):
					continue
				if(ip[1] < 0 or ip[1] >= DIM_Y):
					continue
				if(op[0] < 0 or op[0] >= DIM_X):
					continue
				if(op[1] < 0 or op[1] >= DIM_Y):
					continue

				try:
					a = parsed_data[ip][0]
					b = parsed_data[ip][1]
					c = parsed_data[op][0]
					d = parsed_data[op][1]
				except KeyError:
					continue

				choice = 1 if compute_choice(a, b, c, d) else 0
				
				router_id = x + y*DIM_Y

				cur_choice = [router_id, port, choice]
				choices.append(cur_choice)

	return choices



def main():
	OUTPUT_FILE = "accuracy_setup"
	if(os.path.exists(OUTPUT_FILE)):
		os.system("rm -f " + OUTPUT_FILE)
		print("Overwriting...")

	parsed_data = get_accuracy_data()
	choices = get_choice(parsed_data)

	for c in choices:
		with open(OUTPUT_FILE, 'a') as of:
			of.write(", ".join(list(map(str, c))) + "\n")

if __name__ == '__main__':
	main()