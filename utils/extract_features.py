#!/bin/python

import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
args = sys.argv
import mliputils as mlp
import os.path
import re

#Arguments:
# Extract mode: 1 = cfg file to pull features from. 2 = poscar file
#Note. The poscar file needs to have a number attached at the end corresponding to its index in the cfg file. Eg poscar32, POSCAR43, etc.

cfg = mlp.read_cfg_from_file(args[1])
index = int(re.search(r'\d+', args[2]).group(0))+1
features = cfg.loc[index, ('Feature', slice(None))]
features.to_csv('config{}.csv'.format(index-1))
