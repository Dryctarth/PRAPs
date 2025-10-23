#!/bin/bash -l
pth=/projects/academic/ezurek/josiah/MLIP

#Note: This script expects to be run inside $cmpd_pth (the working directory).
. inpraps.sh
Nels=${#els[@]}
declare -A CHULLS=( [DFT]=lowE_vasp.cfg [RR]=lowE_robust_relaxed.cfg [ALS_AP_RR]=ALS_AP_RR.cfg [ALS_AP_v]=ALS_AP_v.cfg [ALS_AR_RR]=ALS_AR_RR.cfg )

for i in DFT RR ALS_AP_RR ALS_AP_v ALS_AR_RR
do
 if [ ! -f ${CHULLS[$i]} ]; then
  echo "You are missing ${CHULLS[$i]}. I cannot make those plots. Please re-generate and try again, or run PRAPs at CHK=4."
  continue
 fi
 if [ $Nels -eq 3 ]; then
  python $pth/utils/tri_phase_points2.py M ${CHULLS[$i]} ${i}_chullcans ${els[@]}
  python $pth/utils/trivex_masashi.py ${i}_chullcans.csv svg
  bash $pth/utils/config_summary.sh ${i}_chullcans_mapped.cfg
  if [ -f ${i}_dftrelaxed.cfg ]; then
   python $pth/utils/tri_phase_points2.py M ${i}_dftrelaxed.cfg ${i}_dftrelaxed ${els[@]}
   python $pth/utils/trivex_masashi.py ${i}_dftrelaxed.csv svg
  fi
  if [ -f ${i}_dftrx+DFT.cfg ]; then
   python $pth/utils/tri_phase_points2.py M ${i}_dftrx+DFT.cfg ${i}_dftrx+DFT ${els[@]}
   python $pth/utils/trivex_masashi.py ${i}_dftrx+DFT.csv svg
   bash $pth/utils/config_summary.sh ${i}_dftrx+DFT_mapped.cfg
  fi
 elif [ $Nels -lt 3 ]; then
  python $pth/utils/make_2D_hulls.py ${CHULLS[$i]} ${els[@]} ${i}_chullcans.svg
  if [ -f ${i}_dftrelaxed.cfg ]; then
   python $pth/utils/make_2D_hulls.py ${i}_dftrelaxed.cfg ${els[@]} ${i}_dftrelaxed.png
  fi
  if [ -f ${i}_dftrx+DFT.cfg ]; then
   python $pth/utils/make_2D_hulls.py ${i}_dftrx+DFT.cfg ${els[@]} ${i}_dftrx+DFT.png
  fi
 fi
done

