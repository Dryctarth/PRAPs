#!/bin/python/


import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules')
args = sys.argv
import mliputils as mlp
import re

#Args: 1 = input.cfg, 2 = output.cfg.

cfg = mlp.read_cfg_from_file(args[1])
for i in cfg.index:
    stoichs = [j for j in re.split(r'[A-Z|a-z]', cfg.loc[i,('Feature','from')]) if j]
    els = [j for j in re.split(r'\d', cfg.loc[i,('Feature','from')]) if j]
    typedict = {j:count for count, j in enumerate(els)}
    s = ''
    for count, j in enumerate(stoichs):
        for k in range(int(j)):
            s += '{} '.format(typedict[els[count]])
    cfg.loc[i, ('Atoms', 'type')] = s
mlp.write_cfg(cfg, args[2])
