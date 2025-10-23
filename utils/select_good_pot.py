#!/bin/python

#this script is intended to be called from praps.slurm
import sys
args = sys.argv
sys.path.append('/projects/academic/ezurek/software/customPythonModules/')
import re
import mliputils as mlp
#arguments: 1 = MTP level, 2 = compound, 3 = $cmpd_pth
pth = args[3]
rmses = {}; hl = {1:[], 2:[], 3:[], 4:[], 5:[], 0:[]}
if pth[-1] != '/':
    pth += '/'
with open(pth+'highlow.csv', 'r') as f: #get the highlow results from the main data
    while True:
        line = f.readline()
        if '[' in line:
            hl[0].append([int(i) for i in re.split(r'[\[\] ,\'\"\n]', line) if i])
        elif line == '':
            break
for i in range(1,6):
    fpath = pth + '{}/'.format(str(i))
    rmses[i] = mlp.get_RMSE(fpath+'err_{}_{}.txt'.format(args[1], str(i)))
    with open(fpath+'highlow.csv', 'r') as f: #get the highlow results from the sub-dirs
        while True:
            line = f.readline()
            if '[' in line:
                hl[i].append([int(i) for i in re.split(r'[\[\] ,\'\"\n]', line) if i])
            elif line == '':
                break
    low = hl[0][0] + hl[i][0]
    high = hl[0][1] + hl[i][1]
    low = len(set(low))
    high = len(set(high))
    hl[i] = [low, high]
#this ends the 'for' loop
lows = [hl[1][0], hl[2][0], hl[3][0], hl[4][0], hl[5][0]]
highs = [hl[1][1], hl[2][1], hl[3][1], hl[4][1], hl[5][1]]
lowest = lows.index(min(lows))+1
highest = highs.index(min(highs))+1
bestrmse = min(rmses, key=rmses.get)
#determine which subdirectory to print, usually the bestrmse
if len(set([lowest, highest, bestrmse])) == 2:
    if (bestrmse==highest) or (bestrmse==lowest):
        print(bestrmse)
    else: print(lowest)
else:
    print(bestrmse)
#end
