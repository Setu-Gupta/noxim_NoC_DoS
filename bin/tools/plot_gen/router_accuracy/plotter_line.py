'''
Usage: python3 path/to/this/file path/to/accuracy/report
Makes a 3dbar graph for accuracy
'''

from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors
import sys

def get_accuracy():
	accuracy = {}
	with open(sys.argv[1], 'r') as report:
		for line in report:
			data = line.split()
			data.remove(":")

			router = data[0].split("_")
			key_x = int(router[0])
			key_y = int(router[1])
			key_id = key_x + 8*key_y + 1
			key_dir = 1 if 'in' in router[2] else 0
			key = (key_id, key_dir)

			acc = float(data[1].replace(",", ""))

			accuracy[key] = acc
	return accuracy

def f(accuracy, in_out):
	x = []
	y = []
	for x_val in range(1,65):
		x.append(x_val)
		y.append(accuracy[(x_val, in_out)])
	return x, y


accuracy = get_accuracy()

x, y = f(accuracy, 1)

cmap = cm.get_cmap('viridis') # Get desired colormap - you can change this!
max_height = np.max(y)   # get range of colorbars so we can normalize
min_height = np.min(y)
rgba = [cmap((k-min_height)/(max_height-min_height)) for k in y]

# plt.bar(x, y, color=rgba)		# <----------- Uncomment this for bar graph
plt.plot(x,y,'r', marker='o', markerfacecolor='b', markeredgecolor='b')		# <----------- Uncomment this for line graph
plt.title(label="Accuracy for different routers", fontsize=18)
plt.xlabel("Router ID", fontsize=16)
plt.xticks(list(range(2, 65, 2)))
plt.ylabel("Accuracy in %", fontsize=16)
plt.autoscale(enable=True, axis='x', tight=True)
# plt.grid()	# <--------- Uncomment this for grid
plt.show()