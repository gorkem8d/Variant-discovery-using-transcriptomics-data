#!/bin/bash

#SBATCH --job-name=count_mutations
#SBATCH --output=count_mutations_%j.out
#SBATCH --error=count_mutations_%j.err
#SBATCH --time=2:00:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1

# Print job info
echo "Job started at $(date)"
echo "Running on host: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"

# Set directory variables
BASE_PATH="/work/project/ext_016/RNA-Seq-Variant-Calling_1"
SCRIPT_PATH="./create_datasets.py"

# Run the script
echo "Starting mutation count analysis..."
python ${SCRIPT_PATH} --base-path ${BASE_PATH} --dirs source_dir source_dir_4 source_dir_6

# Check exit status
if [ $? -eq 0 ]; then
    echo "Job completed successfully at $(date)"
else
    echo "Job failed at $(date)"
    exit 1
fi

exit 0