#!/bin/python

import sys
args = sys.argv

#Adjusts the first atom's coordinates of a POSCAR by 0.001
#Arguments: 1 = a POSCAR file.

lines = []
with open(args[1], 'r') as f:
    lines = f.readlines()

line = lines[8]
line = [i for i in line.strip().split(' ') if i]
line = [float(line[0]), float(line[1]), float(line[2])]
line[0] = line[0] + 0.001
line[1] = line[1] + 0.001
line[2] = line[2] - 0.001
line = '{}   {}   {}\n'.format(line[0], line[1], line[2])
lines[8] = line

with open(args[1], 'w') as f:
    f.writelines(lines)
#end
