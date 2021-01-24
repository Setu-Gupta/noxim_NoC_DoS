from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors

DELTA_X = 0.25
DELTA_Y = -3
MULTIPLIER = 10
def f():
	x = []
	y = []
	z = []
	for x_val in range(0, 64, 7):	# <------ change to 2 for a denser graph
		for y_val in range(0, 64, 7):# <------ change to 2 for a denser graph

			# Get coordinates of first router
			x1 = x_val % 8
			y1 = x_val // 8

			# Get coordinates of first router
			x2 = y_val % 8
			y2 = y_val // 8

			dist = abs(y2-y1) + abs(x2-x1) 
			val = dist + 1 
			val *= MULTIPLIER

			if(dist == 0):
				val = 0

			val = max(val, 0)

			x.append(x_val+DELTA_X)
			y.append(y_val+DELTA_Y)
			z.append(val)
	return np.array(x), np.array(y), np.array(z)

fig = plt.figure()
ax1 = fig.add_subplot(111, projection='3d')

x3, y3, dz = f()
dx = np.ones(10*10)
#dx = np.ones(16*16)# <------ change to 32*32 for a denser graph
dx *= 2
dy = np.ones(10*10)
#dy = np.ones(16*16)# <------ change to 32*32 for a denser graph
dy *= 2
z3 = np.zeros(10*10)
#z3 = np.zeros(16*16)# <------ change to 32*32 for a denser graph


# cmap = cm.get_cmap('coolwarm') # Get desired colormap - you can change this!
cmap = cm.get_cmap('viridis') # Get desired colormap - you can change this!
# cmap = cm.get_cmap('jet') # Get desired colormap - you can change this!

max_height = np.max(dz)   # get range of colorbars so we can normalize
min_height = np.min(dz)
# scale each z to [0,1], and get their rgb values
rgba = [cmap((k-min_height)/(max_height-min_height)) for k in dz]

bars = ax1.bar3d(x3, y3, z3, dx, dy, dz, color=rgba, zsort='average')


cbar = fig.colorbar(cm.ScalarMappable(norm=colors.Normalize(vmin=min_height, vmax=max_height), cmap=cmap), ax=ax1, pad = -0.02, fraction=0.01)
cbar.ax.tick_params(labelsize = 15)
ax1.set_xlabel("MIP Router ID", fontsize=16, labelpad = 18)
ax1.set_ylabel("VIP Router ID", fontsize=16, labelpad = 18)
ax1.set_zlabel("Localization time(in cycles)", fontsize=16)
ax1.set_xticks(range(0,64,7))
ax1.set_yticks(range(0,64,7))
ax1.tick_params(which='major', labelsize=16)
ax1.tick_params(which='minor', labelsize=16)

plt.show()