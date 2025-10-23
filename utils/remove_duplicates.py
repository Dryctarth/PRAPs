#!/bin/python
import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
args = sys.argv
import mliputils as mlp
import re
import pandas as pd

cfgfile = args[1]; protos = args[2]
els = args[3:]
#Outputs a string designed for the bash rm command to remove duplicate configurations

cfg = mlp.read_cfg_from_file(cfgfile)
with open(protos, 'r') as f:
 while True:
  line = f.readline()
  if 'POSCAR' in line:
   ind = re.search(r'\d+', line).group()
   ind = int(ind)+1
  elif 'label' in line:
   label = [i for i in re.split(r' ', line) if i]
   cfg.loc[ind, ('Feature', 'label')] = label[3]
  elif line == '': break
  else: continue
labels = set(list(cfg.loc[:, ('Feature', 'label')]))
#print(labels)
#print(cfg.loc[lambda cfg: cfg.loc[:,('Feature','label')].isna(), :])
endpts = mlp.get_min_endpoints_from_els(els)
cfg = mlp.get_Hf(cfg, endpts)
#Note that ('Size', 'Comp') is in style=0
KeepList = []
for i in labels:
 cfg1 = cfg.loc[lambda cfg: cfg.loc[:, ('Feature', 'label')] == i, :]
 comps = set(cfg1.loc[:,('Size','Comp')])
 for j in comps:
  Hf = cfg1.loc[lambda cfg1: cfg1.loc[:,('Size','Comp')] == j, ('Energy', 'Hf')]
  KeepList.append(Hf.idxmin())
 #add KeepList configs to a separate DF for writing?
#mlp.write_cfg(KeepList configs)?
s = ''; q = 'Keeping: '
#If multiple configs have the same label, this only selects the lowest energy structure. Others are output for deletion.
for i in cfg.index:
 if i not in KeepList:
  s += "POSCAR{} ".format(i-1)
 else:
  q += "POSCAR{} ".format(i-1)
print(s)
#print(q)
 
