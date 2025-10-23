#!/bin/bash -l

pth=/projects/academic/ezurek/josiah/MLIP
MTPth=/projects/academic/ezurek/software/mlip-2-master/untrained_mtps
potpth=/projects/academic/ezurek/vasp-potcars/potpaw_PBE
echo "---- Plan for Robust and Accurate Potentials ----"
echo "\"PRAPs it'll work and PRAPs it won't.\""
echo "Maintained by Josiah Roberts, Eva Zurek Group, University of Buffalo, 2022"

echo '---- Output SLURM Environment Variables ----'
echo 'SLURM_JOB_ACCOUNT    '$SLURM_JOB_ACCOUNT
echo 'SLURM_JOB_ID         '$SLURM_JOBID
echo 'SLURM_JOB_NODELIST   '$SLURM_JOB_NODELIST
echo 'SLURM_SUBMIT_DIR     '$SLURM_SUBMIT_DIR
echo 'SLURM_SUBMIT_HOST    '$SLURM_SUBMIT_HOST

#The input file should be the first (and only?) argument.
if [ -z ${1+x} ]; then
 echo "You forgot the inpraps file."
 exit
fi
if [ ! -f $1 ]; then
 echo "No inpraps file found. Exiting before I make a mess."
 exit
fi
. $1
#Assigning variables from input.
Nels=${#els[@]}
cmpd=""
for i in ${els[@]}; do
 cmpd+=$i
done
#Get any special pathing, check-and-fix if the directory exists and if the .cfg files are in there.
if [ -z ${cmpd_pth+x} ]; then
 cmpd_pth=$pth/$cmpd
fi
if [ ! -d $cmpd_pth ]; then
 mkdir $cmpd_pth
fi
if [ ! -z ${DFT_CFG+x} ]; then
 if [ ! -e $cmpd_pth/$DFT_CFG ]; then
  mv $DFT_CFG $cmpd_pth/$DFT_CFG
 fi
 python $pth/utils/ID.py $cmpd_pth/$DFT_CFG I prefix=DFT
 cp $cmpd_pth/$DFT_CFG $cmpd_pth/relax.cfg
fi
if [ ! -z ${URX_CFG+x} ]; then
 if [ ! -e $cmpd_pth/$URX_CFG ]; then
  mv $URX_CFG $cmpd_pth/$URX_CFG
 fi
 python $pth/utils/ID.py $cmpd_pth/$URX_CFG I prefix=URX
 cat $cmpd_pth/$URX_CFG >> $cmpd_pth/relax.cfg
fi
if [[ -z ${DFT_CFG+x} && -z ${URX_CFG+x} ]]; then
 echo "You must specify either DFT_CFG or URX_CFG in the inpraps file. Exiting."
 exit
fi
if [ ! -z ${REF_CFG+x} ]; then
 if [ ! -e $cmpd_pth/$REF_CFG ]; then
  mv $REF_CFG $cmpd_pth/$REF_CFG
 fi
 python $pth/utils/ID.py $cmpd_pth/$REF_CFG I prefix=REF
fi

#Now that the path is set up and the .cfg files are inside, go in and continue setup.
if [ ! -e inpraps.sh ]; then
 cp $1 ./inpraps.sh
fi
cd $cmpd_pth
echo "Entering $cmpd_pth"
. ./inpraps.sh
if [ -z ${mindist+x} ]; then
 mindist=1.1
fi
if [ -z ${maxdist+x} ]; then
 maxdist=3.1
fi
#python $pth/utils/ID.py $DFT_CFG I prefix=DFT
#python $pth/utils/ID.py $REF_CFG I prefix=REF
#cp $DFT_CFG relax.cfg
#if [ -n $URX_CFG ]; then
 #python $pth/utils/ID.py $URX_CFG I prefix=URX
 #cat $URX_CFG >> relax.cfg
#fi
if [ -z ${training_setting+x} ]; then
 training_settings=""
fi
#mlp mindist relax.cfg
mind=$(mlp mindist relax.cfg)
mind=($mind)
echo "Filtering relax.cfg."
python $pth/utils/filter.py D relax.cfg relax.cfg ${mind[-1]} $mindist $maxdist
if [ -z ${filter_volumes+x} ]; then
 filter_volumes=false
fi
if [ -z ${filter_trajectories+x} ]; then
 filter_trajectories=false
fi
if [ "$filter_volumes" = true ]; then
 if [ -z ${volume_scaling+x} ]; then
  volume_scaling=0.25
 fi
 python $pth/utils/filter.py V relax.cfg relax.cfg $volume_scaling
 python $pth/utils/filter.py V $DFT_CFG dft_volfilt.cfg $volume_scaling
 DFT_FILT=dft_volfilt.cfg
else
 mind=$(mlp mindist $DFT_CFG)
 mind=($mind)
 python $pth/utils/filter.py D $DFT_CFG dft_distfilt.cfg ${mind[-1]} $mindist $maxdist
 DFT_FILT=dft_distfilt.cfg
fi
if [ -z ${filter_forces+x} ]; then
 filter_forces=0
elif (( $filter_forces == 0 )); then
 continue
else
 python $pth/utils/filter.py F $DFT_FILT $DFT_FILT $filter_forces
fi
cfg="relax.cfg"
if [ -z ${chull_var+x} ]; then
 chull_var=0.05
fi
if [ -z ${CHK+x} ]; then
 CHK=0
 echo "CHK=0" >> inpraps.sh
fi
if [ -z ${CHULL+x} ]; then
 CHULL=false
fi
mind=$(mlp mindist ${DFT_FILT})
M=($mind)
mind="Global mindist ${M[-1]}"
echo "Mindist is $mind"
#This sets up the MTP file
rm curr.mtp
cp $MTPth/${LevMTP}.mtp ./.
python $pth/utils/insert_mindist.py ${LevMTP}.mtp ${mind} ${Nels}


echo "---- Arguments ----"
echo "DFT Configs = ${DFT_CFG}; a dataset with DFT EFS values, used for pre-training."
echo "The DFT set has been filtered for low-quality compounds as ${DFT_FILT}."
if [ -n $URX_CFG ]; then 
 echo "Unrelaxed configs = ${URX_CFG}; a dataset without DFT EFS values, used for active learning."
fi
echo "Level = ${LevMTP}; the level of MTP training."
echo "Elements = ${els[@]}; the elements in ${cmpd}."
echo "Training will happen in ${cmpd_pth}."
echo "The convex hull variance is ${chull_var} eV."
echo "The checkpoint tag is ${CHK}."
echo "The minimum mindist is ${mindist} and the maximum mindist is ${maxdist}."
echo "Volume filtration is set to ${filter_volumes}."
echo "Relaxation trajectory filtration is set to ${filter_trajectories}."

echo '---- Initial Time ----'
echo 'Current time is:'
date

if [ $CHK -lt 1 ]; then
 echo "-- Pre-training Lev${LevMTP} MTP --"
 echo "Pre-training using a filtered $DFT_CFG"
 ncfgs=$(grep BEGIN ${DFT_FILT} | wc -l)
 echo "$ncfgs found in ${DFT_FILT}"
 mkdir 1 2 3 4 5
 for i in 1 2 3 4 5
 do
  cd $i
  if [ -f post_${LevMTP}_${i}.cfg ]; then
   echo "Sub-directory $i has already finished, moving on."
   if [ ! -f highlow.csv ]; then
    python $pth/utils/lowE_configs.py post_${LevMTP}_${i}.cfg lowout.cfg H ${chull_var}
   fi
   cd ..
   continue
  fi
  echo "Pre-training sub-directory $PWD"
  echo "Time Start:"
  date
  cp ../${LevMTP}.mtp ./.
  #Make testing and training set, do basic training.
  python $pth/utils/test_train.py ../${DFT_FILT} train.cfg test.cfg validate.cfg $ncfgs
  #This while loop is supposed to detect whether or not the training converged, and re-try if it hasn't.
  srun mlp train ${LevMTP}.mtp train.cfg --trained-pot-name=pot_${LevMTP}_${cmpd}.mtp --valid-cfgs=test.cfg ${training_settings}> training.out
  retrain=$(python $pth/utils/how_did_training_end.py training.out)
  while true
  do
   if $retrain; then 
    echo "Pre-training in $i is finished."
    break
   else
    echo "Pre-training (Basic) in $i not converged, trying again."
    srun mlp train pot_${LevMTP}_${cmpd}.mtp train.cfg --trained-pot-name=pot_${LevMTP}_${cmpd}.mtp --valid-cfgs=test.cfg ${training_settings} > training.out
    retrain=$(python $pth/utils/how_did_training_end.py training.out)
   rm training.out
   fi
  done
  echo "Finished Pre-training (Basic), getting various errors and analyses."
  mlp calc-errors pot_${LevMTP}_${cmpd}.mtp validate.cfg > err_${LevMTP}_${i}.txt
  mlp calc-errors pot_${LevMTP}_${cmpd}.mtp train.cfg >> err_${LevMTP}_${i}.txt
  mlp calc-efs pot_${LevMTP}_${cmpd}.mtp ../${DFT_FILT} post_${LevMTP}_${i}.cfg
  python $pth/utils/ID.py post_${LevMTP}_${i}.cfg I suffix=PreP
  python $pth/utils/lowE_configs.py post_${LevMTP}_${i}.cfg lowout.cfg.cfg H $chull_var
  echo "Time Done:"
  date
  cd ..
 done
 CHK=1
 echo "CHK=1" >> inpraps.sh
 #lowE_vasp.cfg contains the DFT convex hull, very important.
 python $pth/utils/lowE_configs.py ${DFT_FILT} lowE_vasp.cfg F $chull_var
 python $pth/utils/lowE_configs.py lowE_vasp.cfg lowout.cfg H #Duplicate to get correct highlow data and name.
 python $pth/utils/lowE_configs.py lowE_vasp.cfg lowout.cfg H #Need to get lowE_vasp into the highlow for later
 best=$(python $pth/utils/select_good_pot.py $LevMTP $cmpd $cmpd_pth)
 echo "Analysis of basic training done. The best potential is in sub-dir $best"
 cp ./$best/pot_${LevMTP}_${cmpd}.mtp ./.
 cp ./$best/train.cfg ./.
 mlp calc-errors pot_${LevMTP}_${cmpd}.mtp train.cfg >> err_train_${LevMTP}.txt
 #This is the convex hull generated by using the best basic-trained MTP on DFT_CFG.
 python $pth/utils/lowE_configs.py ./$best/post_${LevMTP}_${best}.cfg lowout.cfg H $chull_var
 #rm ./1/highlow.csv ./2/highlow.csv ./3/highlow.csv ./4/highlow.csv ./5/highlow.csv
else
 echo "Checkpoint tag $CHK found, skipping Pre-training step. Some setup still required."
 if [ ! -f pot_${LevMTP}_${cmpd}.mtp ]; then
  echo "PRAPs did not find a pre-trained MTP. The RP training will begin with an untrained MTP."
  cp $MTPth/${LevMTP}.mtp pot_${LevMTP}_${cmpd}.mtp
  python $pth/utils/insert_mindist.py pot_${LevMTP}_${cmpd}.mtp ${mind} ${Nels}
 fi
 if [ ! -f train.cfg ]; then
  echo "PRAPs did not find a pre-training set. The RP training will begin with an empty training set."
  touch train.cfg
 fi
 echo "Setting up lowE_vasp.cfg and the initial highlow data."
 python $pth/utils/lowE_configs.py ${DFT_FILT} lowE_vasp.cfg F $chull_var
 python $pth/utils/lowE_configs.py ${DFT_FILT} lowout.cfg H #Duplicate to get correct highlow data and name.
 python $pth/utils/lowE_configs.py lowE_vasp.cfg lowout.cfg H #Need to get lowE_vasp into the highlow for later
fi

if [ $CHK -lt 2 ]; then
 echo "-- ALS Robust MTP --"
 echo "Time Start:"
 date
 #Starting with a pre-generated training set is faster and more robust.
 if [ ! -f als-train.cfg ]; then
  cp train.cfg als-train.cfg
 fi
 cp $pth/ser/active_learning.sh ./.
 cp $pth/ser/mlip.ini ./.
 #See comments in active_learning.sh
 if [ -f curr.mtp ]; then
  bash active_learning.sh curr.mtp train.cfg ${cfg} ${els[@]}
 else
  bash active_learning.sh pot_${LevMTP}_${cmpd}.mtp train.cfg ${cfg} ${els[@]}
 fi
 CHK=2
 echo "CHK=2" >> inpraps.sh
 mv als-train.cfg als-robust.cfg
 mv pot_als_done.mtp pot_als_robust.mtp
 echo "ALS Robust finished training."
 #Now use ALS_RP to predict all relax.cfg EFS and get the associated convex hull.
 mlp calc-efs pot_als_robust.mtp ${cfg} post_als_robust.cfg
 python $pth/utils/ID.py post_als_robust.cfg I suffix=RP
 mlp calc-efs pot_als_robust.mtp ${DFT_FILT} post_filt_als_robust.cfg
 python $pth/utils/ID.py post_filt_als_robust.cfg I suffix=RP
 python $pth/utils/lowE_configs.py post_filt_als_robust.cfg lowout.cfg H $chull_var
 rm post_filt_als_robust.cfg
 mlp calc-errors pot_als_robust.mtp als-robust.cfg >> err_train_${LevMTP}.txt
 mlp calc-errors pot_als_robust.mtp $DFT_CFG >> err_predict_${LevMTP}.txt
 mlp calc-errors pot_als_robust.mtp $DFT_FILT >> err_predict_${LevMTP}.txt
 echo "Analysis finished. ALS-Robust predictions added to highlow.csv."
 echo "Time Done:"
 date
else
 echo "Checkpoint tag $CHK found, skipping ALS Robust step."
fi

if [ $CHK -lt 3 ]; then
 echo "-- Basic Accurate MTP --"
 echo "Time Start:"
 date
 cp $pth/ser/accurate_potentials.sh ./.
 #See comments in accurate_potentials.sh
 bash accurate_potentials.sh ${cfg} $cmpd $chull_var $LevMTP
 CHK=3
 echo "CHK=3" >> inpraps.sh
 echo "Training finished. Robust-Relaxed added to highlow.csv."
 #The convex hull from relaxing relax.cfg with ALS_RP is in lowE_robust_relaxed,
 #This duplicates for the correct name of the highlow data.
 python $pth/utils/lowE_configs.py lowE_robust_relaxed.cfg lowout.cfg H
 rm lowout.cfg 
 #Two things happen here: use the Basic_AP to predict the convex hull candidates from Robust_Relaxed,
 #and use the Basic_AP to predict the convex hull from DFT_CFG.
 #Note to me old --> new nomenclature: 
  #lowE_post_basic_acc_mtp ==> Bas_AP_RR
  #lowE_post_basic_acc_vasp ==> Bas_AP_v
 if [ "$basic_acc" = true ]; then
  mlp calc-efs pot_basic_acc.mtp lowE_robust_relaxed.cfg post_basic_acc_mtp.cfg
  python $pth/utils/ID.py post_basic_acc_mtp.cfg I suffix=bAP
  python $pth/utils/lowE_configs.py post_basic_acc_mtp.cfg Bas_AP_RR.cfg B $chull_var
  mlp calc-efs pot_basic_acc.mtp lowE_vasp.cfg post_basic_acc_vasp.cfg
  python $pth/utils/ID.py post_basic_acc_vasp.cfg I suffix=bAP
  python $pth/utils/lowE_configs.py post_basic_acc_vasp.cfg Bas_AP_v.cfg B $chull_var
  mlp calc-errors pot_basic_acc.mtp lowE_robust_relaxed.cfg >> err_train_${LevMTP}.txt
  mlp calc-errors pot_basic_acc.mtp lowE_robust_relaxed.cfg >> err_predict_${LevMTP}.txt
  mlp calc-errors pot_basic_acc.mtp $DFT_FILT >> err_predict_${LevMTP}.txt
 fi
 echo "Analysis finished. Basic-Acc predictions added to highlow.csv."
 echo "Time Done:"
 date
else
 echo "Checkpoint tag $CHK found, skipping Robust Relaxation and Basic Accurate step."
fi

if [ $CHK -lt 4 ]; then
 echo "-- ALS Accurate MTP --"
 echo "Time Start:"
 date
 #Start the ALS_AP from an empty set since the relaxation set is so much smaller. 
 touch als-train.cfg
 bash active_learning.sh pot_${LevMTP}_${cmpd}.mtp train.cfg lowE_robust_relaxed.cfg ${els[@]}
 CHK=4
 echo "CHK=4" >> inpraps.sh
 echo "ALS Accurate finished training."
 mv als-train.cfg als-acc.cfg
 mv pot_als_done.mtp pot_als_acc.mtp
 #Two things happen here: Use ALS_AP to get convex hull candidates from Robust_Relaxed and DFT_CFG.
 #Note to me old --> nomenclature:
  #lowE_post_als_acc_mtp ==> ALS_AP_RR
  #lowE_post_als_acc_vasp ==> ALS_AP_v
 mlp calc-efs pot_als_acc.mtp lowE_robust_relaxed.cfg post_als_acc_mtp.cfg
 python $pth/utils/ID.py post_als_acc_mtp.cfg I suffix=AP
 python $pth/utils/lowE_configs.py post_als_acc_mtp.cfg ALS_AP_RR.cfg B $chull_var
 mlp calc-efs pot_als_acc.mtp lowE_vasp.cfg post_als_acc_vasp.cfg
 python $pth/utils/ID.py post_als_acc_vasp.cfg I suffix=AP
 python $pth/utils/lowE_configs.py post_als_acc_vasp.cfg ALS_AP_v.cfg B $chull_var
 mlp calc-errors pot_als_acc.mtp als-acc.cfg >> err_train_${LevMTP}.txt
 mlp calc-errors pot_als_acc.mtp lowE_robust_relaxed.cfg >> err_predict_${LevMTP}.txt
 mlp calc-errors pot_als_acc.mtp $DFT_FILT >> err_predict_${LevMTP}.txt
 echo "Analysis finished. ALS-ACC predictions added to highlow.csv."
 echo "Accurate Potential Relaxation."
 cp pot_als_acc.mtp curr.mtp
 mlp calc-grade curr.mtp als-acc.cfg lowE_robust_relaxed.cfg delme --als-filename=state.als
 rm delme
 mlp relax mlip.ini --cfg-filename=lowE_robust_relaxed.cfg --save-relaxed=rx.cfg --min-dist=$mindist $relax_settings
 for i in rx.cfg_*
 do
  cat $i >> ALS_AR_RR.cfg
 done
 rm rx.cfg* preselected* state.als
 python $pth/utils/ID.py ALS_AR_RR.cfg IR suffix=-AR
 echo "Relaxation done."
 echo "Time Done:"
 date
else
 echo "Checkpoint tag $CHK found; skipping ALS Accurate step."
fi

#Note, if $CHK = 4 or higher, then we go straight here, to the analysis portion.
echo "Beginning PRAPs Analysis"
if [ ! -f ALS_AP_RR.cfg ]; then
 mlp calc-efs pot_als_acc.mtp lowE_robust_relaxed.cfg post_als_acc_mtp.cfg
 python $pth/utils/ID.py post_als_acc_mtp.cfg I suffix=AP
 python $pth/utils/lowE_configs.py post_als_acc_mtp.cfg ALS_AP_RR.cfg B $chull_var
fi
if [ ! -f ALS_AP_v.cfg ]; then
 mlp calc-efs pot_als_acc.mtp lowE_vasp.cfg post_als_acc_vasp.cfg
 python $pth/utils/ID.py post_als_acc_vasp.cfg I suffix=AP
 python $pth/utils/lowE_configs.py post_als_acc_vasp.cfg ALS_AP_v.cfg B $chull_var
fi
if [ ! -z ${REF_CFG+x} ]; then
 mkdir $cmpd_pth/chulls
 mkdir $cmpd_pth/chulls/refs $cmpd_pth/chulls/aflow
 cd $cmpd_pth/chulls
 bash $pth/ser/dft_chulls.sh refs
 rm refs_DONE
 cd $cmpd_pth
 if [ ! -f refs_RR.cfg ]; then
  echo "Relaxing $REF_CFG with RP."
  cp pot_als_robust.mtp curr.mtp
  mlp calc-grade pot_als_robust.mtp als-robust.cfg $REF_CFG out.cfg --als-filename=state.als
  mlp relax mlip.ini --cfg-filename=$REF_CFG --save-relaxed=rx.cfg --min-dist=$mindist $relax_settings
  for i in rx.cfg_*
  do
   cat $i >> refs_RR.cfg
  done
  rm rx.cfg_*
  python $pth/utils/ID.py refs_RR.cfg IR suffix=RR
  echo "Making refs_AP_RR.cfg."
  mlp calc-efs pot_als_acc.mtp refs_RR.cfg refs_AP_RR.cfg
  python $pth/utils/ID.py refs_AP_RR.cfg I suffix=AP
  rm out.cfg curr.mtp state.als prese*
 fi
 if [ ! -f refs_AR.cfg ]; then
  echo "Relaxing refs_RR.cfg with AR."
  cp pot_als_acc.mtp curr.mtp
  mlp calc-grade curr.mtp als-acc.cfg refs_RR.cfg out.cfg --als-filename=state.als
  mlp relax mlip.ini --cfg-filename=$REF_CFG --save-relaxed=rx.cfg --min-dist=$mindist $relaxation_settings
  for i in rx.cfg_*
  do
   cat $i >> refs_AR.cfg
  done
  rm rx.cfg_*
  python $pth/utils/ID.py refs_AR.cfg IR suffix=AR
  rm out.cfg curr.mtp state.als prese*
 fi
fi
#I might add this section back in via an optional input tag.
#for i in lowE_vasp.cfg lowE_robust_relaxed.cfg ALS_AP_RR.cfg ALS_AP_v.cfg
#do #This filters the lowE configs by Hf to keep only configs with negative Hf
# python $pth/lowE_configs.py $i $i F Hf ${els[@]}
#done
if [ $Nels -eq 3 ]; then
 echo "Generating ternary phase diagrams prior to DFT relaxation."
 python $pth/utils/tri_phase_points2.py M lowE_vasp.cfg DFT_chullcans ${els[@]}
 python $pth/utils/tri_phase_points2.py M lowE_robust_relaxed.cfg RR_chullcans ${els[@]}
 python $pth/utils/tri_phase_points2.py M ALS_AP_RR.cfg ALS_AP_RR_chullcans ${els[@]}
 python $pth/utils/tri_phase_points2.py M ALS_AP_v.cfg ALS_AP_v_chullcans ${els[@]}
 python $pth/utils/tri_phase_points2.py M ALS_AR_RR.cfg ALS_AR_RR_chullcans ${els[@]}
 for i in DFT RR ALS_AP_RR ALS_AP_v ALS_AR_RR
 do
  python $pth/utils/trivex_masashi.py ${i}_chullcans.csv svg
  bash $pth/utils/config_summary.sh ${i}_chullcans_mapped.cfg
  #mv cfg_summary.csv ${i}_chullcans_summary.csv
 done
elif [ $Nels -lt 3 ]; then
 echo "Generating binary convex hulls prior to DFT relaxation."
 python $pth/utils/make_2D_hulls.py lowE_vasp.cfg ${els[@]} DFT_chullcans.svg
 python $pth/utils/make_2D_hulls.py lowE_robust_relaxed.cfg ${els[@]} RR_chullcans.svg
 python $pth/utils/make_2D_hulls.py ALS_AP_RR.cfg ${els[@]} ALS_AP_RR_chullcans.svg
 python $pth/utils/make_2D_hulls.py ALS_AP_v.cfg ${els[@]} ALS_AP_v_chullcans.svg
 python $pth/utils/make_2D_hulls.py ALS_AR_RR.cfg ${els[@]} ALS_AR_RR_chullcans.svg
 #python $pth/utils/make_2D_hulls.py $DFT_FILT.cfg ./$best/post_${LevMTP}_${best}.cfg ${els[@]} post_${LevMTP}.png
 #python $pth/utils/make_2D_hulls.py ${cfg} post_als_robust.cfg ${els[@]} post_als_robust_${LevMTP}.png
 #python $pth/utils/make_2D_hulls.py lowE_vasp.cfg lowE_robust_relaxed.cfg ${els[@]} post_relaxed_${LevMTP}.png
 #python $pth/utils/make_2D_hulls.py lowE_vasp.cfg post_basic_acc_vasp.cfg post_als_acc_vasp.cfg ${els[@]} post_acc_vasp_${LevMTP}.png
 #python $pth/utils/make_2D_hulls.py lowE_mtp.cfg post_basic_acc_mtp.cfg post_als_acc_mtp.cfg ${els[@]} post_acc_mtp_${LevMTP}.png
fi
mv highlow.csv highlow_${LevMTP}.csv

if [ "$CHULL" = true ]; then
 #Compare convex hull structures here using aflow.
 echo "Examining Convex Hulls from MLIP and DFT."
 echo "Please ignore any Python-highlow-related error messages."
 mkdir chulls
 cd $cmpd_pth/chulls
 mkdir DFT RR ALS_AP_RR ALS_AP_v ALS_AR_RR
 #declare -A CHULLS=( [DFT]=lowE_vasp.cfg [RR]=lowE_robust_relaxed.cfg [ALS_AP_RR]=ALS_AP_RR.cfg [ALS_AP_v]=ALS_AP_v.cfg [ALS_AR]=ALS_AR.cfg )
 #We grab all chull candidates, not just minimal-E configs, for relaxation.
 #RR_chull is result of using ALS_RP on relax.cfg.
 #ALS_AP_RR_chull is result of using ALS_AP on RR.
 #ALS_AP_v_chull is a check to see if ALS_AP can reproduce DFT results.
 
 #Now we turn the chull candidates into POSCARs
 #Next, we run through all the chull candidates and relax them with DFT via AFLOW.
 #Note that we include the DFT_chullcans from lowE_vasp because we know lowE_vasp contains mid-relaxed structures.
 for i in DFT RR ALS_AP_RR ALS_AP_v ALS_AR_RR
 do
  sbatch $pth/dft_chulls_p.slurm $i --output=dft_${i}.out
 done
 while true
 do
  sleep 20m
  check=$(ls *DONE | wc -l)
  if [ $check -eq 5 ]; then
   rm *DONE
   break
  fi
 done
 cd $cmpd_pth
 
 echo Make _dftrelaxed plots and _dftrx+DFT plots
 #The first is the PRAPs-only convex hulls and the second is when we consider the configs in DFT_CFG as well.
 #Really, the dftrx+DFT are more important, but the others are included for the user's discretionary use.
 #Actually, first we do the DFT_dftrelaxed plot and get those vertices and make them into POSCARs.
 if [ $Nels -eq 3 ]; then
  python $pth/utils/tri_phase_points2.py M DFT_dftrelaxed.cfg DFT_dftrelaxed ${els[@]}
  python $pth/utils/trivex_masashi.py DFT_dftrelaxed.csv svg
 elif [ $Nels -lt 3 ]; then
  python $pth/utils/make_2D_hulls.py DFT_dftrelaxed.cfg ${els[@]} DFT_dftrelaxed.svg
 fi
 #Then we do plots for the others.
 for i in RR ALS_AP_RR ALS_AP_v ALS_AR_RR
 do
  if [ $Nels -eq 3 ]; then
   python $pth/utils/tri_phase_points2.py M ${i}_dftrelaxed.cfg ${i}_dftrelaxed ${els[@]}
   python $pth/utils/trivex_masashi.py ${i}_dftrelaxed.csv svg
   cp ${i}_dftrelaxed.cfg ${i}_dftrx+DFT.cfg
   cat DFT_dftrelaxed.cfg >> ${i}_dftrx+DFT.cfg
   python $pth/utils/tri_phase_points2.py M ${i}_dftrx+DFT.cfg "${i}_dftrx+DFT" ${els[@]}
   python $pth/utils/trivex_masashi.py "${i}_dftrx+DFT.csv" svg
   bash $pth/utils/config_summary.sh "${i}_dftrx+DFT_mapped.cfg"
  elif [ $Nels -lt 3 ]; then
   python $pth/utils/make_2D_hulls.py ${i}_dftrelaxed.cfg ${els[@]} ${i}_dftrelaxed.svg
   cp ${i}_dftrelaxed.cfg ${i}_dftrx+DFT.cfg
   cat DFT_dftrelaxed.cfg >> ${i}_dftrx+DFT.cfg
   python $pth/utils/make_2D_hulls.py ${i}_dftrx+DFT.cfg ${els[@]} "${i}_dftrx+DFT.svg"
  fi
  #Once the dftrx+DFT plots are made, we have the _dftrx+DFT_vertices.cfg and we want to match them against DFT_CFG.
  #This will tell us which structures are new to the hull, though not which, if any, vanished from the hull.
  #The code for this section was removed into xtalfinder.sh and summarize_xtalfinder.py.
 done
else
 echo "CHULL tag set to False. Skipping the post-training DFT relaxation and convex hull plotting."
fi

#Collect important files and clean up.
#rm lowE_post* post*
rm -r ./chulls/
cp pot_${LevMTP}_${cmpd}.mtp ./pots/.
cp pot_als_robust.mtp ./pots/pot_${LevMTP}_als_robust.mtp
cp pot_als_acc.mtp ./pots/pot_${LevMTP}_als_acc.mtp
mv $DFT_CFG ${DFT_CFG}.keep
mv $URX_CFG ${URX_CFG}.keep
mv $REF_CFG ${REF_CFG}.keep
tar -cf praps_${cmpd}_${LevMTP}.tar *.mtp *.cfg *.png highlow_${LevMTP}.csv err_*_${LevMTP}.txt inpraps.sh
rm pot* *.cfg bfgs.log inpraps.sh
mv ${DFT_CFG}.keep ${DFT_CFG}
mv ${URX_CFG}.keep ${URX_CFG}
mv ${REF_CFG}.keep ${REF_CFG}

echo '---- Final Time ----'
echo 'Current time is:'
date


