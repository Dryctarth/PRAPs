#!/bin/python/

import sys
import re
import os

args = sys.argv
lines = []
#Arguments: 1 = pth, where the praps directory is stored. 2 = potcar, where potcars are stored.
#Arguments: 3 = MTPth, where the untrained MTP's are stored. 4 = module path, where your modules are stored.
#Arguments: 5 = email, for notifications. 6 (optional) = mlpth, where mliputils.py is stored
files = ['active_learning.slurm', 'praps.slurm', 'filter_mindist.py', 'lowE_configs.py', 'make_ltvc_plot.py', 'poscar_to_cfg.py', 'select_good_pot.py', 'accurate_potentials.slurm', 'filter_grade.py', 'lammps_to_cfg.py', 'pymatgen_prep.py', 'remove_duplicates.py', 'tri_phase_points2.py']
ser = '{}/ser'.format(args[1])
par = '{}/par'.format(args[1])
utils = '{}/utils'.format(args[1])

def adjust(file):
    with open(file, 'r') as f:
        lines = f.readlines()       
    for count, line in enumerate(lines):
        if 'potpth=' in line:
            line='potpth={}\n'.format(args[2])
            lines[count] = line
        elif 'pth=' in line: 
            if 'cmpd_pth=' in line: continue
            line = 'pth={}\n'.format(args[1])
            lines[count] = line
        elif 'path.append' in line:
            if len(args) > 6:
                line = 'sys.path.append(\'{}\')\n'.format(args[6])
            else: 
                line = 'sys.path.append(\'{}/utils\')\n'.format(args[1])
            lines[count] = line
            break
        elif 'MTPth=' in line:
            line = 'MTPth={}\n'.format(args[3])
            lines[count] = line
        elif 'module use' in line:
            line = 'module use {}\n'.format(args[4])
            lines[count] = line
        elif 'mail-user=' in line:
            line = '#SBATCH --mail-user={} --mail-type=ALL'.format(args[5])
            lines[count] = line
        elif line == '':
            break
    with open(file, 'w') as f:
        for line in lines:
            f.write(line)
    return

for i in os.listdir(ser):
    f = ser + '/{}'.format(i)
    adjust(f)
for i in os.listdir(par):
    f = par + '/{}'.format(i)
    adjust(f)
for i in os.listdir(utils):
    if '__' in i: continue
    f = utils + '/{}'.format(i)
    adjust(f)
