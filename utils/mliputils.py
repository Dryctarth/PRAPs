# -*- coding: utf-8 -*-
"""
Created on Sat Dec 11 21:11:58 2021

@author: Josiah
Place in /projects/academic/ezurek/software/customPythonModules
"""

import pandas as pd
import statistics as st
import re
import numpy as np
#import pymatgen as mg
#from pymatgen.core.composition import Composition
#from pymatgen.analysis import phase_diagram as pdm

endpoints = {'Sc':-6.332, 'Ti':-7.939, 'V':-9.630, 'Cr':-9.078, 'Mn':-8.455, 'Fe':-9.157, 'Co':-7.109, 'Ni':-5.778, 'Cu':-4.100, 'Zn':-1.266,\
    'Y':-10.083, 'Zr':-6.464, 'Nb':-8.478, 'Mo':-10.844, 'Tc':-10.360, 'Ru':-9.272, 'Rh':-7.341, 'Pd':-5.382, 'Ag':-2.827, 'Cd':-0.912,\
    'La':-4.918, 'Hf':-9.953, 'Ta':-11.849, 'W':-13.012, 'Re':-12.433, 'Os':-11.219, 'Ir':-8.858, 'Pt':-6.055, 'Au':-3.277, 'Hg':-0.308,\
    'B':-6.693, 'C':-9.223, 'N':-8.331, 'O':-4.943, 'Al':-3.745, 'Ga':-2.415, 'Ge':-4.504, 'As':-4.652, 'In':-2.587, 'Sn':-3.764,\
    'Sb':-4.117, 'Tl':-2.363, 'Pb':-3.704, 'Bi':-4.038, 'Li':-1.906, 'Be':-3.741, 'Na':-1.315, 'Mg':-1.593, 'K':-1.906, 'Ca':-2.001,\
    'Rb':-0.962, 'Sr':-1.684, 'Cs':-0.853, 'Ba':-1.924, 'Te':-3.141}

typedict = {}

#Very important, for future: 
    #To grab elements out of a string such as "CHfTa" or "HLuNaW"
    #use the regex: re.findall(r'[A-Z][a-z]|[A-Z]', string)

def init_configs():
    a = ['Size', 'Lattice', 'Lattice', 'Lattice', 'Atoms', 'Atoms', 'Atoms', 'Atoms', 'Atoms',
         'Forces', 'Forces', 'Forces', 'Energy', 'Energy', 'Stresses', 'Stresses', 
         'Stresses', 'Stresses', 'Stresses', 'Stresses']
    b = ['', 'X', 'Y', 'Z', 'cd', 'type', 'x', 'y', 'z', 'fx', 'fy', 'fz', '', 'E/atom', 'xx', 'yy', 'zz', 'yz', 'xz', 'xy']
    cfg = pd.MultiIndex.from_arrays([a,b], names=('Property', 'Value'))
    cfg = pd.DataFrame(columns=cfg)
    return cfg

def read_cfg_from_file(file):
    'Reads a MLIP.cfg file and converts it into a pandas MultiIndex.'
    cfg = init_configs()
    with open(file, 'r') as f:
        count = 0
        while True:
            line = f.readline()
            if line == 'BEGIN_CFG\n':
                count += 1
            elif 'Size' in line:
                cfg.loc[count, ('Size','')] = f.readline().strip()
            elif 'Supercell' in line:
                cfg.loc[count, ('Lattice','X')] = f.readline().strip()
                cfg.loc[count, ('Lattice','Y')] = f.readline().strip()
                cfg.loc[count, ('Lattice','Z')] = f.readline().strip()
            elif 'AtomData' in line:
                x = ''; y = ''; z = ''; types=''
                fx = ''; fy = ''; fz = ''
                if 'cartes' not in line: cd = 'd'
                else: cd = 'c'
                for i in range(int(cfg.loc[count, ('Size','')])):
                    atom = [j for j in re.split(r'[ \t]' ,f.readline().strip()) if j]
                    types += atom[1] + ' '
                    x += atom[2] + ' '
                    y += atom[3] + ' '
                    z += atom[4] + ' '
                    if len(atom) > 5:
                        fx += atom[5] + ' '
                        fy += atom[6] + ' '
                        fz += atom[7] + ' '
                cfg.loc[count, ('Atoms', slice(None))] = [cd, types, x, y, z]
                if fx:
                    cfg.loc[count, ('Forces', slice(None))] = [fx, fy, fz]
            elif 'Energy' in line: #in eV, not meV
                cfg.loc[count, ('Energy', '')] = f.readline().strip()
                cfg.loc[count, ('Energy', 'E/atom')] = float(cfg.loc[count, ('Energy','')])/float(cfg.loc[count, ('Size','')])
            elif 'PlusStress' in line:
                S = [i for i in re.split(r'[ \t]' ,line.strip()) if i]
                stress_dict = dict(zip(S[1::], range(0,6)))
                stresses = [i for i in re.split(r'[ \t]', f.readline().strip()) if i]
                S = [stresses[stress_dict['xx']], stresses[stress_dict['yy']],
                     stresses[stress_dict['zz']], stresses[stress_dict['yz']],
                     stresses[stress_dict['xz']], stresses[stress_dict['xy']]]
                cfg.loc[count, ('Stresses', slice(None))] = S
            elif 'Feature' in line:
                F = [i for i in re.split(r'[ \t]', line.strip()) if i]
                cfg.loc[count, ('Feature', F[1])] = F[2]
            elif 'END_CFG' in line:
                pass
            elif line == '':
                break
    return cfg

def read_json(file):
    'Reads a JSON generated bt AFLOW 3.2.13 or later, and makes it a cfgDF.'
    import json
    cfg = init_configs()
    data = {}
    with open(file, 'r') as f:
        data = json.load(f)
    els = list(set(data['data'][0]['atoms']['type']))
    els.sort()
    typedict = {i:j for j,i in enumerate(els)} #nb: use this for Ba:0, O:1 typedicts
    cmpd = ''
    for i in els:
        cmpd += i
    auid = re.split(':', data['data'][0]['auid'])[-1]
    rstep = 0
    for count,i in enumerate(data['data']):
        s = len(i['atoms']['cpos'])
        cfg.loc[count,('Size','')] = s
        cfg.loc[count,('Energy','')] = i['energy']
        cfg.loc[count,('Energy','E/atom')] = float(cfg.loc[count,('Energy','')])/s
        cfg.loc[count,('Stresses',slice(None))] = i['stress'] 
        cfg.loc[count,('Feature','elements')] = cmpd
        for c,j in enumerate(['X','Y','Z']):
            cfg.loc[count,('Lattice',j)] = '{} {} {}'.format(i['lattice'][c][0],i['lattice'][c][1],i['lattice'][c][2])
        x = ''; y = ''; z = ''; types = ''
        fx = ''; fy = ''; fz = ''; cd = ''
        a = i['atoms']['cpos']
        f = i['atoms']['force']
        #if re.match(r'[cC]', data['units']['position']): cd = 'c'
        #else: cd = 'd'
        cd = 'c'
        for j in range(s):
            x += str(a[j][0]) + ' '
            y += str(a[j][1]) + ' '
            z += str(a[j][2]) + ' '
            fx += str(f[j][0]) + ' '
            fy += str(f[j][1]) + ' '
            fz += str(f[j][2]) + ' '
            types += str(typedict[i['atoms']['type'][j]]) + ' '
        cfg.loc[count,('Atoms',slice(None))] = [cd, types, x, y, z]
        cfg.loc[count,('Forces',slice(None))] = [fx, fy, fz]
        feat = 'aflow.org/JSON/{}/'.format(cmpd) #sets up consistent 'Feature from'.
        if re.split(':', i['auid'])[-1] != auid:
            auid = re.split(':', i['auid'])[-1]
            rstep = 1
        else:
            rstep += 1
        feat += auid + '/relax-step={}'.format(rstep)
        cfg.loc[count,('Feature','from')] = feat
    return cfg

def lat_transform(lat, V):
    'Takes the lattice and volume scaling number from a POSCAR and fixes when that volume-scaling number is not 1.'
    temp = []
    for i in range(3):
        temp.append([float(j)*V for j in re.split(' ', lat[i]) if j])
    lat = []
    for i in range(3):
        lat.append('{} {} {}'.format(temp[i][0], temp[i][1], temp[i][2]))
    return lat

def read_cfg_from_poscar(file, cfg=None, sg=None, els=None, ffrom=None):
    "Appends a poscar to the end of a cfg-df."
    if cfg is None:
        cfg = init_configs()
    val = len(cfg) + 1
    lat = []; coords = []; Vcd = []
    with open(file, 'r') as f:
        line = f.readline().strip() #comment line, can become Feature, from.
        if ffrom:
            cfg.loc[val, ('Feature','from')] = ffrom
        else:
            cfg.loc[val, ('Feature','from')] = line
        Vcd.append(float(f.readline().strip())) #Volume-scaling number
        for i in range(3): #The lattice bits
            lat.append(f.readline().strip())
        line = f.readline().strip() #Check to see if the next line are the elements, or just quantities.
        if not re.match(r'\d', line):
            poscar_els = [i for i in re.split(' ', line) if i]
            line = f.readline().strip() #Element quantitites
            line = [int(i) for i in re.split(' ', line) if i] #Element quantities
        else:
            line = [int(i) for i in re.split(' ',line) if i] #Element quantities, again
            if els is None:
                poscar_els = [count for count, i in enumerate(line)] #if no els and no elements in POSCAR, do this.
            else:
                poscar_els = els.copy() #If no elements in poscar, but els is given, just set them the same.
        size = sum(line)
        if els is None: 
            typedict = {}
            for count, i in enumerate(poscar_els):
                typedict[i] = [count, line[count]]
            els = poscar_els.copy()
        else:
            typedict = {}
            for count, i in enumerate(els):
                typedict[i] = [count]
            poscar_typedict = dict(zip(poscar_els, line))
            for i in poscar_typedict:
                typedict[i].append(poscar_typedict[i])
        line = f.readline().strip()
        if re.match(r'[cC]', line):
            Vcd.append('c')
        else:
            Vcd.append('d')
        for i in range(size):
            coords.append(f.readline().strip())
        cfg.loc[val,('Size','')] = str(size)
    if Vcd[0] < 0:
        Vcd[0] *= -1
    lat = lat_transform(lat, Vcd[0])
    for count, i in enumerate(['X', 'Y', 'Z']):
        cfg.loc[val, ('Lattice', i)] = lat[count]
    x = ''; y = ''; z = ''
    for i in coords:
        atom = [j for j in re.split(' ', i) if j]
        x += atom[0] + ' '
        y += atom[1] + ' '
        z += atom[2] + ' '
    types = ''
    for i in poscar_els: #iterate over the elements
        for j in range(typedict[i][1]): #i[1] is the amount of each element
            types += '{} '.format(typedict[i][0]) #i[0] is the type of each element
    #cfg.loc[val, ('Feature','typedict')] = repr(typedict)
    cfg.loc[val, ('Feature','elements')] = ''
    for i in els:
        cfg.loc[val, ('Feature','elements')] += str(i)
    cfg.loc[val, ('Atoms', slice(None))] = [Vcd[1], types, x, y, z]
    if sg:
        cfg.loc[val, ('Feature', 'space-group')] = sg
    #cfg.fillna(False)
    return cfg

def write_cfg(cfg, file, mode='w', start=None, stop=None):
    'Writes cfg to file. Use -a for appending, and start/stop for range selection.'
    with open(file, mode) as f:
        for i in cfg.index[start:stop]: #should this say [start:stop] instead?
            s = 'BEGIN_CFG\n Size\n\t{}\n Supercell\n'.format(cfg.loc[i,('Size','')])
            for j in 'X', 'Y', 'Z':
                s += '\t{}\n'.format(cfg.loc[i,('Lattice',j)])
            #now add in the atom data
            if cfg.loc[i,('Atoms','cd')] == 'c':
                s += ' AtomData:  id type\tcartes_x\tcartes_y\tcartes_z\t'
            elif cfg.loc[i,('Atoms','cd')] == 'd':
                s += ' AtomData:  id type\tdirect_x\tdirect_y\tdirect_z\t'
            else: #there is a flag (False) that can be placed here to skip a config
                continue
            AD = [[x for x in re.split(r'[ \t]', cfg.loc[i,('Atoms','type')]) if x]]
            for j in 'x', 'y', 'z':
                AD.append([x for x in re.split(r'[ \t]', cfg.loc[i,('Atoms',j)]) if x])
            if type(cfg.loc[i,('Forces','fx')]) is str:
                s += 'fx\tfy\tfz\n'
                for j in 'fx', 'fy', 'fz':
                    AD.append([x for x in re.split(r'[ \t]', cfg.loc[i,('Forces',j)]) if x])
            else: s += '\n'
            for j in range(int(cfg.loc[i,('Size','')])):
                atom = [j+1]
                for k in AD:
                    atom.append(k[j])
                if type(cfg.loc[i,('Forces','fx')]) is str:
                    s += '\t{0[0]}\t{0[1]}\t{0[2]}\t{0[3]}\t{0[4]}\t{0[5]}\t{0[6]}\t{0[7]}\n'.format(atom)
                else:
                    s += '\t{0[0]}\t{0[1]}\t{0[2]}\t{0[3]}\t{0[4]}\n'.format(atom)
            #now add energy, stress, and features.
            if not np.isnan(float(cfg.loc[i, ('Energy','')])):
                s += ' Energy\n\t{}\n'.format(cfg.loc[i,('Energy','')])
            if not np.isnan(float(cfg.loc[i,('Stresses','xx')])):
                s += ' PlusStress:  xx\tyy\tzz\tyz\txz\txy\n'
                s += '\t{0[0]}\t{0[1]}\t{0[2]}\t{0[3]}\t{0[4]}\t{0[5]}\n'.format(list(cfg.loc[i,('Stresses',slice(None))]))
            if 'Feature' in cfg.columns:
                fs = [i for i in cfg.columns if 'Feature' in i]
                for j in fs:
                    s += ' {}\t{}\t{}\n'.format(j[0], j[1], cfg.loc[i,j])
            s += 'END_CFG\n\n'
            f.write(s)
    return

def organize_atoms(cfg):
    'Arranges the atoms by [type, x, y, z]. This arranges atoms in bc-planes, stacked along a.'
    atoms = pd.DataFrame()
    for i in cfg.index:
        els = [int(j) for j in cfg.loc[i,('Atoms','type')].split(' ') if j]
        xs = [float(j) for j in cfg.loc[i,('Atoms','x')].split(' ') if j]
        ys = [float(j) for j in cfg.loc[i,('Atoms','y')].split(' ') if j]
        zs = [float(j) for j in cfg.loc[i,('Atoms','z')].split(' ') if j]
        atoms = pd.DataFrame(data=[els,xs,ys,zs], index=['els','x','y','z'])
        atoms = atoms.transpose()
        atoms = atoms.sort_values(by=['els','x']).reset_index(drop=True)
        els_str = ''; xstr = ''; ystr = ''; zstr = ''
        for count in atoms.index:
            els_str += '{} '.format(int(atoms.loc[count,'els']))
            xstr += '{} '.format(atoms.loc[count,'x'])
            ystr += '{} '.format(atoms.loc[count,'y'])
            zstr += '{} '.format(atoms.loc[count,'z'])
        cfg.loc[i,('Atoms','type')] = els_str
        cfg.loc[i,('Atoms','x')] = xstr
        cfg.loc[i,('Atoms','y')] = ystr
        cfg.loc[i,('Atoms','z')] = zstr
    return cfg

def get_comp(cfg, style=0, typedict=None):
    '''Adds the Comp column to the cfg-df.
    Styles:
        0 (default) = 0_0.5_1_0.5
        1 = Cr2Mn2 (Needs typedict)
        2 = {0:0.5, 1:0.5} (will store as a string, use eval() or json to get dict back.)
    '''
    size = cfg.loc[:,('Size','')].astype(int)
    els = cfg.loc[:,('Atoms','type')]
    mx = len(set([j for i in list(els) for j in i if re.match(r'\d', j)]))
    for i in cfg.index: #Build comp strings
        if style == 2:
            comp = {}
        else:
            comp = ''
        el = [int(j) for j in re.split(r'[ \t]', els[i]) if j]
        elset = set(el)
        for j in elset:
        #for j in range(mx): #Using the max Nels here ensures that mono and binaries still get proper comp string
            if style != 1:    
                Natoms = el.count(j)/size[i]
            else:
                Natoms = el.count(j)
            if style == 0:
                comp += '{}_{}_'.format(j, Natoms)
            elif style == 1:
                comp += '{}{}'.format(typedict[j],Natoms)
            elif style == 2:
                comp[j] = Natoms
            else:
                raise KeyError('Please set the "style" argument to 0, 1, or 2.')
        if style == 2:
            cfg.loc[i, ('Size', 'Comp')] = repr(comp)
        else: cfg.loc[i, ('Size', 'Comp')] = comp
    return cfg

def cfg_dist(config):
    "config is a single entry from a cfg-DataFrame"
    atoms = []
    x = [float(i) for i in config[('Atoms','x')].split(' ') if i]
    y = [float(i) for i in config[('Atoms','y')].split(' ') if i]
    z = [float(i) for i in config[('Atoms','z')].split(' ') if i]
    for i in range(len(x)):
        atoms.append([x[i],y[i],z[i]])
    from scipy.spatial.distance import pdist
    dists = pdist(atoms, 'euclidean')
    return dists

def clean_df(cfg, method):
    '''Iterates over each composition, marking outliers so they are not included in the final.
    method = a string of the form "set+center+width". 
        Set = "comp" or "all". Comp means to calculate statistis and clean each composition independently. All means to calculate the statistics and clean the dataset as a whole. 
        Center = "med", "avg", or a number. 
        Width = "sd", "err", or a number.'''
    if ('Size', 'Comp') not in cfg.columns:
        cfg = get_comp(cfg)
    method = [i for i in method.split('+') if i]
    if method[0] == 'comp':
        for i in set(cfg.loc[:,('Size','Comp')]):
            dfs = cfg.loc[lambda cfg: cfg.loc[:,('Size','Comp')] == i, :]
            if method[1] == 'med':
                E_med = st.median(dfs.loc[:,('Energy','E/atom')])
            elif method[1] == 'avg':
                E_med = st.mean(dfs.loc[:,('Energy','E/atom')])
            else:
                E_med = float(method[1])
            if len(dfs) == 1:
                E_std = 1
            else:
                if method[2] == 'sd':
                    E_std = st.stdev(dfs.loc[:,('Energy','E/atom')])
                elif method[2] == 'err':
                    E_std = st.stdev(dfs.loc[:,('Energy','E/atom')])/np.sqrt(len(dfs))
                else:
                    E_std = float(method[2])
            E_rng = E_med+2*E_std, E_med-2*E_std
            for j in dfs.index:
                if E_rng[1] < dfs.loc[j, ('Energy','E/atom')] < E_rng[0]:
                    continue
                else:
                    cfg.loc[j,('Atoms','cd')] = False
    if method[0] == 'all':
        if method[1] == 'med':
            E_med = st.median(cfg.loc[:,('Energy','E/atom')])
        elif method[1] == 'avg':
            E_med = st.mean(cfg.loc[:,('Energy','E/atom')])
        else:
            E_med = float(method[1])
        if method[2] == 'sd':
            E_std = st.stdev(cfg.loc[:,('Energy','E/atom')])
        elif method[2] == 'err':
            E_std = st.stdev(cfg.loc[:,('Energy','E/atom')])/np.sqrt(len(cfg))
        else:
            E_std = float(method[2])
        E_rng = E_med+2*E_std, E_med-2*E_std
        for i in cfg.index:
            if E_rng[1] < cfg.loc[i, ('Energy','E/atom')] < E_rng[0]:
                continue
            else:
                cfg.loc[i, ('Atoms','cd')] = False
    cfg = cfg.loc[lambda cfg: cfg.loc[:,('Atoms','cd')] != False, :]
    return cfg

def get_ground_states(cfg):
    'Marks the ground states of each composition as a Feature.'
    if ('Size', 'Comp') not in cfg.columns:
        cfg = get_comp(cfg)
    cfg1 = cfg.astype({('Energy',''):float})
    mindex = [cfg1.loc[lambda cfg1: cfg1.loc[:,('Size','Comp')] == i, ('Energy','')].idxmin() 
              for i in set(cfg1.loc[:,('Size','Comp')])]
    for i in cfg.index:
        if i in mindex:
            cfg.loc[i, ('Feature', 'min_config')] = True
        else:
            cfg.loc[i, ('Feature', 'min_config')] = False
    return cfg

def get_min_endpoints_from_cfg(gs):
    'Gets the lowest-energy endpoints out of a cfg-df containing ground-states.'
    if ('Feature', 'min_config') not in gs.columns:
        gs = get_ground_states(gs)
    endpts = {}
    for i in gs.index:
        fracs = gs.loc[i, ('Size','Comp')]
        comp = gs.loc[i, ('Size','Comp')]
        fracs = [float(i) for i in re.split('_', fracs)[1::2] if i]
        comp = [int(i) for i in re.split('_', comp)[0::2] if i]
        Nels = 0
        for j in fracs:
            if j > 0: Nels += 1
        gs.loc[i,('Feature','Nels')] = Nels
        if Nels == 1:
            b = comp[fracs.index(1.0)]
            endpts[b] = gs.loc[i,('Energy','E/atom')]
    return endpts

def get_min_endpoints_from_els(els):
    'gets the endpoints from the endpoints dict, els is a list of elements.'
    endpts = {}
    for count,i in enumerate(els):
        endpts[count] = endpoints[i]
    return endpts

def get_Hf(cfg, endpts):
    "Adds the ('Energy', 'Hf') column to the cfg-df in eV/atom."
    if ('Size', 'Comp') not in cfg.columns:
        cfg = get_comp(cfg)
    for i in cfg.index:
        comp_list = [i for i in re.split('_', cfg.loc[i,('Size','Comp')]) if i]
        comp_dict = {}
        for count, j in enumerate(comp_list):
            if count%2 == 0:
                comp_dict[int(j)] = float(comp_list[count+1])
            else: continue
        e = cfg.loc[i, ('Energy', 'E/atom')]
        for j in comp_dict.keys():
            e -= comp_dict[j]*endpts[j]#/int(cfg.loc[i,('Size','')])
        cfg.loc[i, ('Energy', 'Hf')] = e
    return cfg

def config_entropy(cfg, style=0, typedict=None):
    "Adds ('Feature', 'Entropy') to the cfg-df. Only returns configurational entropy, in eV/K."
    cfg = get_comp(cfg)
    for i in cfg.index:
        comp = cfg.loc[i,('Size', 'Comp')]
        comp = [float(j) for j in re.split('_', comp) if j]
        vals = []
        for count, j in enumerate(comp):
            if count%2==1 and j > 0:
                vals.append(j*np.log(j))
        cfg.loc[i,('Feature','Entropy')] = 0.0000861733*sum(vals)
    if style != 0:
        cfg = get_comp(cfg, style=style, typedict=typedict)
    return cfg

def get_G(cfg, endpts, T):
    '''Adds ('Energy','Gibbs') column to the cfg-df, in eV/atom.
    NB: If you don't include your preferred entropy in ('Feature','Entropy'),
    this will calculate and use the configurational entropy.'''
    if ('Feature','Entropy') not in cfg.columns:
        cfg = config_entropy(cfg)
    for i in cfg.index:
        comp = [float(j) for j in re.split('_', cfg.loc[i,('Size','Comp')]) if j]
        comp_dict = {}
        for count, j in enumerate(comp):
            if count%2 == 0:
                comp_dict[int(j)] = comp[count+1]
        E = cfg.loc[i,('Energy','E/atom')]
        S = cfg.loc[i,('Feature','Entropy')]/int(cfg.loc[i,('Size','')])
        M = sum([comp_dict[j]*endpts[j] for j in comp_dict])
        G = E - T*S - M
        cfg.loc[i,('Energy','Gibbs')] = G
    return cfg

def get_low_E(cfg, lim=0.05):
    'Grabs the configs in each comp that have the min E up to the limit (default 50 meV).'
    if ('Size', 'Comp') not in cfg.columns:
        cfg = get_comp(cfg)
    try:
        lim = float(lim)
    except ValueError:
        lim = 'Hf'
    if ('Feature', 'Pressure') in cfg.columns:
        cfg = get_volumes(cfg)
        for i in cfg.index:
            cfg.loc[i,('Energy','Enthalpy')] = float(cfg.loc[i,('Energy','')]) + float(cfg.loc[i,('Feature','Pressure')])*cfg.loc[i,('Lattice','Volume')]*0.0062414
            cfg.loc[i,('Energy','H/atom')] = cfg.loc[i,('Energy','Enthalpy')]/int(cfg.loc[i,('Size','')])
    low_E = pd.DataFrame(columns=cfg.columns)
    for i in set(cfg.loc[:,('Size','Comp')]):
        temp = cfg.loc[lambda cfg: cfg.loc[:, ('Size', 'Comp')] == i, :]
        m = temp.loc[:,('Energy', 'E/atom')].min()
        for j in temp.index:
            if lim == 'Hf':
                if temp.loc[j, ('Energy', 'Hf')] < 0:
                    low_E.loc[j,:] = cfg.loc[j,:]
            elif ('Feature','Pressure') in cfg.columns:
                if temp.loc[j,('Energy','H/atom')] <= (m + lim):
                    low_E.loc[j,:] = cfg.loc[j,:]
            else:
                if temp.loc[j, ('Energy', 'E/atom')] <= (m + lim):
                    low_E.loc[j,:] = cfg.loc[j,:]
    return low_E

def get_RMSE(fin):
    'Looks in a MLIP calc-errors output (as a file) and grabs the E/atom RMSE.'
    with open(fin, 'r') as f:
        while True:
            line = f.readline()
            if "Energy per atom" in line:
                while True:
                    line = f.readline()
                    if "RMS" in line:
                        rms = [i for i in re.split(' ', line.strip()) if i][-1]
                        break
                    else: pass
                break
            elif line == '': break
            else: pass
    return float(rms)*2

def write_highlow(cfg, cfg_name, fin='highlow.csv', N=10):
    'Looks in any cfg-dataframe and writes the N-lowest and N-highest energy configs to fin.'
    with open(fin, 'a') as f:
        df = cfg.loc[:,('Energy','E/atom')]
        df = df.sort_values()
        f.write('--{}-- \n'.format(cfg_name))
        f.write('Ten Lowest:\n')
        low = list(df.head(N).index)
        high = list(df.tail(N).index)
        f.write(repr(low)+'\n')
        f.write('Ten Highest:\n')
        f.write(repr(high)+'\n')
        f.write('\n')
    return

def convert_comp(ocfg, typedict):
    'Deprecated'
    cfg = ocfg.copy()
    for i in cfg.index:
        c = cfg.loc[i, ('Size', 'Comp')].split('_')
        c.pop(-1)
        els = []
        stoich = []
        for count, j in enumerate(c):
            if count%2 == 0:
                els.append(typedict[j])
            else:
                stoich.append(j)
        s = ''
        for j in range(len(els)):
            s += els[j] + stoich[j]
        cfg.loc[i, ('Size', 'Comp')] = s
    return cfg

def make_phase_diagram(cfg, els, fout=None, cmap='terrain'):
    'Makes a pymatgen phase diagram. Deprecated.'
    if ('Size', 'Comp') not in cfg.columns:
        cfg = get_comp(cfg)
    if '_' in cfg.loc[1,('Size', 'Comp')]:
        a = [str(i) for i in range(len(els))]
        ncfg = convert_comp(cfg, dict(zip(a,els)))
    else: ncfg = cfg.copy()
    pdentries = []
    for i in ncfg.index:
        pdentries.append(pdm.PDEntry(ncfg.loc[i,('Size','Comp')], float(ncfg.loc[i,('Energy','')])))
    elements = [mg.core.periodic_table.Element(i) for i in els]
    try:
        phases = pdm.PhaseDiagram(pdentries,elements=elements)
    except ValueError:
        for i in els:
            pdentries.append(pdm.PDEntry(i, endpoints[i]))
        phases = pdm.PhaseDiagram(pdentries,elements=elements)
    plot = pdm.PDPlotter(phases, show_unstable=0.2, backend='matplotlib')
    if fout:
        plot.write_image(fout, image_format='png', label_unstable=False, energy_colormap=cmap)
    else: plot.get_plot(label_unstable=False, energy_colormap=cmap)
    return

def get_crystal(X,Y,Z):
    'Takes input X,Y,Z vectors and returns one of the seven crystal families.'
    x = np.linalg.norm(X)
    y = np.linalg.norm(Y)
    z = np.linalg.norm(Z)
    alpha = round(np.degrees(np.arccos(np.dot(Y,Z)/(y*z))), 0)
    beta = round(np.degrees(np.arccos(np.dot(X,Z)/(x*z))), 0)
    gamma = round(np.degrees(np.arccos(np.dot(X,Y)/(x*y))), 0)
    x = round(x,2)
    y = round(y,2)
    z = round(z,2)
    crystal = 'Triclinic'
    if (119 <= gamma <= 121) and (89 <= alpha <= 91) and (89 <= beta <= 91):
        if 0 <= np.abs(x-y) <= 0.5:
            crystal = 'Hexagonal'
        else:
            crystal = 'Monoclinic'
    elif (89 <= gamma <= 91) and (89 <= alpha <= 91) and not (89 <= beta <= 91):
        if (0 <= np.abs(x-y) <= 0.5) and not (0 <= np.abs(x-z) <= 0.5):
            crystal = 'Monoclinic'
        elif (0 <= np.abs(x-y) <= 0.5) and (0 <= np.abs(x-z) <= 0.5):
            crystal = 'Hexagonal'
    elif (0 <= np.abs(alpha-beta) <= 2) and (0 <= np.abs(alpha-gamma) <= 0):
        if not 89 <= alpha <= 91:
            crystal = 'Rhombohedral'
        else:
            if (0 <= np.abs(x-y) <= 0.5) and (0 <= np.abs(x-z) <= 0.5):
                crystal = 'Cubic'
            elif (0 <= np.abs(x-y) <= 0.5) and not (0 <= np.abs(x-z) <= 0.5):
                crystal = 'Tetragonal'
            else:
                crystal = 'Orthorhombic'
    return crystal

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
        cfg.loc[i,('Lattice','V/atom')] = cfg.loc[i,('Lattice','Volume')]/int(cfg.loc[i,('Size','')])
        cfg.loc[i,('Lattice','Crystal')] = get_crystal(X,Y,Z)
    return cfg

def chull_prep(cfg, remove_elements=True):
    'Prepares a cfg for convex hull plotting by removing dupes and elemental configs.'
    comps = list(set(cfg.loc[:,('Size','Comp')]))
    if remove_elements:
        for count, comp in enumerate(comps):
            if '_' in comp:
                comp = [float(j) for j in re.split('_', comp) if j]
                comp = [i for c, i in enumerate(comp) if c%2 == 1]
            else:
                comp = [float(j) for j in re.split(r'[A-Z]|[a-z]', comp) if j]
            if comp.count(0) == 2:
                comps[count] = ''
        comps = [i for i in comps if i]
    cfg2 = pd.DataFrame(columns=cfg.columns)
    for i in comps:
        df = cfg.loc[lambda cfg: cfg.loc[:,('Size','Comp')] == i,:]
        idx = df.loc[:,('Energy','Hf')].astype(float).idxmin()
        cfg2.loc[idx,:] = df.loc[idx,:]
    cfg2 = cfg2.sort_index().reset_index(drop=True)
    cfg2.index += 1
    return cfg2

def convexhull(cfg, full=False):
    '''This takes a cfg DataFrame in and produces the convex hull as a DataFrame output.
    The input cfg needs to contain the Hf before you call this function.
    Note: This code adapted (with minimal changes) from code written by Xiaoyu Wang.'''
    from scipy.spatial import ConvexHull
    if ('Energy','Hf') not in cfg.columns:
        raise KeyError('Hf is not yet in this DataFrame. Please choose endpoints and run mlp.get_Hf().')
    chull = pd.DataFrame(columns=[0,1,2,'Hf'])
    cfg = chull_prep(cfg)
    cfg = get_volumes(cfg)
    #Keeping for now, but probably not going to use the 'markers' dictionary or plotting idea.
    markers = {'Triclinic':'p', 'Monoclinic':'X', 'Rhombohedral':'D', 'Hexagonal':'H',\
               'Orthorhombic':'P', 'Tetragonal':'d', 'Cubic':'s'}
    indices = []
    if full:
        for i in cfg.index:
            if '_' in cfg.loc[i,('Size','Comp')]:
                L = [float(j) for count, j in enumerate(re.split('_',cfg.loc[i,('Size','Comp')])) if count%2 == 1]
            else:
                L = [float(j) for j in re.split(r'[A-Z]|[a-z]',cfg.loc[i,('Size','Comp')]) if j]
            L = [round(j*int(cfg.loc[i,('Size','')])) for j in L]
            L.append(round(float(cfg.loc[i,('Energy','Hf')])*1000,3))
            #L.append(markers[cfg.loc[i,('Lattice','Crystal')]])
            chull.loc[i,:] = L
            indices.append(i)
    else:
        for i in cfg.index:
            if cfg.loc[i,('Energy','Hf')] < 0:
                if '_' in cfg.loc[i,('Size','Comp')]:
                    comp = [j for j in re.split('_',cfg.loc[i,('Size','Comp')]) if j]
                    compdict = {}
                    #print(comp)
                    for count, j in enumerate(comp):
                        if count%2 == 0:
                            compdict[int(j)] = float(comp[count+1])
                    for j in [0,1,2]:
                        if j not in compdict:
                            compdict[j] = 0.0
                    actual_els = list(compdict.keys())
                    actual_els.sort()
                    L = []
                    for j in actual_els:
                        L.append(compdict[j])
                    #print(L)
                    #L = [float(j) for count, j in enumerate(re.split('_',cfg.loc[i,('Size','Comp')])) if count%2 == 1]
                else:
                    L = [float(j) for j in re.split(r'[A-Z]|[a-z]',cfg.loc[i,('Size','Comp')]) if j]
                L = [round(j*int(cfg.loc[i,('Size','')])) for j in L]
                L.append(round(float(cfg.loc[i,('Energy','Hf')])*1000,3))
                #print(L)
                #L.append(markers[cfg.loc[i,('Lattice','Crystal')]])
                chull.loc[i,:] = L
                indices.append(i)
    chull = chull.reset_index(drop=True)
    chull.index += 1
    chull.loc[len(chull)+1,:] = [1,0,0,0]
    chull.loc[len(chull)+1,:] = [0,1,0,0]
    chull.loc[len(chull)+1,:] = [0,0,1,0]
    data = np.array(chull)
    ratio = [np.array(i[:3])/sum(i[:3]) for i in data]
    #ratio = [np.array(i[:Nels])/sum(i[:Nels]) for i in data
    pos = np.array([[ratio[i][2]+0.5*ratio[i][0], ratio[i][0]*0.86602540, data[i][3]] for i in range(len(ratio))])
    hull = ConvexHull(pos)
    return hull, chull, indices

def chull_dist(hull, points=None):
    '''For a given convex hull, returns the hull distances of the points.
    The default behavior returns the hull distances of the points within the given hull.
    If you provide a different list of hull.points, this returns the hull distances
    of those points to the provided hull.
    Note: This code adapted from code written by Xiaoyu Wang.'''
    v = False
    s = hull.simplices
    p = hull.points
    if points is not None:
        p = points
    distance = []
    for i in p:
        xp, yp = i[0:2]
        for j in s:
            vec = hull.points[j]
            x1, y1 = vec[0][0:2]
            x2, y2 = vec[1][0:2]
            x3, y3 = vec[2][0:2]
            d1  = ((x2 - x1)**2 + (y2 - y1)**2)**.5
            d2  = ((x3 - x1)**2 + (y3 - y1)**2)**.5
            d3  = ((x3 - x2)**2 + (y3 - y2)**2)**.5
            dp1 = ((xp - x1)**2 + (yp - y1)**2)**.5
            dp2 = ((xp - x2)**2 + (yp - y2)**2)**.5
            dp3 = ((xp - x3)**2 + (yp - y3)**2)**.5
            dd1 = abs(d1 - dp1 - dp2)
            dd2 = abs(d2 - dp1 - dp3)
            dd3 = abs(d3 - dp3 - dp2)
            c1 = (x2 - x1) * (yp - y1) - (y2 - y1) * (xp - x1)
            c2 = (x3 - x2) * (yp - y2) - (y3 - y2) * (xp - x2)
            c3 = (x1 - x3) * (yp - y3) - (y1 - y3) * (xp - x3)
            # calculate the plane
            v1 = vec[2] - vec[0]
            v2 = vec[1] - vec[0]
            cp = np.cross(v1, v2)
            a, b, c = cp
            d = np.dot(cp, vec[2])
            # skip the cover
            if (vec[0][2] >= 0 and vec[1][2] >= 0 and vec[2][2] >= 0):
                continue
            # check if plane is vertical
            elif c == 0:
                continue
            # check if point is vertex
            elif dp1 == 0 or dp2 == 0 or dp3 == 0:
                v = True
                break
            # check if point on edge
            elif dd1 < 10.**-7 or dd2 < 10.**-7 or dd3 < 10.**-7:
                break
            # check if point in triangle
            elif (c1 < 0 and c2 < 0 and c3 < 0) or (c1 > 0 and c2 > 0 and c3 > 0):
                break
        #else:
            #print("Found point not inside the convex hull!!!")
            #return
        value = i[2] - (d - a * i[0] - b * i[1]) / c
        if v:
            distance.append(0.)
            v = False
        elif abs(value) < 10**-5:
            distance.append(0.)
        else:
            distance.append(value)
    #chull.loc[:,'Distance'] = [round(i,3) for i in distance]
    distance = [round(i,3) for i in distance]
    return distance
    #return chull, indices

