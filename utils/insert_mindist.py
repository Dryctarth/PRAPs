#!/bin/python/

import sys

args = sys.argv
#args : 0=self, 1=.mtp filename, 2=mindist, 3=number of elements.
#the bash cmd that leads here actually produces, like, 4 space-separated words and python needs to grab the right one.
mind = args[4]
Nels = args[5]
lines = ''
with open(args[1], 'r') as f:
	lines = f.readlines()

for count, line in enumerate(lines):
	if 'species_count' in line:
		stuff = [i.strip() for i in line.split(' ') if i]
		stuff[2] = Nels
		s = '{0[0]} {0[1]} {0[2]}\n'.format(stuff)
		lines[count] = s
	elif 'min_dist' in line:
		stuff = [i.strip() for i in line.split(' ') if i]
		stuff[2] = mind
		s = '\t{0[0]} {0[1]} {0[2]}\n'.format(stuff)
		lines[count] = s
		break
#end read
with open(args[1], 'w') as f:
	for line in lines:
		f.write(line)
#end
