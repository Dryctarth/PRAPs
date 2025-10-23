#!/bin/python
import sys
args = sys.argv
import re
#Looks at a mlip-calc-errors output and returns 2*RMSE in eV/atom for energy.
#Args 1 = mlip-errors.txt
with open(args[1], 'r') as f:
 while True:
  line = f.readline()
  if "Energy per atom" in line:
   while True:
    line = f.readline()
    if "RMS" in line:
     rms = [i for i in re.split(' ', line.strip()) if i][-1]
     break
    else: pass
   break
  else: pass

print(float(rms)*2)

