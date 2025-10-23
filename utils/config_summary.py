#!/bin/python/

import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
import mliputils as mlp
args = sys.argv
import re
import pandas as pd
import numpy as np
import os.path

cfg = mlp.read_cfg_from_file(args[1])
els = args[2:]
typedict = {}
for count, i in enumerate(els):
    typedict[i] = count
    typedict[count] = i
if os.path.exists('refs_dftrelaxed.cfg'):
    gs = mlp.read_cfg_from_file('refs_dftrelaxed.cfg')
    endpts = mlp.get_min_endpoints_from_cfg(gs)
else:
    endpts = mlp.get_min_endpoints_from_els(els)
cfg = mlp.get_comp(cfg)
cfg = mlp.get_Hf(cfg, endpts)
cfg = mlp.get_comp(cfg, style=1, typedict=typedict)
cfg = mlp.chull_prep(cfg)
out = pd.DataFrame()
out.loc[:,'Energy'] = cfg.loc[:,('Energy','')]
out.loc[:,'Hf'] = cfg.loc[:,('Energy','Hf')]
out.loc[:,'mindist'] = cfg.loc[:,('Feature','mindist')]
cfg = mlp.get_volumes(cfg)
out.loc[:,'Volume'] = cfg.loc[:,('Lattice','Volume')]
#chull, indices = mlp.convexhull(cfg)
hull, chull, indices = mlp.convexhull(cfg)
chull.loc[:,'Distance'] = mlp.chull_dist(hull)
if not args[1].startswith('DFT') and 'chullcans' not in args[1]:
    dft = mlp.read_cfg_from_file('DFT_dftrelaxed.cfg')
    dft = mlp.get_Hf(dft, endpts)
    dft_hull, dft_chull, dft_indices = mlp.convexhull(dft)
    chull.loc[:,'Above_DFT'] = mlp.chull_dist(dft_hull, points=hull.points)
for count,i in enumerate(indices):
    cfg.loc[i,('Energy','Distance')] = chull.loc[count+1,'Distance']
    if 'Above_DFT' in chull.columns:
        cfg.loc[i,('Energy','Above_DFT')] = chull.loc[count+1,'Above_DFT']
dists = []; ad = []
for i in cfg.index:
    if not np.isnan(cfg.loc[i,('Energy','Distance')]):
        dists.append(cfg.loc[i, ('Energy','Distance')])
        if 'Above_DFT' in chull.columns:
            ad.append(cfg.loc[i,('Energy','Above_DFT')])
    else:
        dists.append('posHf')
        ad.append('posHf')
out.loc[:,'Distance'] = dists
if 'Above_DFT' in chull.columns:
    out.loc[:,'Above_DFT'] = ad
with open('protos.txt', 'r') as f:
    idx = 0
    while True:
        line = f.readline()
        if 'label' in line:
            idx += 1
            proto = re.split(' ', line.strip())[-1]
            out.loc[idx,'Prototype'] = proto
        elif line == '': break

out.to_csv(args[1][:-4]+'_summary.csv')
