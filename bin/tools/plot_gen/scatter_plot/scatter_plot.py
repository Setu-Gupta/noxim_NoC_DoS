
# Import libraries
from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
 
# x -> BO
# y -> IFI
# z -> BWT

# Parsed features index
PARSED_FEATURE_COUNT            = 5
PARSED_CYCLE                    = 0
PARSED_BUFFER_STATUS            = 1
PARSED_CYCLES_SINCE_LAST_FLIT   = 2
PARSED_STALLED_FLITS            = 3
PARSED_TRANSMITTED_FLITS        = 4
PARSED_BUFFER_WAITING_TIME      = 5
PARSED_ANNOTATION               = 6
 
# Creating dataset
attack = [[], [], []]
non_attack = [[], [], []]
for line in open('random_data', 'r'):
	raw_data = list(map(float, line.split(',')))
	if(raw_data[-1] == 1):	# Attack
		attack[0].append(raw_data[PARSED_BUFFER_STATUS])
		attack[1].append(raw_data[PARSED_CYCLES_SINCE_LAST_FLIT])
		attack[2].append(raw_data[PARSED_BUFFER_WAITING_TIME])
	else:
		non_attack[0].append(raw_data[PARSED_BUFFER_STATUS])
		non_attack[1].append(raw_data[PARSED_CYCLES_SINCE_LAST_FLIT])
		non_attack[2].append(raw_data[PARSED_BUFFER_WAITING_TIME])

# z = np.random.randint(100, size =(50))
# x = np.random.randint(80, size =(50))
# y = np.random.randint(60, size =(50))
 
# Creating figure
fig = plt.figure(figsize = (10, 7))
ax = plt.axes(projection ="3d")
 
# Creating plot
ax.scatter3D(attack[0], attack[1], attack[2], color = "red")
ax.scatter3D(non_attack[0], non_attack[1], non_attack[2], color = "blue")
plt.title("Attack and non attack scenarios")
ax = plt.gca()
ax.set_xlabel("Slots free in buffer")
ax.set_ylabel("Inter-Flit Interval")
ax.set_zlabel("Buffer Waiting Time")

# show plot
plt.show()
