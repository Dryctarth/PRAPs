#!/bin/python

import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
import mliputils as mlp
import re
args = sys.argv

#This reads a .cfg file and makes pymatgen-legible compositions and an output for easier pymatgen processing.
#Arguments: 1 = file-in.cfg, 2+ = elements
args.pop(0)
fin = args.pop(0)
cfg = mlp.read_cfg_from_file(fin)
s = '{}\n'.format(fin)
elements = args.copy()

s += str(len(cfg)) + '\n'
endpts = {}
for count, i in enumerate(elements):
    s += i + ' '
    endpts[i] = mlp.endpoints[i]
    endpts[count] = mlp.endpoints[i]
s += '\n'
s += ' Comp Cell_Energy Hf\n'
typedict = dict(enumerate(elements))
for i in range(len(elements)):
    typedict[str(i)] = typedict[i]
cfg = mlp.get_comp(cfg)
#print(cfg.loc[:, ('Size', 'Comp')])
cfg = mlp.get_Hf(cfg, endpts)
cfg = mlp.convert_comp(cfg, typedict)

fout = fin[0:-4]
fout += '_pymg.txt'

for i in cfg.index:
    s += ' ' + cfg.loc[i, ('Size', 'Comp')]
    s += ' ' + cfg.loc[i, ('Energy', '')]
    s += ' ' + str(cfg.loc[i, ('Energy', 'Hf')]) + '\n'

with open(fout, 'w') as f:
    f.write(s)
