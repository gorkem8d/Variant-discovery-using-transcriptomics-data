#!/bin/bash

#SBATCH --job-name=confidence_calc
#SBATCH --output=confidence_calc_%j.out
#SBATCH --error=confidence_calc_%j.err
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4

# Print job information
echo "Job started at: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Running on node: $SLURM_NODELIST"


# Set the location of the python script
SCRIPT_DIR="/work/project/ext_016/RNA-Seq-Variant-Calling_1"
PYTHON_SCRIPT="./confidence.py"

# Create a log directory if it doesn't exist
mkdir -p ${SCRIPT_DIR}/logs

# Make sure the python script is executable
chmod +x ${PYTHON_SCRIPT}

echo "Starting confidence calculation script..."
python ${PYTHON_SCRIPT} > ${SCRIPT_DIR}/logs/confidence_calc_${SLURM_JOB_ID}.log 2>&1

echo "Job completed at: $(date)"