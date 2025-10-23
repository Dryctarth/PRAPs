#!/bin/bash -l

pth=/projects/academic/ezurek/josiah/MLIP
potpth=/projects/academic/ezurek/vasp-potcars/potpaw_PBE
echo 'Title'
echo 'Maintained by Josiah Roberts (josiahro@buffalo.edu)'
echo 'Eva Zurek group, University at Buffalo, Fall 2021'
echo '---- Output SLURM Environment Variables ----'
echo 'SLURM_JOB_ACCOUNT    '$SLURM_JOB_ACCOUNT
echo 'SLURM_JOB_ID         '$SLURM_JOBID
echo 'SLURM_JOB_NODELIST   '$SLURM_JOB_NODELIST
echo 'SLURM_SUBMIT_DIR     '$SLURM_SUBMIT_DIR
echo 'SLURM_SUBMIT_HOST    '$SLURM_SUBMIT_HOST

#Arguments: 1 = the subsystem of interest: RR, ALS_AP-v, etc.
#Note: Expects to be run in the cmpd_pth/chulls directory

echo '---- Initial ----'
echo 'Current time is:'
date

. $PWD/../inpraps.sh
ELS=""
for i in ${els[@]}
do
 ELS+=$i
 ELS+=,
done
declare -A CHULLS=( [DFT]=lowE_vasp.cfg [RR]=lowE_robust_relaxed.cfg [ALS_AP_RR]=ALS_AP_RR.cfg [ALS_AP_v]=ALS_AP_v.cfg [ALS_AR_RR]=ALS_AR_RR.cfg [refs]=$REF_CFG )
if [ ! -d ./${1}/ ]; then
 mkdir $1
fi
if [ ! -d ./${1}_work/ ]; then
 mkdir ${1}_work
fi
if [ -z ${save_outcars+x} ]; then
 save_outcars=false
fi
if [ "save_outcars" = true ]; then
 mkdir $cmpd_pth/${1}_outcars/
fi
if [ -z ${custom_relax+x} ]; then
 custom_relax=false
fi


if [ ! -f ./${1}/protos.txt ]; then
 echo "Filtering ${1}."
 rm ../${1}_dftrelaxed.cfg
 touch ../${1}_dftrelaxed.cfg
 mlp convert-cfg ../${CHULLS[$1]} ./${1}/POSCAR --output-format=vasp-poscar
 cd $1
 for j in ./POSCAR*
 do #This filters out the duplicate structures so we don't relax redundantly.
  echo "$j" >> protos.txt
  python $pth/utils/insert_elements.py $j ${els[@]}
  aflow --prototype_label < $j >> protos.txt
  echo "" >> protos.txt
  python $pth/utils/extract_features.py $cmpd_pth/${CHULLS[$1]} $j
 done
 cd $cmpd_pth/chulls
 if [ "${1}" != "refs" ]; then
  rem=$(python $pth/utils/remove_duplicates.py ../${CHULLS[$1]} ./${1}/protos.txt ${els[@]})
  cd $1
  rm $rem
  echo "Done Filtering ${1}"
 fi
 cd $cmpd_pth/chulls
fi
pos=$(ls ./${1}/ | grep POSCAR | wc -l)
if [ $pos -eq 0 ]; then
 echo "Sub-directory $1 empty"
 echo 'Current time is:'
 date
 exit
fi
echo "There are $pos structures to relax."
for j in ./${1}/POSCAR*
do
 mv $j working_poscar
 cp working_poscar ./${1}_work/POSCAR
 cd ${1}_work
 echo $j
 counter=1
 while [ ! -f OUTCAR.relax1.xz ]
 do
  #######################
  module load intel
  if [ "$custom_relax" = true ]; then
   cp $cmpd_pth/INCAR_rx $cmpd_pth/chulls/${1}_work/INCAR
   cp $cmpd_pth/KPOINTS_rx $cmpd_pth/chulls/${1}_work/KPOINTS
   for e in ${els[@]}
   do
    cat $potpth/$e/POTCAR >> $cmpd_pth/chulls/${1}_work/POTCAR
   done
   module load vasp6.4.2
   mpirun -n $SLURM_NTASKS vasp
   mv OUTCAR OUTCAR.relax1
   cp CONTCAR POSCAR
   mv CONTCAR CONTCAR.relax1
   cp $cmpd_pth/INCAR_st $cmpd_pth/chulls/${1}_work/INCAR
   mpirun -n $SLURM_NTASKS vasp
   mv OUTCAR OUTCAR.relax2
   mv CONTCAR CONTCAR.relax2
  else
   aflow --mpi --poscar2aflowin < POSCAR > aflow.in
   aflow --mpi --np=$SLURM_NTASKS --run 
   unxz OUTCAR* CONTCAR*
  fi
  module load gcc/11.2.0 openmpi/4.1.1
  #######################
  if [ -f OUTCAR.relax2 ]; then
   #unxz OUTCAR.relax2.xz CONTCAR.relax2.xz
   mlp convert-cfg OUTCAR.relax2 temp.cfg --input-format=vasp-outcar
   step=$(grep BEGIN temp.cfg | wc -l)
   rm temp.cfg
   mlp convert-cfg OUTCAR.relax2 temp.cfg --input-format=vasp-outcar --last
   echo "Step is $step"
   proto=$(aflow --prototype_label < CONTCAR.relax2)
   proto=($proto)
   python $pth/utils/ID.py temp.cfg O els=$ELS source=$j car=CONTCAR.relax2 proto=${proto[3]} last=$step features=../${1}/config.csv
   #python $pth/fix_binary_type.py temp.cfg CONTCAR.relax2 $j ${proto[3]} $step ${els[@]}
   cat temp.cfg >> ../../${1}_dftrelaxed.cfg
   if [ "$save_outcars" = true ]; then
    if [[ "$j" =~ [0-9]+ ]]; then
     idx=${BASH_REMATCH[0]}
     idx=$((idx+1))
    fi
    ID=$(grep PRAPs-ID ../config${idx}.csv)
    if [[ "$ID" =~ [0-9]+ ]]; then
     ID=${BASH_REMATCH[0]}
    fi
    mv OUTCAR.relax2 $cmpd_pth/${1}_outcars/OUTCAR_${ID}_rx2
    mv OUTCAR.relax1 $cmpd_pth/${1}_outcars/OUTCAR_${ID}_rx1
   fi
   rm OUTCAR* LOC*
   break
  elif [ -f OUTCAR.relax1 ]; then
   #unxz OUTCAR.relax1.xz CONTCAR.relax1.xz
   mlp convert-cfg OUTCAR.relax1 temp.cfg --input-format=vasp-outcar
   step=$(grep BEGIN temp.cfg | wc -l)
   rm temp.cfg
   mlp convert-cfg OUTCAR.relax1 temp.cfg --input-format=vasp-outcar --last
   echo "Step is $step"
   proto=$(aflow --prototype_label < CONTCAR.relax1)
   proto=($proto)
   python $pth/utils/ID.py temp.cfg O els=$ELS source=$j car=CONTCAR.relax1 proto=${proto[3]} last=$step features=../${1}/config.csv
   #python $pth/fix_binary_type.py temp.cfg CONTCAR.relax1 $j ${proto[3]} $step ${els[@]}
   cat temp.cfg >> $cmpd_pth/${1}_dftrelaxed.cfg
   if [ "$save_outcars" = true ]; then
    if [[ "$j" =~ [0-9]+ ]]; then
     idx=${BASH_REMATCH[0]}
     idx=$((idx+1))
    fi
    ID=$(grep PRAPs-ID ../config${idx}.csv)
    if [[ "$ID" =~ [0-9]+ ]]; then
     ID=${BASH_REMATCH[0]}
    fi
    mv OUTCAR.relax1 $cmpd_pth/${1}_outcars/OUTCAR_${ID}_rx1
   fi
   rm OUTCAR* LOC*
   break
  else
   if [ $counter -gt 4 ]; then
    echo "Sorry. I couldn't relax $j after 5 tries. :( "
    break
   else
    counter=$((++counter))
    rm $cmpd_pth/chulls/${1}_work/*
    cd $cmpd_pth/chulls
    python $pth/utils/adjust_poscar_coords.py working_poscar
    cp working_poscar ./${1}_work/POSCAR
    cd ${1}_work
   fi
  fi
 done
 rm aflow* *.xz temp.cfg
 cd $cmpd_pth/chulls
done

echo '---- Final ----'
echo 'Current time is:'
date
