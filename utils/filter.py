#!/bin/python

import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules')
args = sys.argv
import mliputils as mlp
import pandas as pd
import re
import numpy as np

#Arguments: 
#1 = mode: D = distance, generally mindist. V = Volumes. T = Relaxation trajectories. G = MLIP Grade. F = Forces. Xa = Append instead of overwrite.
#2 = input .cfg file for filtration
#3 = output .cfg file. If input=output, then input will be overwritten.
#4+ all other args as needed by individual modes.

cfg = mlp.read_cfg_from_file(args[2])

mode = args[1]
if len(mode) == 2:
    write = 'a'
    mode = mode[0]
else:
    write = 'w'

def trajectories(cfg):
    '''If the 'Feature from' line is in the format: Source1/Source2/Elements/Prototype/step,
    and if it contains the word "OUTCAR" in it, then this function will grab all of the prototype labels into df.
    'df' will get filtered in the main code.
    All entries in the cfg that do not contain "OUTCAR" get put into cfg2 and admitted without filtering.
    '''
    cfg2 = pd.DataFrame(columns=cfg.columns)
    df = pd.DataFrame(columns=['proto','step'])
    if ('Feature', 'from') not in cfg.columns:
        raise TypeError("I'm sorry, Dave, that config file needs to contain 'Feature from' data.")
    for i in cfg.index:
        a = cfg.loc[i, ('Feature', 'from')]
        if 'OUTCAR' in a:
            df.loc[i, 'proto'] = re.split('/', a)[3]
            df.loc[i, 'step'] = re.split('/', a)[4]
        else:
            cfg2.loc[i,:] = cfg.loc[i,:]
    return cfg2, df

def get_volumes(cfg):
    "This adds a column ('Lattice', 'Volume') in cubic Angstroms to the cfg dataframe."
    for i in cfg.index:
        X = cfg.loc[i,('Lattice','X')]
        Y = cfg.loc[i,('Lattice','Y')]
        Z = cfg.loc[i,('Lattice','Z')]
        X = np.array([float(j) for j in re.split(' ',X) if j])
        Y = np.array([float(j) for j in re.split(' ',Y) if j])
        Z = np.array([float(j) for j in re.split(' ',Z) if j])
        cfg.loc[i,('Lattice','Volume')] = np.dot(X, np.cross(Y, Z))
    return cfg

def force_filter(index,limit):
     for f in ['fz', 'fy', 'fx']:
          stop = False
          F = [float(i) for i in re.split(' ', cfg.loc[index,('Forces',f)]) if i]
          for i in F:
              if (i > limit) or (i < -limit):
                  print('Found bad forces. In config {}, Forces-{}: {}.'.format(index,f,i))
                  stop = True
                  break
          if stop:
              break
     return stop

if mode == 'D':
    #Args: 4 = the .cfg mindist (see below). 5 = your preferred mindist. 6 = your preferred maxdist
    #Outputs configs with mindist in the preferred range.
    #Set Args: 4 = 'X' to have mliputils find min-distance manually. 
    if args[4] == 'X':
        for i in cfg.index:
            try:
                i_mindist = mlp.cfg_dist(cfg.loc[i,:]).min()
            except ValueError:
                i_mindist = (float(args[5]) + float(args[6]))/2
            cfg.loc[i,('Feature','mindist')] = i_mindist
        args[4] = cfg.loc[:,('Feature','mindist')].min()
    else:
        #print(cfg.columns)
        cfg = cfg.astype({('Feature','mindist'):float})
    mindist = float(args[5])
    maxdist = float(args[6])
    #if (float(args[4]) < mindist) or (float(args[4]) > maxdist):
    cfg = cfg.loc[lambda cfg: mindist < cfg.loc[:,('Feature','mindist')], :]
    cfg = cfg.loc[lambda cfg: cfg.loc[:, ('Feature','mindist')] < maxdist, :]
    mlp.write_cfg(cfg, args[3], mode=write)
elif mode == 'V':
    #Args: 4 = Volume scaling factor
    #For each prototype in your cfg, removes those whose volume is too large relative to that of the final relaxation step.
    #Assumes that a set of configs with the same prototype label in the 'Feature from' are all part of the same relaxation.
    outcfg, proto_step_df = trajectories(cfg)
    protos = set(proto_step_df['proto'])
    for i in protos:
        proto_cfg = pd.DataFrame(columns=cfg.columns)
        cfg_indices = proto_step_df.loc[lambda proto_step_df: proto_step_df.loc[:, 'proto'] == i].index
        for i in cfg_indices:
            proto_cfg.loc[i,:] = cfg.loc[i,:]
        proto_cfg = get_volumes(proto_cfg)
        V_max = proto_cfg.loc[cfg_indices[-1], ('Lattice', 'Volume')]*(1+float(args[4]))
        V_min = proto_cfg.loc[cfg_indices[-1], ('Lattice', 'Volume')]*(1-float(args[4]))
        for j in proto_cfg.index:
            if V_min < proto_cfg.loc[j, ('Lattice', 'Volume')] < V_max:
                outcfg.loc[j,:] = proto_cfg.loc[j,:]
    mlp.write_cfg(outcfg, args[3], mode=write)
elif mode == 'T':
    #Args: no extra args needed for this mode.
    #Assumes that a set of configs with the same prototype label in the 'Feature from' are all part of the same relaxation.
    #Keeps only the last relaxation step for each prototype in your cfg.
    outcfg, proto_step_df = trajectories(cfg)
    protos = set(proto_step_df['proto'])
    for i in protos:
        cfg_indices = proto_step_df.loc[lambda proto_step_df: proto_step_df.loc[:, 'proto'] == i]
        last_index = cfg_indices.index[-1]
        outcfg.loc[last_index,:] = cfg.loc[last_index,:]
    mlp.write_cfg(outcfg, args[3], mode=write)
elif mode == 'G':
    #Args: 4 = minimum grade. 5 = maximum grade
    #Removes configs with Grade outside the preferred range.
    cfg = cfg.astype({('Feature','MV_grade'):float})
    cfg = cfg.loc[lambda cfg: cfg.loc[:,('Feature','MV_grade')] >= float(args[4]), :]
    cfg = cfg.loc[lambda cfg: cfg.loc[:,('Feature','MV_grade')] <= float(args[5]), :]
    mlp.write_cfg(cfg, args[3], mode=write)
elif mode == 'F':
    #Args: 4 = force limits, recommend 5-10.
    #Removes configs with at least one Force term outside the range -args[4] < force < args[4].
    keeplist = []
    for i in cfg.index:
        if pd.isna(cfg.loc[i,('Forces','fx')]):
            keeplist.append(i)
            continue
        if not force_filter(i, float(args[4])):
            keeplist.append(i)
    cfg = cfg.loc[keeplist,:]
    mlp.write_cfg(cfg, args[3], mode=write)
else:
    print('The argument you provided, {}, is not a valid mode of filtration.'.format(args[1]))


