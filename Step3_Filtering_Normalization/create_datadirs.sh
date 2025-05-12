#!/bin/bash

# Define the source directory from the config file
sourcedir="/work/project/ext_016/RNA-Seq-Variant-Calling_1/source_dir_2"

# Array of subdirectories relative to the sourcedir
declare -a dirs=(
  "demo_data"
  "qc_output"
  "trimmed_files"
  "pass1"
  "sj_files"
  "RGbam"
  "dedup"
  "splitNcigar"
  "Recal1"
  "BQSR_1"
  "Recal2"
  "BQSR_2"
  "vcf"
  "vcf_new"
  "CombinedGvcfs"
)

# Loop through the array and create each directory with full path
for dir in "${dirs[@]}"; do
  mkdir -p "${sourcedir}/${dir}"
done

echo "All directories created successfully."
