#!/bin/bash -l

pth=/projects/academic/ezurek/josiah/MLIP
potpth=/projects/academic/ezurek/vasp-potcars/potpaw_PBE
echo '---- SLURMscript for Vienna Ab-initio Simulation Package and MLIP Active Learning Integration ----'
echo 'Maintained by Josiah Roberts (josiahro@buffalo.edu)'
echo 'Eva Zurek group, University at Buffalo, Fall 2021'

echo '---- Output SLURM Environment Variables ----'
echo 'SLURM_JOB_ACCOUNT    '$SLURM_JOB_ACCOUNT
echo 'SLURM_JOB_ID         '$SLURM_JOBID
echo 'SLURM_JOB_NODELIST   '$SLURM_JOB_NODELIST
echo 'SLURM_SUBMIT_DIR     '$SLURM_SUBMIT_DIR
echo 'SLURM_SUBMIT_HOST    '$SLURM_SUBMIT_HOST

echo '---- Initial MLIP ----'
echo 'Current time is:'
date

. $PWD/inpraps.sh
MTP="$1"
Ref="$2"
Relax="$3"
els=()
Nels=$(($# - 3))
i=0
shift 3
while [ $i -lt $Nels ]
do
 els+=( $1 )
 i=$(($i + 1))
 shift 1
done
echo "Arguments:
 1 = ${MTP} = the .mtp file of interest
 2 = ${Ref} = the set of configs most originally used to train the initial MTP.
 3 = ${Relax} = the relaxation set
 4+ = ${els[@]} = the elements of interest
Run this in the directory with the various data, not the home directory.
Make sure to set up the training set as als-train.cfg before running, 
or else the script will create an empty training set.
"

if [ -z ${mindist+x} ]; then
 mindist=1.1
fi
if [ -z ${relax_settings+x} ]; then
 relax_settings=""
fi
if [ -z ${training_settings+x} ]; then
 training_settings=""
fi
if [ -z ${ALS_conv+x} ]; then
 ALS_conv=0
fi
if [ -z ${custom_relax+x} ]; then
 custom_relax=false
fi


echo "Active learning with ${MTP} and ${Relax} using elements ${els[@]}."
mkdir vaspy
cp $pth/ser/mlip.ini ./.
if [ ! -f curr.mtp ]; then
 cp $MTP curr.mtp
fi
sv_els='^(Li|K|Ca|Ti|V|Rb|Sr|Y|Zr|Nb|Mo|Cs|Ba|W|Fr|Ra)$'
pv_els='^(Na|Cr|Mn|Tc|Ru|Rh|Hf|Ta)$'
for i in ${els[@]}; do
 if [[ $i =~ $sv_els ]]; then
  cat $potpth/${i}_sv/POTCAR >> ./vaspy/POTCAR
 elif [[ $i =~ $pv_els ]]; then
  cat $potpth/${i}_pv/POTCAR >> ./vaspy/POTCAR
 else
  cat $potpth/$i/POTCAR >> ./vaspy/POTCAR
 fi
done
cp ./vaspy/POTCAR ./POTCAR
if [ "$custom_relax" = true ]; then
 cp $cmpd_pth/INCAR_st ./vaspy/INCAR
 cp $cmpd_pth/KPOINT_st ./vaspy/KPOINTS
else
 cp $pth/utils/INCAR_st ./vaspy/INCAR
 cp $pth/utils/KPOINTS ./vaspy/.
fi
if [ ! -f "als-train.cfg" ]; then
 touch als-train.cfg
fi

echo "Finished setup, beginning active learning."

#A Active set construction
if [ ! -f "state.als" ]; then
 mlp calc-grade curr.mtp ${Ref} als-train.cfg out.cfg --als-filename=state.als #fast, no need for slurm
 rm out.cfg #this info is stored in state.als, so remove the redundant one
 echo "Initialized Active Set."
fi
c=1
while true
do

#B Relax with MLIP
 echo "Rabbit Hole $c" #This helps you search through and count each iteration.
 #touch preselected.cfg
 mlp relax mlip.ini --cfg-filename=${Relax} --save-relaxed=out.cfg --min-dist=$mindist $relax_settings
 rm out.cfg_*
 mv preselected.cfg_0 preselected.cfg

#C Grade and select
 n_preselected=$(grep "BEGIN_CFG" preselected.cfg | wc -l)
 echo "MLIP Relaxation finished. $n_preselected configurations found."
 #Most of the ALS happens in this next if-elif statement, providing a built-in convergence criteria.
 #If there are no structures in preselected.cfg, an else down below breaks the while loop and stops the process
 if [ $n_preselected -gt 0 ]; then 
  mlp select-add curr.mtp als-train.cfg preselected.cfg diff.cfg --als-filename=state.als
  D=$(grep "BEGIN" diff.cfg | wc -l)
  echo "$D configurations selected for ab initio relaxation."
  cp diff.cfg ./vaspy/.
  rm preselected.cfg
  rm selected.cfg

#D Relax selected with DFT
  cd ./vaspy/
  mlp convert-cfg diff.cfg POSCAR --output-format=vasp-poscar
  RANGE=$(ls | grep 'POSCAR' | wc -l)
  for (( i=0; i<RANGE; i++ ))
  do
   python $pth/utils/insert_elements.py POSCAR${i} ${els[@]}
   python $pth/utils/extract_features.py diff.cfg POSCAR${i}
   mv POSCAR${i} POSCAR
   echo '---- Initial VASP ----'
   echo $i
   echo 'Current time is:'
   date
   ##################
   module load intel vasp6.4.2
   srun vasp
   module load gcc/11.2.0 openmpi/4.1.1
   #################
   echo '---- VASP Job Done ----'
   echo $i
   echo 'Current time is:'
   date
   mv OUTCAR OUTCAR${i}
  done

#E Merge and update training set
  echo "All VASP done. Updating training set."
  rm diff.cfg
  ELS=""
  for i in ${els[@]}
  do
   ELS+=$i
   ELS+=,
  done
  for i in ./OUTCAR*
  do
   name=$(basename $i)
   mlp convert-cfg $name ${name}.cfg --input-format=vasp-outcar
   python $pth/utils/ID.py ${name}.cfg O els=$ELS source=./ALS/${name} features=config.csv
   cat ${name}.cfg >> ../als-train.cfg
  done
  #find $PWD -name "OUTCAR*" -execdir srun -n 1 mlp convert-cfg '{}' '{}'.cfg --input-format=vasp-outcar ';'
  #find $PWD -name ".cfg" -execdir python $pth/ID.py '{}' O els=oops source=oops features=config.csv 
  #find $PWD -name "*.cfg" -execdir python ${pth}/insert_from_outcar.py '{}' ${els[@]} ';'
  #find $PWD -name "*.cfg" -execdir cat '{}' >> ../als-train.cfg ';'
  rm POSCAR* *.csv
  rm *.cfg
  rm OUTCAR*
  cd ..

#F Re-train MTP on new training set
  echo "Updating MTP."
  mlp train curr.mtp als-train.cfg --trained-pot-name=curr.mtp --update-mindist ${training_settings} > training.out
  retrain=$(python $pth/how_did_training_end.py training.out)
  while true
  do
   if $retrain; then
    echo "Re-training in Hole $c is finished."
    break
   else
    echo "Re-training in Hole $c not converged, trying again."
    mlp train curr.mtp als-train.cfg --trained-pot-name=curr.mtp --update-mindist ${training_settings} > training.out
    retrain=$(python $pth/how_did_training_end.py training.out)
   rm training.out
   fi
  done


#A Active set re-construction and loop
  echo "Updating active state and re-calculating grade."
  #mlp calc-grade curr.mtp als-train.cfg diff.cfg out.cfg --als-filename=state.als
  c=$((c +1))
  case $ALS_conv in #Tests the convergence criteria,
  #The answer to the question, "Should I stop yet?" is stored in $br and determined in als-conv.py
  #Note that $ALS_conv must be passed into als-conv.py so that the script knows how to parse the other vars.
  1) 
   #If N_diff < 1% of N_train
   diff=$(grep BEGIN diff.cfg | wc -l)
   train=$(grep BEGIN als-train.cfg | wc -l)
   br=$(python $pth/utils/als-conv.py $ALS_conv $diff $train);;
  2)
   #If RMSE < chull_var
   mlp calc-errors curr.mtp als-train.cfg > delme
   rmse=$(python $pth/utils/get_RMSE.py delme)
   br=$(python $pth/utils/als-conv.py $ALS_conv $rmse $chull_var)
   rm delme;;
  3)
   #If change in RMSE < 0.1 meV/atom
   mlp calc-errors curr.mtp als-train.cfg > delme
   if [ -z ${rmse+x} ]; then
    rmse=$(python $pth/utils/get_RMSE.py delme)
   else
    new_rmse=$(python $pth/utils/get_RMSE.py delme)
    br=$(python $pth/utils/als-conv.py $ALS_conv $rmse $new_rmse)
    rmse=$new_rmse
   fi
   rm delme;;
  4)
   #If at 50 iterations
   br=$(python $pth/utils/als-conv.py $ALS_conv $c);;
  *) br="False";; #If using default convergence criteria
  esac
  rm diff.cfg
  rm out.cfg
  echo "Iteration finished."
  if [ $br == "True" ]; then
   echo "PRAPs reached convergence criteria ${ALS_conv}, stopping active learning."
   break
  fi
 else #[ $n_preselected -eq 0 ] if there are no structures in preselected.cfg, default convergence criteria
  break
 fi
done

rm -r vaspy
rm preselect*
mv curr.mtp pot_als_done.mtp
rm state.als

echo '---- MLIP Job Done ----'
echo 'Current time is:'
date

