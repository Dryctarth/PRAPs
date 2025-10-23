#!/bin/python

import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules')
args = sys.argv
import mliputils as mlp
import pandas as pd                                                                             
import re
import numpy as np
import matplotlib 
import matplotlib.pyplot as plt

#Args. 1 = dft cfg, 2 = mlip cfg, 3 = plot output filename
#Optional kwargs: lab1=str, lab2=str. Use these for custom labels.

cfg = mlp.read_cfg_from_file(args[2])
dft = mlp.read_cfg_from_file(args[1])
lab1 = 'DFT'
lab2 = 'MTP'
for i in args:
    if 'lab1' in i:
        lab1 = i.split('=')[-1]
    if 'lab2' in i:
        lab2 = i.split('=')[-1]

def corr(cfg, dft):
    fig, ax = plt.subplots()
    x = list(dft.loc[:,('Energy','E/atom')])
    y = list(cfg.loc[:,('Energy','E/atom')])
    ax.scatter(x,y)
    lims = [np.min([ax.get_xlim(),ax.get_ylim()]), np.max([ax.get_xlim(),ax.get_ylim()])]
    ax.plot(lims,lims,color='black', zorder=0)
    ax.set_xlabel('{} Energies (eV/atom)'.format(lab1))
    ax.set_ylabel('{} Energies (eV/atom)'.format(lab2))
    ax.set_aspect('equal')
    fig.savefig('c-'+args[3])
    return

def residuals(cfg, dft):
    fig, ax = plt.subplots(2,1,sharex=True)
    x = list(cfg.index)
    y1 = np.array(dft.loc[:,('Energy','E/atom')])
    y2 = np.array(cfg.loc[:,('Energy','E/atom')])
    ax[0].scatter(x,y1,label=lab1)
    ax[0].scatter(x,y2,label=lab2)
    ax[0].legend()
    ax[0].set_ylabel('Energy (eV/atom)')
    diff = y1 - y2
    ax[1].plot(x,diff,color='b')
    ax[1].set_xlabel('Index')
    ax[1].set_ylabel('Residuals')
    fig.savefig('r-'+args[3])
    out = pd.DataFrame(index=x, columns=[lab1,lab2])
    out[lab1] = y1
    out[lab2] = y2
    out.to_csv('data.csv')
    return

diff = []
for i in dft.index:
    diff.append(abs(dft.loc[i,('Energy','E/atom')]-cfg.loc[i,('Energy','E/atom')]))
diff = pd.Series(diff, dtype=float)
mean = diff.describe()['mean']
std = diff.describe()['std']
x = []; y = []
for i in diff:
    if i < 0.5: x.append(i)
    if mean-std < i < mean+std: y.append(i)
x = round(len(x)/len(dft)*100,2)
y = round(len(y)/len(dft)*100,2)

print('For the set of {}:'.format(args[3]))
print('{}% of configs with diff < 0.5 eV/atom'.format(x))
print('{}% of configs with diff within one std deviation of the mean.'.format(y))

corr(cfg,dft)
residuals(cfg,dft)
