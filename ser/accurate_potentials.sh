#!/bin/bash -l

pth=/projects/academic/ezurek/josiah/MLIP
echo '---- SLURMscript for Generation of MLIP Accurate Potentials ----'
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

echo "Args: ${1} is Relaxation Set. ${2} is compound. ${3} is chull variance. ${4} is level."
. $PWD/inpraps.sh

cp pot_als_robust.mtp curr.mtp
mlp calc-grade curr.mtp als-robust.cfg ${1} out.cfg --als-filename=state.als
if [ -z ${mindist+x} ]; then
 mindist=1.1
fi
if [ -z ${relax_settings+x} ]; then
 relax_settings=""
fi
if [ -z ${training_settings+x} ]; then 
 training_settings=""
fi
if [ -z ${filter_trajectories+x} ]; then
 filter_trajectories=false
fi
if [ "$filter_trajectories" = true ]; then
 mv ${1} full_relax.cfg
 python $pth/utils/filter.py T full_relax.cfg relax.cfg
fi
mlp relax mlip.ini --cfg-filename=relax.cfg --save-relaxed=relaxed.cfg --min-dist=$mindist $relax_settings
echo '---- Grading and Relaxation done ----'
date
mv relaxed.cfg_0 relaxed.cfg
python $pth/utils/ID.py relaxed.cfg R
python $pth/utils/lowE_configs.py relaxed.cfg lowE_robust_relaxed.cfg F $3
echo '---- Filtering done ----'
date
rm state.als out.cfg* curr.mtp relaxed.cfg
if [ "$basic_acc" = true ]; then
 "Performing Basic Training for Accurate Potential."
 mlp train pot_${4}_${2}.mtp lowE_robust_relaxed.cfg --trained-pot-name=pot_basic_acc.mtp ${training_settings}
 mlp calc-errors pot_basic_acc.mtp lowE_robust_relaxed.cfg
fi

echo '---- MLIP Done ----'
echo 'Current time is:'
date

