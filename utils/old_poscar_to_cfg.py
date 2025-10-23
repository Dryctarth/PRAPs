#! bin/python

import sys
import re

args = sys.argv
fin = open(args[1], 'r')
fout = open(args[2], 'a')

l=0
lat = []
size = ''
while True:
 line = fin.readline()
 l += 1
 if l < 3:
  if l == 1:
   name = line.strip()
   name = name.replace(' ', '_')
  continue
 elif 2 < l < 6:
  lat.append(line)
  continue
 elif l == 6:
  if not re.match(r'/d', line):
   line = line.strip().split(' ')
   els = ''
   for i in line:
      els += i
   line = fin.readline()
  line = [int(i) for i in re.split(' ', line.strip()) if i]
  size = str(sum(line))
  typedict = dict(zip(range(len(line)),line))
  continue
 elif l == 7:
  break

l = 1
atoms = []
at = ''
index = -1
for i in typedict:
 for j in range(typedict[i]):
  line = fin.readline()
  #if line == '':
   #break
  a = '\t' + str(l) + '\t'
  lin = [k for k in re.split(' ', line.strip()) if k]
  #print(repr(lin))
  #if lin[3] != at:
   #at = lin[3]
   #index += 1
  a += str(i) + '\t'
  for k in range(3):
   a += lin[k] + '\t'
  a += '\n'
  atoms.append(a)
  l += 1

intro = '''
BEGIN_CFG
 Size
\t{}
 Supercell
'''.format(size)
fout.write(intro)
for i in lat:
 fout.write(i)
fout.write(' AtomData: id type direct_x direct_y direct_z \n')
for i in atoms:
 fout.write(i)
fout.write('Feature\tfrom\tVASP/POSCAR/{}/{}/step=0\n'.format(els,name))
fout.write('Feature\telements\t{}\n'.format(els))
fout.write('END_CFG \n')

fin.close()
fout.close()

