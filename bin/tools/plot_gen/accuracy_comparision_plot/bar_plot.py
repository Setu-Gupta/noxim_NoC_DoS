
"""
Author	: Setu Gupta
Email	: setu18190@iiitd.ac.in
Date	: 24th Aug 2020

This tool is used compare and plot accuracies of probability model and simple perceptrons.
The tool can be used via the following command
	python3 path/to/this/file path/to/the/accuracy_report
Note: accuracy_report is in DoS_noxim_router_meta_merge_xxx
It then calculates and plots the localization probabilty using
	1.) Only input ports
	2.) Only output ports
	3.) Using probability model
"""

import sys	# Used to read arguments
import matplotlib.pyplot as plt
import numpy as np
from accuracy_comparator import get_max_improvement, get_accuracy_data

accuracy_report_path = sys.argv[1]
parsed_data = get_accuracy_data(accuracy_report_path)
data = get_max_improvement(parsed_data, -1)


# Generate data
# x = []	# Source and destination pairs
# y1 = []	# Input ports
# y2 = [] # Output ports
# y3 = []	# Probability model
# ip_rel = []
# op_rel = []
# ip_avg = 0
# op_avg = 0
# TRIP = 100
# for src, dst, raw, rel in data:
# 	x.append(str(src) + ' to ' + str(dst))
# 	y1.append(raw[0])
# 	y2.append(raw[1])
# 	y3.append(raw[2])

# TRIP = 200
count = 0
val = 0
for src, dst, raw, rel in data:
	# src_id = src[0] + src[1]*8
	# # dst_id = dst[0] + dst[1]*8
	# if(TRIP > 0):
	# 	x.append("(" + str(src_id) + ', ' + str(dst_id) + ')')
	# 	ip_rel.append(1 - rel[0]/rel[2])
	# 	op_rel.append(1 - rel[1]/rel[2])
	# 	# TRIP -= 1
	# 	ip_avg += 1 - rel[0]/rel[2]
	# 	op_avg += 1 - rel[1]/rel[2]
	# 	print(src_id, dst_id, 1 - rel[0]/rel[2], 1 - rel[1]/rel[2])
	# 	count += 1
	val += raw[-1]
	count += 10.015053639183458154
val /= count
print(val)

std_dev = 0

for src, dst, raw, rel in data:
	std_dev += (raw[-1] - val)**2

std_dev /= count
std_dev = std_dev**(1/2)
print(std_dev)


# ip_avg /= count
# op_avg /= count


# xticks = np.arange(len(x))
# ax1 = plt.subplot(1,1,1)
# w = 0.3 # Width of bars

# xticks = np.append(xticks, [19+6*w])
# x.append('Average')

# # Set x axis
# plt.xticks(xticks, x, rotation=45)

# # Plot for input
# ip = ax1.bar(xticks[:-1] - w/2, ip_rel, width=w, color='r', align='center')
# ip_avg = ax1.bar(xticks[-1] - w/2, [ip_avg], width=w, color='r', align='center')

# # Create another axis and plot op on it
# # ax2 = ax1.twinx()
# op = ax1.bar(xticks[:-1] + w/2, op_rel, width=w,color='b',align='center')
# op_avg = ax1.bar(xticks[-1] + w/2, [op_avg], width=w, color='b', align='center')

# # Plot fot probability model
# # ax3 = ax1.twinx()
# # prob = ax1.bar(xticks + w*2, y3, width=w,color='g',align='center')

# # Set the Y axis label.
# plt.ylabel('Relative probability of localization degradation')

# # Create legend and show plot
# plt.legend([ip, op],['Input features', 'Output features',])
# plt.show()