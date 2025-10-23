#!/bin/python

import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
args = sys.argv
import mliputils as mlp
import os.path
import re
import pandas as pd
import numpy as np

#Arguments: 1 = cfg file. 2 = mode.
#Mode options: I = insert ID numbers. R = post-mlip-relaxation, adjust the Feature from. IR = both. O = post-OUTCAR.
#Add keyword els=a,b,c to insert elements if Feature, elements not in your cfg. Must be a comma-sep list, not space-sep

cfg = mlp.read_cfg_from_file(args[1])
caridx = False

def get_els(cfg=cfg, args=args):
    els = []
    for i in args:
        if 'els' in i:
            els = re.split('=',i)[1]
            els = [j for j in re.split(',',els) if j]
    if els: pass
    elif ('Feature', 'elements') in cfg.columns:
        els = cfg.loc[1,('Feature','elements')]
    else:
        print('Cannot find elements in arguments or in Features.')
        els = 'NotFound'
    return els

if ('I' in args[2]) or ('i' in args[2]):
    #Use keywords prefix= and suffix= to set prefixes and suffixes.
    prefix = ''; suffix = ''
    for i in args:
        if 'prefix' in i: prefix = re.split('=',i)[1] + '_'
        elif 'suffix' in i: suffix = '-' + re.split('=',i)[1]
    for i in cfg.index:
        if ('Feature','PRAPs-ID') not in cfg.columns:
            cfg.loc[i,('Feature','PRAPs-ID')] = prefix + str(int(i)) + suffix
        else:
            if cfg.loc[i, ('Feature', 'PRAPs-ID')] == 'nan':
                cfg.loc[i, ('Feature','PRAPs-ID')] = prefix + str(int(i)) + suffix
            elif type(cfg.loc[i,('Feature','PRAPs-ID')]) is str:
                cfg.loc[i,('Feature','PRAPs-ID')] = prefix + cfg.loc[i,('Feature','PRAPs-ID')] + suffix
            elif not np.isnan(cfg.loc[i,('Feature','PRAPs-ID')]):
                cfg.loc[i,('Feature','PRAPs-ID')] = prefix + str(cfg.loc[i,('Feature','PRAPs-ID')]) + suffix
            else:
                cfg.loc[i,('Feature','PRAPs-ID')] = prefix + str(int(i)) + suffix

if ('R' in args[2]) or ('r' in args[2]):
    els = get_els()
    s = 'MLIP/Relax'
    if ('Feature', 'PRAPs-ID') not in cfg.columns:
        cfg.loc[1,('Feature','PRAPs-ID')] = np.nan
    for i in cfg.index:
        if pd.notna(cfg.loc[i,('Feature','PRAPs-ID')]):
            ID = cfg.loc[i,('Feature','PRAPs-ID')] + '-RX'
        else:
            ID = '{}-RX'.format(i)
        #cfg.loc[i,('Feature','PRAPs-ID')] = ID
        rx = cfg.loc[i,('Feature','from')]
        cfg.loc[i,('Feature','from')] = '{}/{}/{}/{}'.format(s, els, ID, rx)
        try:
            cfg.loc[i,('Feature','EFS_by')] = 'mlip-rx'
        except: pass

if ('O' in args[2]) or ('o' in args[2]):
    #For this usage, please use keyword arguments:
    #cmpd = the compound, CHfTa; will be overwritten by els.
    #els = a comma-sep list of els, not space-sep: C,Hf,Ta
    #proto = AFLOW prototype, use 'None' to set to composition
    #last = the step number of the final ionic step in the OUTCAR. Without, 'all' behavior is assumed
    #all = Get step numbers for each ionic step in the OUTCAR. Do not use, assumed by default.
    #source = a source name like ./DFT/POSCAR0
    #features = a feature file like configs0.csv
    #index = a specific index, probably don't need.
    #car = a POSCAR/CONTCAR file, use to fix post-VASP type problems.
    ffrom = 'VASP/'
    proto = None; cmpd = None; els = None; source = None; features = None; car = None; last = None
    for i in args[3:]:
        if 'proto' in i: 
            proto = re.split('=', i)[1]
        elif 'cmpd' in i: cmpd = re.split('=', i)[1]
        elif 'els' in i:
            els = re.split('=',i)[1]
            els = [j for j in re.split(',',els) if j]
            cmpd = ''
            for j in els:
                cmpd += j
        elif 'source' in i:
            source = re.split('=',i)[1]
            name = re.split('/',source)[-1]
            source = re.split('/',source)[1]
        elif 'features' in i:
            features = re.split('=',i)[1]
            if not re.search(r'\d',features):
                features = features[:-4]
                cfg_df_idx = re.search(r'\d+', name).group(0)
                f_df_idx = str(int(cfg_df_idx)+1)
                features += '{}.csv'.format(cfg_df_idx)
            features = pd.read_csv(features,index_col=1)
        elif 'last' in i: last = int(re.split('=',i)[1])
        elif 'index' in i: index = int(re.split('=',i)[1])
        elif 'car' in i:
            #must include els, not cmpd, and els must be given before car
            car = re.split('=',i)[1]
            cfg = mlp.read_cfg_from_poscar(car, cfg=cfg, els=els)
            cfg.loc[:,('Feature','elements')] = cmpd
            caridx = list(cfg.index)[-1]
    #Start building the ffrom string by looking for the source and name. If not present, set name = comp
    if source is not None:
        ffrom += '{}/{}/{}/step='.format(source,cmpd,name)
    else:
        ffrom += 'OUTCAR/{}/'.format(cmpd)
        cfg = mlp.get_comp(cfg)
        name = cfg.loc[1,('Size','Comp')]
        ffrom += name + '/step='
    #To finalize the ffrom, need to check for last/all to get step= values. Then write ffrom lines
    if last is not None: 
        ffrom += str(last)
        cfg.loc[1,('Feature','from')] = ffrom
    else:
        for i in cfg.index:
            cfg.loc[i,('Feature','from')] = '{}{}'.format(ffrom,i)
    #If prototype is given, add it in.
    if proto is not None:
        for i in cfg.index:
            cfg.loc[i, ('Feature','prototype')] = proto
    #Implement fix_binary_type behavior if needed
    if car is not None:
        for i in cfg.index:
            cfg.loc[i,('Atoms','type')] = cfg.loc[caridx,('Atoms','type')]
    #If there is a features csv, read the features. Important for PRAPs-ID.
    #Should probably adjust PRAPs-ID here.
    if features is not None:
        for val in features.index:
            col = ('Feature',val)
            if col not in cfg.columns:
                cfg.loc[:,col] = features.loc[val,f_df_idx]
        if ('Feature', 'PRAPs-ID') in cfg.columns:
            for i in cfg.index:
                s = str(cfg.loc[i, ('Feature','PRAPs-ID')]) + '-DFT'
                if last is None:
                    s += '-step{}'.format(i)
                cfg.loc[i, ('Feature','PRAPs-ID')] = s
        else:
            for i in cfg.index:
                cfg.loc[i, ('Feature','PRAPs-ID')] = str(int(i)) + "-DFT"
##end big if-block

if caridx:
    #print(cfg.loc[:,('Atoms',slice(None))])
    mlp.write_cfg(cfg, args[1], start=0, stop=len(cfg)-1)
else:
    mlp.write_cfg(cfg, args[1])
