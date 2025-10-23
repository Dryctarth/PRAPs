#!/bin/python/

#This does two things: filters an input config file so that only the lowest energy configs, plus a few, appear in the output file.
#The second thing it does, is it prints to highlow.csv the list of the the ten lowest and ten highest configs in the input...
#...as well as the 'score' the intersection of the input lowest/highest to a reference lowest/highest (relax.cfg and lowE_frx_mtp.cfg).
#To use this script without regard for the first function, make the output something unremarkable like lowout.cfg. 

#Args: 1 = input cfg file for filtering. 2 = output cfg file. 3 = Mode ('F' for Filter, 'H' for highlow, 'B' for both)
#4 = Energy threshold in eV, to do filtering by formation enthalpy, this arg should be 'Hf'.
#5+ = elements

import sys
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
args = sys.argv
import mliputils as mlp
import os.path
import re

#This stores the highest-E configs and lowest-E configs in a dict, containing a list of two lists: lowE and highE indices.
#lowE_vasp is the data from DFT_CFG.
#lowE_robust_relaxed is the data from Robust_Relaxed (relaxing the combined relax.cfg with the ALS-RP).
#relax is old, probably deprecated, keeping it in here just in case I was wrong and I need it later.
#This dict is for score generation, by comparing any 'post' config files to some reference to see if the 'post' highlow agrees with reference. 
hl = {'relax':[], 'lowE_robust_relaxed':[], 'lowE_vasp':[], 'dft_filt':[]}

def get_highlow(name, f, hl):
    'Reads a high-low block and gets the high-low lists'
    line = f.readline()
    line = f.readline()
    hl[name].append([int(i) for i in re.split(r'[\[\] ,\'\"\n]', line) if i])
    line = f.readline()
    line = f.readline()
    hl[name].append([int(i) for i in re.split(r'[\[\] ,\'\"\n]', line) if i])
    return hl

def get_stuff(name, hl, high, low):
    'Does some set math to get the numbers for the a-b/c-d string.'
    highs = len(set(set(hl[name][1]) & set(high)))
    lows = len(set(set(hl[name][0]) & set(low)))
    highneg = len(set(set(hl[name][0]) & set(high)))
    lowneg = len(set(set(hl[name][1]) & set(low)))
    return lows, lowneg, highs, highneg

def get_str(name, hl, high, low):
    'While reading the high-low file, do the comparison and get the output string.'
    if "lowE_robust_relaxed" in name: #don't need to generate score for reference config
        return ''
    elif "filt.cfg" in name: #don't need to generate score for reference config
        return ''
    elif "lowE_vasp" in name: #don't need to generate score for reference config
        return ''
    elif '_mtp' in name:
        lows, lowneg, highs, highneg = get_stuff('lowE_robust_relaxed', hl, high, low)
    elif '_vasp' in name:
        lows, lowneg, highs, highneg = get_stuff('lowE_vasp', hl, high, low)
    else:
        lows, lowneg, highs, highneg = get_stuff('dft_filt', hl, high, low)
    s = '  Score = {}-{}/{}-{}\n'.format(lows, lowneg, highs, highneg)
    return s

#read the cfg file into the dataframe.
cfg = mlp.read_cfg_from_file(args[1])
cfg.loc[:,('Feature', 'index')] = cfg.index

#If mode is F or B, do the filtering.
if args[3] != 'H':
    if args[4] == 'Hf': #If the filtering is by Hf, get the Hf. 
        if os.path.exists('refs_dftrelaxed.cfg'): #if using REF_CFG for Hf reference vals.
            gs = mlp.read_cfg_from_file('refs_dftrelaxed.cfg')
            endpts = mlp.get_min_endpoints_from_cfg(gs)
        else: #If not using REF_CFG, just use the els.
            els = args[5::]
            endpts = mlp.get_min_endpoints_from_els(els)
        lowE = mlp.get_Hf(cfg, endpts)
    lowE = mlp.get_low_E(cfg, args[4]) #get_low_E will figure out if filtering by chull_var or Hf.
    mlp.write_cfg(lowE, args[2])

#if the mode is H or B, do the highlow.
if args[3] != 'F':
    #This fills in the hl dict for score generation.
    if os.path.exists('highlow.csv'):
        with open('highlow.csv', 'r') as f:
            while True:
                line = f.readline()
                #if "relax" in line:
                    #hl = get_highlow('relax', f, hl)
                if "lowE_robust_relaxed" in line:
                    hl = get_highlow('lowE_robust_relaxed', f, hl)
                elif "filt.cfg" in line:
                    hl = get_highlow('dft_filt', f, hl)
                elif "lowE_vasp" in line:
                    hl = get_highlow('lowE_vasp', f, hl)
                elif line == '': break
    #Write the highlow.csv file.
    with open('highlow.csv', 'a') as f:
        df = cfg.loc[:,('Energy','E/atom')]
        df = df.sort_values()
        f.write('--{}-- \n'.format(args[1]))
        f.write('Ten Lowest:\n')
        low = list(df.head(10).index)
        high = list(df.tail(10).index)
        f.write(repr(low)+'\n')
        f.write('Ten Highest:\n')
        f.write(repr(high)+'\n')
        f.write(get_str(args[1], hl, high, low))
        f.write('\n')

