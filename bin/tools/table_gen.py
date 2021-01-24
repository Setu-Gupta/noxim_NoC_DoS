"""
Author	: Setu Gupta
Email	: setu18190@iiitd.ac.in
Date	: 24th Jan 2021

This tool is used to generate custom traffic tables.
Filtered log is feed as input and a traffic table is generated corresponding to that input.
	python3 path/to/this/file < path/to/filtered/log > path/to/output/traffic/table
Example of creating a filtered log:
./noxim -topology MESH -dimx 2 -dimy 2 -config ../personal_configs/my_config.yaml -traffic transpose2 | grep "SENDING PACKET" > tlog

Example of a filtered log
1001    NoC.Tile[01][00]_(#1).ProcessingElement::txProcess() --> SENDING PACKET! Src:1 Dst:2 at Cycle:1001
1021    NoC.Tile[01][00]_(#1).ProcessingElement::txProcess() --> SENDING PACKET! Src:1 Dst:2 at Cycle:1021
1049    NoC.Tile[01][00]_(#1).ProcessingElement::txProcess() --> SENDING PACKET! Src:1 Dst:2 at Cycle:1049
1064    NoC.Tile[01][01]_(#3).ProcessingElement::txProcess() --> SENDING PACKET! Src:3 Dst:3 at Cycle:1064
1113    NoC.Tile[00][01]_(#2).ProcessingElement::txProcess() --> SENDING PACKET! Src:2 Dst:1 at Cycle:1113
1128    NoC.Tile[00][01]_(#2).ProcessingElement::txProcess() --> SENDING PACKET! Src:2 Dst:1 at Cycle:1128
"""

import sys
input_lines = sys.stdin.read().split('\n')

for line in input_lines:
	line_parts = line.split()
	if(len(line) == 0):
		continue
	cycle = line_parts[-1].split(':')[1]
	dst = line_parts[-3].split(':')[1]
	src = line_parts[-4].split(':')[1]
	print(src + "\t" + dst + "\t1\t1\t" + str(int(cycle)-1) + "\t" + str(int(cycle)+1) + "\t100000000")