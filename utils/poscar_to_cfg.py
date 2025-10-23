#!/bin/python/

import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
import mliputils as mlp
args = sys.argv
import os.path
import re
#Args 
#1 = input poscar, 2 = the output .cfg file
#3+ are optional:
#	sg = space group
#	els = elements
#	ffrom = feature from

args.pop(0)
fin = args.pop(0)
fout = args.pop(0)
if '.cfg' in fout:
    if os.path.exists(fout):
        cfg = mlp.read_cfg_from_file(fout)
    else: cfg = None
else:
    fout += '.cfg'
    cfg = None
els = None; sg = None; ffrom = None
for i in args:
    if 'sg' in i:
        sg = i.split('=')[-1]
    elif 'els' in i:
        els = i.split('=')[-1]
        els = re.findall(r'[A-Z][a-z]|[A-Z]', els)
    elif 'ffrom' in i:
        ffrom = i.split('=')[-1]
with open(fin,'r') as f:
    lines = f.readlines()
    lines[0] = lines[0].replace(' ','_')
with open(fin,'w') as f:
    f.writelines(lines)

cfg = mlp.read_cfg_from_poscar(fin, cfg=cfg, sg=sg, els=els, ffrom=ffrom)
mlp.write_cfg(cfg, fout,  mode='w')
