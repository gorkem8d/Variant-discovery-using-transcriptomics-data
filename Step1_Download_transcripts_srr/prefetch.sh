#!/bin/bash
# Define the output directory
output_dir="/work/project/ext_016/RNA-Seq-Variant-Calling_1/source_dir_6/demo_data"

# Check if output directory exists, create only if it doesn't exist
if [ ! -d "$output_dir" ]; then
    mkdir -p "$output_dir"
    echo "Created output directory: $output_dir"
else
    echo "Output directory already exists: $output_dir"
fi

# Maximum number of parallel prefetch jobs
max_jobs=10
while IFS= read -r accession; do
  # Start prefetch in the background
  ./sratoolkit.3.0.5-centos_linux64/bin/prefetch "$accession" -O "$output_dir" &
  # Ensure that the number of background jobs does not exceed max_jobs
  while true; do
    # Check the number of currently running background jobs
    joblist=($(jobs -p))
    if [[ ${#joblist[@]} -lt max_jobs ]]; then
      break  # Exit the loop if we are below the job limit
    fi
    sleep 1  # Sleep for 1 second to prevent excessive CPU usage by this loop
  done
done < SRR_Acc_List.txt
# Wait for all background jobs to finish
wait