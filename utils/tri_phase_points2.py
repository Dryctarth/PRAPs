#!/bin/python/

import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
args = sys.argv
import mliputils as mlp
import os.path
import re

#Arguments: 1 = Mode: X for Xiaoyu's script, M for Masashi's, F for forensics, which plots in Masashi-style.
#2 = The .cfg file to be graphed. 3 = The input for the TriVex script, no file extensions.
#4+ = The elements.

#This section sets up the Hf in the cfg-DataFrame.
els = args[4::]
#els.sort()

def get_endpoints(filename):
    'Checks if the filename exists. If yes, grabs endpoints from it. If not, uses the built-in dict.'
    try:
        gs = mlp.read_cfg_from_file(filename)
        gs = mlp.get_comp(gs)
        endpts = mlp.get_min_endpoints_from_cfg(gs)
    except:
        endpts = mlp.get_min_endpoints_from_els(els)
    return endpts

typedict = dict(enumerate(els))
cfg = mlp.read_cfg_from_file(args[2])
cfg = mlp.get_comp(cfg)
if 'chullcans' in args[3]:
    #don't look for refs_dftrelaxed
    if 'DFT' in args[3]: #DFT_chullcans
        endpts = get_endpoints('ref.cfg')
    elif 'AP' in args[3]: 
        endpts = get_endpoints('refs_AP_RR.cfg')
    elif 'AR' in args[3]:
        endpts = get_endpoints('refs_AR.cfg')
    else:
        endpts = get_endpoints('refs_RR.cfg')
else: #Not chullcans, try to use DFT data.
    endpts = get_endpoints('refs_dftrelaxed.cfg')
cfg = mlp.get_Hf(cfg, endpts)
cfg = mlp.get_low_E(cfg, lim=0) #filters out duplicate configs in each comp.
fout = args[3]

#This makes the input file for Xiaoyu's TriVex script.
if (args[1] == 'X') or (args[1] == 'x'):
    fout += '.txt'
    #Header:
    fpic = args[3][:-4] + '.png'
    s = 'color terrain\nfile {}\ncontour 0\ncomponent\n'.format(fpic)
    for e in els:
        s += "{}1  ".format(e)
    s += 'meV/atom  indices\n'
    #Compositions and Hf values:
    for i in cfg.index:
        comp = cfg.loc[i,('Size','Comp')]
        comp = [float(i) for i in re.split('_', comp) if i]
        comp = [i for count, i in enumerate(comp) if count%2 == 1]
        if comp.count(0) == 2: #ignores elemental configs
            continue
        elif cfg.loc[i,('Energy','Hf')] > 0: #ignores positive Hf configs
            continue
        else:
            for j in comp:
                z = float(cfg.loc[i, ('Size','')])
                a = round(j*z)
                s += '{}  '.format(a)
            s += '{}  '.format(cfg.loc[i, ('Energy','Hf')]*1000)
            s += '{}\n'.format(i)

#This makes the input file for Masashi's TriVex script.
elif (args[1] == 'M') or (args[1] == 'm'):
    fout += '.csv'
    #chull, indices = mlp.convexhull(cfg)
    hull, chull, indices = mlp.convexhull(cfg)
    chull.loc[:,'Distance'] = mlp.chull_dist(hull)
    #print(chull)
    cfg = mlp.chull_prep(cfg)
    cfg = cfg.loc[lambda cfg: cfg.loc[:,('Energy','Hf')] <= 0,:]
    for count, i in enumerate(indices):
        cfg.loc[i,('Energy','Distance')] = chull.loc[count+1, 'Distance']
    s = '{},{},{},Hf-hull,Marker\n'.format(els[0], els[1], els[2])
    chull = chull.loc[lambda chull: chull.loc[:,'Distance'] <= 52,:]
    chull = chull.loc[lambda chull: chull.loc[:,'Distance'] >= 0,:]
    cfg = cfg.loc[lambda cfg: cfg.loc[:,('Energy','Distance')] <= 52,:]
    cfg = cfg.loc[lambda cfg: cfg.loc[:,('Energy','Distance')] >= 0,:]
    for i in chull.index:
       for j in range(3):
           s += '{},'.format(chull.loc[i,j])
       s += '{},o\n'.format(chull.loc[i,'Distance'])

#Make a version of the Masashi hull, but for forensics/full purposes.
elif (args[1] == 'F') or (args[1] == 'f'):
    fout += '.csv'
    hull, chull, indices = mlp.convexhull(cfg, full=True)
    chull.loc[:,'Distance'] = mlp.chull_dist(hull)
    cfg = mlp.chull_prep(cfg)
    for count, i in enumerate(indices):
        cfg.loc[i,('Energy','Distance')] = chull.loc[count+1, 'Distance']
    s = '{},{},{},Hf-hull,Marker\n'.format(els[0],els[1],els[2])
    for i in chull.index:
        for j in range(3):
            s += '{},'.format(chull.loc[i,j])
        if chull.loc[i,'Hf'] > 0:
            s += '{},X\n'.format(chull.loc[i,'Distance'])
        elif chull.loc[i,'Distance'] > 52:
            s += '{},v\n'.format(chull.loc[i,'Distance'])
        else:
            s += '{},o\n'.format(chull.loc[i,'Distance'])
    e = '{},{},{},Hf-hull,Marker\n'.format(els[0],els[1],els[2])
    for i in chull.index:
        for j in range(3):
            e += '{},'.format(chull.loc[i,j])
        e += '{},o\n'.format(chull.loc[i,'Hf'])
    hfout = args[3] + '_enthalpy.csv'
    with open(hfout, 'w') as f:
        f.write(e)

with open(fout, 'w') as f:
    f.write(s)

#Write the mapped files to a .cfg so you can find them later. Also get summary information?
mlp.write_cfg(cfg, args[3]+'_mapped.cfg')
