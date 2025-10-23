#!/bin/python/

import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt
import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
import mliputils as mlp
import re
import pandas as pd

args = sys.argv
#Arguments: [self, in1.cfg, (in2.cfg, opt) ...(other opt cfgs), els(opt), out.png]
#Arguments: 1 = the first input config, large black circles.
#Arguments: 2-5: other input configs to be small blue, green, magenta, and cyan dots.
#Arguments: 2-5+ after input configs: the elements, if you need to grab endpoints from library, but omit if endpoints are in .cfg.
#Arguments: -1 (last): the filename of the graph, the output name.
#Arguments: optional: mult=overlay, vert, hor
plt.rcParams["font.size"] = 16
plt.rcParams['figure.dpi'] = 300
plt.rcParams["font.weight"] = 'normal'
#plt.rcParams["axes.labelweight"] = 'bold'

if '.svg' not in args[-1]:
    args[-1] += '.svg'
colors = {0:'ko', 1:'b.', 2:'g.', 3:'m.', 4:'c.', 5:'y.'}
ins = []; els = []
args.pop(0)
mult = None
while args:
    i = args.pop(0)
    if '.cfg' in i:
        ins.append(i)
    elif '.svg' in i:
        out = i
    elif 'mult' in i:
        mult = re.split('=', i)[-1]
    else:
        els.append(i)
labels = []
for i in ins: #This removes the file extension from the legend entries
    labels.append(i[:-4])

def get_endpoints(filename):
    'Checks if the filename exists. If yes, grabs endpoints from it. If not, uses the built-in dict.'
    try:
        gs = mlp.read_cfg_from_file(filename)
        gs = mlp.get_comp(gs)
        endpts = mlp.get_min_endpoints_from_cfg(gs)
    except:
        endpts = mlp.get_min_endpoints_from_els(els)
    return endpts

if 'chullcans' in out:
    #don't look for refs_dftrelaxed
    if 'DFT' in out: #DFT_chullcans
        endpts = get_endpoints('ref.cfg')
    elif 'AP' in out:
        endpts = get_endpoints('refs_AP_RR.cfg')
    elif 'AR' in out:
        endpts = get_endpoints('refs_AR.cfg')
    else:
        endpts = get_endpoints('refs_RR.cfg')
else: #Not chullcans, try to use DFT data.
    endpts = get_endpoints('refs_dftrelaxed.cfg')

def make_plot(x, y, fig, ax, i):
    ax.plot(x, y, colors[i], label=labels[i])
    ax.set_xlabel('Mol Fraction {}'.format(els[-1]))
    #ax.set_ylabel('Formation Enthalpy (meV/atom)')
    ax.set_ylabel('$\Delta H_F$  (meV/atom)')
    xticks = [0, 0.2, 0.4, 0.6, 0.8, 1]
    xlabels = [els[0], '0.2', '0.4', '0.6', '0.8', els[1]]
    plt.xticks(xticks, xlabels)
    ax.hlines(0, xmin=0, xmax=1, color='r')
    ax.set_xlim(0,1)
    #plt.text(-0.05, ax.get_ylim()[0]*1.33, els[0])
    #plt.text(0.95, ax.get_ylim()[0]*1.33, els[1])
    #ax.set_ylim(-500,1000)
    return fig, ax

W = 150/25.4; H = 112.5/25.4
if mult is None:
    fig, ax = plt.subplots(figsize=(W,H))
    mult = False
elif mult == 'vert':
    fig, ax = plt.subplots(len(ins),sharey=True,sharex=True,figsize=(W,H*len(ins)))
    mult = True
elif mult == 'hor':
    fig, ax = plt.subplots(1,len(ins),sharey=True,sharex=True,figsize=(W*len(ins),H))
    mult = True
else:
    fig, ax = plt.subplots(figsize=(W,H))
    mult = False
if mult:
    colors = {0:'ko', 1:'bo', 2:'go', 3:'mo', 4:'co', 5:'yo'}
else:
    colors = {0:'ko', 1:'b.', 2:'g.', 3:'m.', 4:'c.', 5:'y.'}

for count,i in enumerate(ins):
    cfg = mlp.read_cfg_from_file(i)
    #cfg = mlp.clean_df(cfg)
    cfg = mlp.get_Hf(cfg, endpts)
    x = []
    y = [i for i in cfg.loc[:,('Energy','Hf')]*1000]
    for j in cfg.index:
        comp = cfg.loc[j, ('Size', 'Comp')]
        comp = [i for i in re.split('_', comp) if i]
        x.append(float(comp[-1]))
        #if len(comp) > 2:
        #    x.append(float(comp[-1]))
        #else:
        #    if comp[0] == '0':
        #        x.append(0)
        #    else:
        #        x.append(1)
    y.append(0); y.append(0)
    x.append(0); x.append(1)
    if mult:
        fig, ax[count] = make_plot(x, y, fig, ax[count], count)
    else:
        fig, ax = make_plot(x, y, fig, ax, count)
    if len(ins) > 1:
        if mult:
            ax[count].legend()
        else:
            ax.legend()
    fig.tight_layout()
    #q = pd.DataFrame(columns=['x','y'])
    #q.loc[:,'x'] = x
    #q.loc[:,'y'] = y
    #q.to_csv('xy_{}.csv'.format(count))

fig.savefig(out)
