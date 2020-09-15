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
			key_dir = 1 if 'in' in router[2] else 0
			key = (key_x, key_y, key_dir)

			acc = float(data[1].replace(",", ""))

			accuracy[key] = acc
	return accuracy

def f(accuracy, in_out):
	x = []
	y = []
	z = []
	for x_val in range(8):
		for y_val in range(8):

			val = accuracy[(x_val, y_val, in_out)]

			x.append(x_val)
			y.append(y_val)
			z.append(val)
	return np.array(x), np.array(y), np.array(z)

accuracy = get_accuracy()

fig1 = plt.figure(1)
ax1 = fig1.add_subplot(111, projection='3d')

x3, y3, dz = f(accuracy, 1)
dx = np.ones(8*8)
dx *= 0.2
dy = np.ones(8*8)
dy *= 0.2
z3 = np.zeros(8*8)

# cmap = cm.get_cmap('coolwarm_r') # Get desired colormap - you can change this!
# cmap = cm.get_cmap('seismic_r') # Get desired colormap - you can change this!
# cmap = cm.get_cmap('jet_r') # Get desired colormap - you can change this!
cmap = cm.get_cmap('viridis') # Get desired colormap - you can change this!
max_height = np.max(dz)   # get range of colorbars so we can normalize
min_height = np.min(dz)
# scale each z to [0,1], and get their rgb values
rgba = [cmap((k-min_height)/(max_height-min_height)) for k in dz]
bars = ax1.bar3d(x3, y3, z3, dx, dy, dz, color=rgba) #, zsort='average')

fig1.colorbar(cm.ScalarMappable(norm=colors.Normalize(vmin=min_height, vmax=max_height), cmap=cmap), ax=ax1, pad = -0.04, fraction=0.01)
ax1.set_title('Detection accuracy (Input)', fontsize=14)
ax1.set_xlabel('Router x coordinate', fontsize=12, labelpad = 12)
ax1.set_ylabel('Router y coordinate', fontsize=12, labelpad = 12)
ax1.set_zlabel('Accuracy in %', fontsize=12, labelpad = 12)
ax1.tick_params(which='major', labelsize=12)
ax1.tick_params(which='minor', labelsize=9)



fig2 = plt.figure(2)
ax2 = fig2.add_subplot(111, projection='3d')

x3, y3, dz = f(accuracy, 0)
dx = np.ones(8*8)
dx *= 0.2
dy = np.ones(8*8)
dy *= 0.2
z3 = np.zeros(8*8)

# cmap = cm.get_cmap('coolwarm') # Get desired colormap - you can change this!
max_height = np.max(dz)   # get range of colorbars so we can normalize
min_height = np.min(dz)
# scale each z to [0,1], and get their rgb values
rgba = [cmap((k-min_height)/(max_height-min_height)) for k in dz]

bars = ax2.bar3d(x3, y3, z3, dx, dy, dz, color=rgba, zsort='average')

fig2.colorbar(cm.ScalarMappable(norm=colors.Normalize(vmin=min_height, vmax=max_height), cmap=cmap), ax=ax2, pad = -0.04, fraction=0.01)
ax2.set_title('Detection accuracy (Output)', fontsize=14)
ax2.set_xlabel('Router x coordinate', fontsize=12, labelpad = 12)
ax2.set_ylabel('Router y coordinate', fontsize=12, labelpad = 12)
ax2.set_zlabel('Accuracy in %', fontsize=12, labelpad = 12)
ax2.tick_params(which='major', labelsize=12)
ax2.tick_params(which='minor', labelsize=9)


plt.show()