#!/bin/python/

#linux use: "python test_train.py $input.cfg $train_name.cfg $test_name.cfg $validate_name.cfg $N_of_configs_in_input"
#$input.cfg is the .cfg containing all configs that need to be separated into testing and training sets.

import sys
import numpy as np

args = sys.argv
f = open(args[1],'r')
train = open(args[2],'w')
test = open(args[3],'w')
valid = open(args[4], 'w')
d = 800/(int(args[5])/4)

a = 0 #mod counter that determines which set selected configs go in.
b = 0 #config indexer
c = -10 #holds the last-selected config to be compared against current config
while True:
 line = f.readline()
 if line == '':
  break
 if "BEGIN" in line:
  b += 1
  if b - c <= 3:
   r = 801
  else:
   r = np.random.random()
  if r < d: 
   a += 1
   c = int(b)
 if r < d:
  if a%8 == 0:
   test.write(line)
  elif a%8 == 2:
   valid.write(line)
  else:
   train.write(line)
 if "END" in line:
  continue

f.close()
train.close()
test.close() 
valid.close()
