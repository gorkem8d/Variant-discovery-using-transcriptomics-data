#!/bin/bash

# Define the base output directory and other options
base_dir="/work/project/ext_016/RNA-Seq-Variant-Calling_1/source_dir_6/demo_data"
threads=10  # Number of threads for parallel processing
split="yes"  # 'yes' to split files, anything else will not split

# Navigate through each subdirectory in the base directory
find "$base_dir" -mindepth 1 -maxdepth 1 -type d | while IFS= read -r dir; do
    # Check if .fastq.gz files already exist in the directory
    if find "$dir" -type f -name "*.fastq.gz" -print -quit | grep -q .; then
        echo ".fastq.gz files already exist in $dir, skipping..."
        continue
    fi

    sra_file=$(find "$dir" -type f -name "*.sra" -print -quit)  # Find the first .sra file in the directory
    if [ -z "$sra_file" ]; then
        echo "No SRA file found in $dir"
        continue
    fi

    echo "Processing $(basename "$sra_file")"

    if [ "$split" = "yes" ]; then
        parallel-fastq-dump --sra-id "$sra_file" --threads $threads --outdir "$dir" --split-files --gzip
    else
        parallel-fastq-dump --sra-id "$sra_file" --threads $threads --outdir "$dir" --gzip
    fi
done

echo "All files processed."
