"""
Author	: Setu Gupta
Email	: setu18190@iiitd.ac.in
Date	: 24th Aug 2020

This tool is used compare accuracies of probability model and simple perceptrons.
The tool can be used via the following command
	python3 path/to/this/file path/to/the/accuracy_report
Note: accuracy_report is in DoS_noxim_router_meta_merge_xxx
The tool propmpts user to input the source and destination pairs of router.
It then calculates and prints the localization probabilty using
	1.) Only input ports
	2.) Only output ports
	3.) Using probability model
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
Args:
	report_path		: Path to accuracy_report
Rets:
	{(router_x, router_y, direction), (false +ve, false -ve)}
	Where:
		direction	: input or output
		false +ve	: No of false +ve's encountered, normalized between 0 and 1
		false -ve	: No of false +ve's encountered, normalized between 0 and 1
"""
def get_accuracy_data(report_path):
	parsed_data = {}

	# Read from accuracy report
	for line in open(report_path):
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
Calculates the probability of correctly predicting hop from src to dst depending on false +ve and -ve
Args:	
	a	: False +ve src
	b	: False -ve src
	c	: False +ve dst
	d	: False -ve dst
Rets:
	probability of hopping
"""
def compute_choice_probabilty(a, b, c, d):
	p_and =	(ALPHA)*((1-(b/ALPHA))*(1-(d/ALPHA))) + (1-ALPHA)*(1-(a/(1-ALPHA))*(c/(1-ALPHA)))
	p_or = (ALPHA)*(1-(b/ALPHA)*(d/ALPHA)) + (1-ALPHA)*((1-(a/(1-ALPHA)))*(1-(c/(1-ALPHA))))
	# print(p_or,p_and)
	return max(p_and, p_or)

"""
Calculates the probability of localization if it starts from src and the attacker is dst
Args:
False +ve and -ve data. 
	parsed_data : Format is: {(router_x, router_y, direction), (false +ve, false -ve)} (direction = 1 if input)
	src			: Triggering node
	dst			: Attacker node
Rets:
	(a, b, c) where
		a	: P(localization using input ports)
		b	: P(localization using output ports)
		c	: P(localization using probability model)
"""
def localization_prob(parsed_data, src, dst):

	if(src == dst):	# Base case. Reached destination
		return (1, 1, 1)

	# Calcuate hop direction
	used_dir = -1	# Going to (next_hop_x, next_hop_y) from src using used_dir

	# Routing is XY. So the backtracking is YX
	if(dst[1] > src[1]):	# Move South
		used_dir = DIRECTION_SOUTH
	elif(dst[1] < src[1]):	# Move North
		used_dir = DIRECTION_NORTH
	elif(dst[1] == src[1]):	# Now route in x direction
		if(dst[0] > src[0]):	# Move East
			used_dir = DIRECTION_EAST
		elif(dst[0] < src[0]):	# Move West
			used_dir = DIRECTION_WEST

	cur_router_port = ((src[0], src[1]), used_dir)
	next_router_port = get_neighbour(cur_router_port)
	
	# Input port based
	key_in = (next_router_port[0][0], next_router_port[0][1], 1)
	a = 1 - sum(parsed_data[key_in])

	# Output port based
	key_out = (cur_router_port[0][0], cur_router_port[0][1], 0)
	b = 1 - sum(parsed_data[key_out])

	# Probability model based
	fp_cur = parsed_data[key_in][0]
	fn_cur = parsed_data[key_in][1]
	fp_next = parsed_data[key_out][0]
	fn_next = parsed_data[key_out][1]
	c = compute_choice_probabilty(fp_cur, fn_cur, fp_next, fn_next)

	next_src = (next_router_port[0][0], next_router_port[0][1])
	next_prob = localization_prob(parsed_data, next_src, dst)

	a *= next_prob[0]
	b *= next_prob[1]
	c *= next_prob[2]

	prob = (a,b,c)
	# print(src, "->", dst, ":" ,prob)
	return prob

def get_max_improvement(parsed_data, trip):
	res = []
	for i in range(63):
		for j in range(63):
			src = (i%DIM_Y, i//DIM_Y)
			dst = (j%DIM_Y, j//DIM_Y)

			(ip, op, prob) = localization_prob(parsed_data, src, dst)
			raw = (ip, op, prob)
			rel_prob = ip
			rel = (ip/rel_prob, op/rel_prob, prob/rel_prob)

			res.append((src, dst, raw, rel))

	res.sort(key = lambda x:x[3][-1], reverse = True)

	if(trip == -1):
		return res
	return res[:trip]

def main():
	accuracy_report_path = sys.argv[1]
	parsed_data = get_accuracy_data(accuracy_report_path)
	# src = tuple(map(int,input("Enter src: ").split()))
	# dst = tuple(map(int,input("Enter dst: ").split()))
	# p_localization = localization_prob(parsed_data, src, dst)
	# print(p_localization)
	print_max_improvement(parsed_data, 20)

if __name__ == '__main__':
	main()