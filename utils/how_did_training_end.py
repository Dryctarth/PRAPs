#!/bin/python/

import sys
args = sys.argv

#Arguments: 1 = The MLIP training output file.
#Note, please only use with MLIP-parallel. The serial produces too many repeated thingies to parse properly.

pre = True

with open(args[1], 'r') as f:
    while True:
        line = f.readline()
        if 'Pre-training started' in line:
            pre = False
        elif ('step limit reached' in line) or ('BFGS ended' in line):
            if not pre:
                pre = True
                continue
            else:
                if 'BFGS ended' in line:
                    print('true')
                else:
                    print('false')
                break
        elif line == '':
            print('false')
            break

