import sys

x = int(sys.argv[1])
y = int(sys.argv[2])
sim_time = int(sys.argv[3])

for i in range(x*y):
	for j in range(x*y):
		print(str(i) + '\t' + str(j) + '\t1\t1\t0\t' + str(sim_time-1) + '\t' + str(sim_time))
