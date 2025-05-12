#!/bin/bash

#SBATCH --job-name=process_coverage
#SBATCH --output=process_coverage_%j.out
#SBATCH --error=process_coverage_%j.err
#SBATCH --time=12:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1


# Print job info
echo "Job started at $(date)"
echo "Running on host: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"

# Load any required modules (modify as needed for your environment)
# module load python/3.11

# Activate virtual environment if needed
# source /path/to/your/venv/bin/activate

# Set directory variables
BASE_PATH="/work/project/ext_016/RNA-Seq-Variant-Calling_1"
SCRIPT_PATH="./coverage.py"

# Run the script
echo "Starting coverage processing..."
python ${SCRIPT_PATH} --base-path ${BASE_PATH} --dirs source_dir source_dir_4 source_dir_6

# Check exit status
if [ $? -eq 0 ]; then
    echo "Job completed successfully at $(date)"
else
    echo "Job failed at $(date)"
    exit 1
fi

exit 0