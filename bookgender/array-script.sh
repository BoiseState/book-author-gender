#!/bin/sh

#SBATCH --array=1-{{nparts}}
#SBATCH --output={{work_dir}}/run-%a.out

ulimit -v unlimited
ulimit -u 2048
export NUMBA_NUM_THREADS=$SLURM_CPUS_ON_NODE
export LK_NUM_PROCS=$SLURM_CPUS_ON_NODE

srun invoke sweep-step "{{work_dir}}" $SLURM_ARRAY_TASK_ID
