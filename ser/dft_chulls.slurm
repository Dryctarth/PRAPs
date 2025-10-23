#!/bin/bash -l
#SBATCH --nodes=1 --ntasks-per-node=12 --mem=187000
#SBATCH --time=2:00:00
#SBATCH --job-name=JOB --output=job.out
#SBATCH --account=ezurek      
#SBATCH --clusters=faculty --partition=ezurek --qos=ezurek
##SBATCH --constraint=CPU-Gold-6330
#SBATCH --mail-user=josiahro@buffalo.edu --mail-type=ALL
#SBATCH --exclusive
#SBATCH --requeue
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

echo '---- Loading Dependencies ----'
module purge
module use /projects/academic/ezurek/software/projectmodules/
module load gcccore/11.2.0 gcc/11.2.0 openmpi/4.1.1
module load mlip2 aflow3.2.14
module load python/3.9.6 scipy-bundle/ matplotlib/3.4.3
source /user/josiahro/Python/bin/activate

ulimit -s unlimited
#export I_MPI_PMI_LIBRARY=/usr/lib64/libpmi.so
export I_MPI_PMI_LIBRARY=/opt/software/slurm/lib64/libpmi.so
export vasp="/projects/academic/ezurek/software/vasp6.4.2/vasp.6.4.2/bin/vasp_std"

bash dft_chulls_p.sh $1

