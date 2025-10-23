#!/bin/python

import sys
import numpy as np
args = sys.argv
sys.path.append('/projects/academic/ezurek/software/customPythonModules')
import mliputils as mlp

cfg = mlp.init_configs()
lammps_dump_file = open(args[1], "r")
line1 = ''
lattice = [0,0,0]
typ = []
pos_x = []
pos_y = []
pos_z = []
f_x = []
f_y = []
f_z = []
timesteps = []
#epa = []
#energy = 0
idx = 0
count = 0
while True:
    line = lammps_dump_file.readline()
    if 'ITEM: NUMBER' in line:
        line1 = 'ITEM: NUMBER'
        continue
    if 'ITEM: NUMBER' in line1:
        cfg_size = int(line)
        line1 = ''
    if 'ITEM: BOX' in line:
        line1 = 'ITEM: BOX'
        continue
    if 'ITEM: BOX' in line1:
        idx1 = 0
        for x in line.split():
            if (idx1 == 1):
                lattice[idx] = float(x)
            idx1 += 1
        idx += 1
        if (idx == 3): 
            line1 = ''
            idx = 0
        continue
    if 'ITEM: ATOMS' in line:
        line1 = 'ITEM: ATOMS'
        continue
    if 'ITEM: ATOMS' in line1:
        idx1 = 0
        for x in line.split():
            if (idx1 == 1):
                typ.append(int(x)-1)
            if (idx1 == 2): 
                pos_x.append(float(x))
            if (idx1 == 3): 
                pos_y.append(float(x))
            if (idx1 == 4): 
                pos_z.append(float(x))
            if (idx1 == 5): 
                f_x.append(float(x))
            if (idx1 == 6): 
                f_y.append(float(x))
            if (idx1 == 7): 
                f_z.append(float(x))
            idx1 += 1
        idx += 1
        if (idx == cfg_size):
            line1 = ''
            idx = 0
    if ('ITEM: TIMESTEP' in line) or (line == ''): #end of a config, write to dataframe
        if count == 0:
            pass
        else:
            cfg.loc[count, ('Size','')] = cfg_size
            cfg.loc[count, ('Lattice', slice(None))] = ['{} 0 0'.format(lattice[0]), '0 {} 0'.format(lattice[1]), '0 0 {}'.format(lattice[2])]
            ts = ''
            for j in typ:
                ts += '{} '.format(j)
            d = [[pos_x, ''], [pos_y, ''], [pos_z, ''], [f_x, ''], [f_y, ''], [f_z, '']]
            for c,j in enumerate(d):
                for k in j[0]:
                    d[c][1] += '{} '.format(k)
            cfg.loc[count, ('Atoms', slice(None))] = ['c', ts, d[0][1], d[1][1], d[2][1]]
            cfg.loc[count, ('Forces', slice(None))] = [d[3][1], d[4][1], d[5][1]]
            pos_x = []; pos_y = []; pos_z = []; f_x = []; f_y = []; f_z = []; typ = []
        if line == '': break
        else:
            count += 1
            timesteps.append(lammps_dump_file.readline().strip())

lammps_dump_file.close()

cfg = mlp.get_comp(cfg)
for i in cfg.index:
    cfg.loc[i, ('Feature', 'from')] = 'LAMMPS:{}:time_step={}'.format(cfg.loc[i,('Size', 'Comp')],timesteps[i-1])
mlp.write_cfg(cfg, args[2], mode='w')

