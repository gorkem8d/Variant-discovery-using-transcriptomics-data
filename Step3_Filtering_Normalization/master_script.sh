#!/bin/bash
#
# This script submits four jobs in sequence, where each job starts only after the previous one completes successfully.
# It uses SLURM job dependencies to create a pipeline workflow.
#
# Print header
echo "==================================================="
echo "RNA-Seq Variant Analysis Pipeline Submission Script"
echo "==================================================="
echo "Started at: $(date)"
echo

# Define the scripts to run in sequence
SCRIPT1="./check_coverage.sh"
SCRIPT2="./create_csv.sh"
SCRIPT3="./create_datasets.sh"
SCRIPT4="./coverage.sh"
SCRIPT5="./confidence.sh"

# Check if all required scripts exist
if [ ! -f "$SCRIPT1" ]; then
    echo "Error: $SCRIPT1 not found"
    exit 1
fi
if [ ! -f "$SCRIPT2" ]; then
    echo "Error: $SCRIPT2 not found"
    exit 1
fi
if [ ! -f "$SCRIPT3" ]; then
    echo "Error: $SCRIPT3 not found"
    exit 1
fi
if [ ! -f "$SCRIPT4" ]; then
    echo "Error: $SCRIPT4 not found"
    exit 1
fi
if [ ! -f "$SCRIPT5" ]; then
    echo "Error: $SCRIPT5 not found"
    exit 1
fi
# Make sure the scripts are executable
chmod +x $SCRIPT1 $SCRIPT2 $SCRIPT3 $SCRIPT4 $SCRIPT5

# Submit the first job (independent) and capture its job ID
echo "Submitting job 1: $SCRIPT1"
JOB1_ID=$(sbatch $SCRIPT1 | awk '{print $4}')
if [ -z "$JOB1_ID" ]; then
    echo "Error: Failed to submit $SCRIPT1"
    exit 1
fi
echo "Job 1 submitted with ID: $JOB1_ID"

# Submit the second job with dependency on the first job
echo "Submitting job 2: $SCRIPT2 (will start after job $JOB1_ID completes successfully)"
JOB2_ID=$(sbatch --dependency=afterok:$JOB1_ID $SCRIPT2 | awk '{print $4}')
if [ -z "$JOB2_ID" ]; then
    echo "Error: Failed to submit $SCRIPT2"
    exit 1
fi
echo "Job 2 submitted with ID: $JOB2_ID"

# Submit the third job with dependency on the second job
echo "Submitting job 3: $SCRIPT3 (will start after job $JOB2_ID completes successfully)"
JOB3_ID=$(sbatch --dependency=afterok:$JOB2_ID $SCRIPT3 | awk '{print $4}')
if [ -z "$JOB3_ID" ]; then
    echo "Error: Failed to submit $SCRIPT3"
    exit 1
fi
echo "Job 3 submitted with ID: $JOB3_ID"

# Submit the fourth job with dependency on the third job
echo "Submitting job 4: $SCRIPT4 (will start after job $JOB3_ID completes successfully)"
JOB4_ID=$(sbatch --dependency=afterok:$JOB3_ID $SCRIPT4 | awk '{print $4}')
if [ -z "$JOB4_ID" ]; then
    echo "Error: Failed to submit $SCRIPT4"
    exit 1
fi
echo "Job 4 submitted with ID: $JOB4_ID"

# Submit the fifth job with dependency on the fourth job
echo "Submitting job 5: $SCRIPT5 (will start after job $JOB4_ID completes successfully)"
JOB5_ID=$(sbatch --dependency=afterok:$JOB4_ID $SCRIPT5 | awk '{print $4}')
if [ -z "$JOB5_ID" ]; then
    echo "Error: Failed to submit $SCRIPT5"
    exit 1
fi
echo "Job 5 submitted with ID: $JOB5_ID"

# Print summary of the job chain
echo
echo "==================================================="
echo "Job Pipeline Summary:"
echo "==================================================="
echo "Job 1: $SCRIPT1 (ID: $JOB1_ID)"
echo "Job 2: $SCRIPT2 (ID: $JOB2_ID, depends on Job 1)"
echo "Job 3: $SCRIPT3 (ID: $JOB3_ID, depends on Job 2)"
echo "Job 4: $SCRIPT4 (ID: $JOB4_ID, depends on Job 3)"
echo "Job 5: $SCRIPT5 (ID: $JOB5_ID, depends on Job 4)"
echo
echo "To check the status of these jobs, run:"
echo "  squeue -u $USER"
echo
echo "To cancel the entire pipeline, run:"
echo "  scancel $JOB1_ID $JOB2_ID $JOB3_ID $JOB4_ID $JOB5_ID"
echo
echo "Pipeline submission completed at: $(date)"
echo "==================================================="