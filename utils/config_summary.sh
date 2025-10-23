#!/bin/bash

#Args: 1 = input cfg to summarize

. $PWD/inpraps.sh
cfg=$1
name=$(basename $1 .cfg)
mkdir $name
pth=/projects/academic/ezurek/josiah/MLIP
mlp mindist $cfg
mlp convert-cfg $cfg POSCAR --output-format=vasp-poscar
for i in POSCAR*
do
 python $pth/utils/insert_elements.py $i ${els[@]}
 proto=$(aflow --prototype_label < $i)
 echo "$proto" >> protos.txt
 proto=($proto)
 aflow --sconv < $i > tmp
 aflow --frac < tmp > $i
 rm tmp
 python $pth/utils/fix_aflow_poscar.py $i
 mv $i ./${name}/${proto[3]}.vasp
done
python $pth/utils/config_summary.py $cfg ${els[@]}
rm protos.txt
