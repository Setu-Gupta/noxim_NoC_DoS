
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
data = get_max_improvement(parsed_data, 20)


# Generate data
x = []	# Source and destination pairs
y1 = []	# Input ports
y2 = [] # Output ports
y3 = []	# Probability model
for src, dst, raw, rel in data:
	x.append(str(src) + ' to ' + str(dst))
	y1.append(raw[0])
	y2.append(raw[1])
	y3.append(raw[2])

xticks = np.arange(len(x))
ax1 = plt.subplot(1,1,1)
w = 0.3 # Width of bars

# Set x axis
plt.xticks(xticks + w, x, rotation=45)

# Plot for input
ip = ax1.bar(xticks, y1, width=w, color='r', align='center')

# Create another axis and plot op on it
# ax2 = ax1.twinx()
op = ax1.bar(xticks + w, y2, width=w,color='b',align='center')

# Plot fot probability model
# ax3 = ax1.twinx()
prob = ax1.bar(xticks + w*2, y3, width=w,color='g',align='center')

# Set the Y axis label.
plt.ylabel('Probability of localization')

# Create legend and show plot
plt.legend([ip, op, prob],['Only Input features', 'Only Output features', 'Probability Model'])
plt.show()