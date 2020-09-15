from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as colors

MULTIPLIER = 5
def f():
	x = []
	y = []
	z = []
	for x_val in range(1,65):
		for y_val in range(1,65):

			# Get coordinates of first router
			x1 = x_val % 8
			y1 = x_val // 8

			# Get coordinates of first router
			x2 = y_val % 8
			y2 = y_val // 8

			dist = abs(y2-y1) + abs(x2-x1)
			val = dist - 2
			val *= MULTIPLIER

			val = max(val, 0)

			x.append(x_val)
			y.append(y_val)
			z.append(val)
	return np.array(x), np.array(y), np.array(z)

fig = plt.figure()
ax1 = fig.add_subplot(111, projection='3d')

x3, y3, dz = f()
dx = np.ones(64*64)
dx *= 0.5
dy = np.ones(64*64)
dx *= 0.5
z3 = np.zeros(64*64)


# cmap = cm.get_cmap('coolwarm') # Get desired colormap - you can change this!
cmap = cm.get_cmap('viridis') # Get desired colormap - you can change this!
# cmap = cm.get_cmap('jet') # Get desired colormap - you can change this!

max_height = np.max(dz)   # get range of colorbars so we can normalize
min_height = np.min(dz)
# scale each z to [0,1], and get their rgb values
rgba = [cmap((k-min_height)/(max_height-min_height)) for k in dz]
rgbacm = cm.ScalarMappable([1,64], cmap=cmap)

bars = ax1.bar3d(x3, y3, z3, dx, dy, dz, color=rgba, zsort='average')


fig.colorbar(cm.ScalarMappable(norm=colors.Normalize(vmin=min_height, vmax=max_height), cmap=cmap), ax=ax1, pad = -0.04, fraction=0.01)
ax1.set_title('Localization time', fontsize=14)
ax1.set_xlabel("Source Router ID", fontsize=12, labelpad = 12)
ax1.set_ylabel("Destination Router ID", fontsize=12, labelpad = 12)
ax1.set_zlabel("Localization time", fontsize=12, labelpad = 12)
ax1.tick_params(which='major', labelsize=12)
ax1.tick_params(which='minor', labelsize=9)

plt.show()