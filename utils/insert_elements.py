#! /bin/python/

hlp = '''
Arguments:
 1 = the POSCAR to be opened.
 2 = Element 1
 3 = Element 2
 4 = etc. Continue adding elements as needed.
'''
import sys
import re
args = sys.argv
args.pop(0)
name = args.pop(0)
elements = args.copy()

with open(name, 'r+') as f:
 contents = f.readlines()
 mlip_atoms = contents.pop(5)
 s = ' '
 atoms = [i for i in re.split(' ', mlip_atoms.strip()) if i]
 s1 = ' '
 for count, i in enumerate(atoms): #This bit removes stray zeros and ensures type-element matching.
  if i != '0':
   s += elements[count] + ' '
   s1 += i + ' '
 s += '\n{}\n'.format(s1)
 contents.insert(5, s)
 f.seek(0)
 f.writelines(contents)
#in other words, it turns "0 2" into "Hf \n 2" given elements B Hf Ta.
