#!/usr/bin/env python
"""
This script converts VCF files obtained by GATK pipeline to CSV format.
It processes files across multiple directories: source_dir, source_dir_4, and source_dir_6.
Memory-optimized version to avoid SLURM memory limits.
"""

import io
import os
import glob
import gzip
import pandas as pd
import argparse
import csv
from contextlib import contextmanager

@contextmanager
def open_file(path, mode):
    """Context manager for opening files, handling gzipped files."""
    if path.endswith('.gz'):
        fh = gzip.open(path, mode)
    else:
        fh = open(path, mode)
    try:
        yield fh
    finally:
        fh.close()

def process_vcf_in_chunks(input_path, output_path, chunk_size=10000):
    """
    Process a VCF file in chunks to reduce memory usage.
    
    Args:
        input_path (str): Path to the input VCF file (gzipped)
        output_path (str): Path to the output CSV file
        chunk_size (int): Number of lines to process at once
    """
    # First, get the header line
    header = None
    with open_file(input_path, 'rt') as f:
        for line in f:
            if line.startswith('#') and not line.startswith('##'):
                header = line.strip().split('\t')
                header[0] = 'CHROM'  # Rename #CHROM to CHROM
                break
    
    if not header:
        raise ValueError(f"Could not find header in {input_path}")
    
    # Process the file in chunks
    with open_file(input_path, 'rt') as infile, open(output_path, 'w', newline='') as outfile:
        csv_writer = csv.writer(outfile)
        csv_writer.writerow(header)
        
        # Skip header lines
        for line in infile:
            if line.startswith('##'):
                continue
            if line.startswith('#'):
                continue  # Skip the header line we already processed
            break
        
        # Process the first line that isn't a header
        if not line.startswith('#'):
            process_line(line, csv_writer)
        
        # Process the rest of the file in chunks
        chunk = []
        for line in infile:
            if len(chunk) >= chunk_size:
                process_chunk(chunk, csv_writer)
                chunk = []
            chunk.append(line)
            
        if chunk:  # Process the last chunk
            process_chunk(chunk, csv_writer)

def process_line(line, csv_writer):
    """Process a single line of VCF data."""
    parts = line.strip().split('\t')
    chrom = parts[0]
    alt = parts[4]
    
    # Apply filters
    if chrom == 'chr11' and alt != '<NON_REF>':
        csv_writer.writerow(parts)

def process_chunk(chunk, csv_writer):
    """Process a chunk of VCF lines."""
    for line in chunk:
        process_line(line, csv_writer)

def process_directory(base_path, source_dir):
    """
    Process all VCF files in the specified directory and convert them to CSV.
    
    Args:
        base_path (str): Base path for the project
        source_dir (str): Source directory name (e.g., 'source_dir_4')
    """
    directory_path = os.path.join(base_path, source_dir, "filtered", "*.gz")
    
    # Create the csv_files directory if it doesn't exist
    csv_dir = os.path.join(base_path, source_dir, "filtered", "csv_files")
    os.makedirs(csv_dir, exist_ok=True)
    
    # Get a list of all files that match the pattern
    file_list = glob.glob(directory_path)
    
    # Extract unique filenames without extensions
    unique_file_list = list(set([os.path.basename(file_path).split(".")[0] for file_path in file_list]))
    
    print(f"Processing {len(unique_file_list)} files in {source_dir}...")
    
    for unique_file in unique_file_list:
        csv_path = os.path.join(csv_dir, f"{unique_file}.csv")
        
        # Skip if the CSV file already exists
        if os.path.exists(csv_path):
            print(f"Skipping {unique_file}.csv (already exists)")
            continue
        
        try:
            path_gz = os.path.join(base_path, source_dir, "filtered", f"{unique_file}.variant_filtered.vcf.gz")
            
            # Check if the file exists
            if not os.path.exists(path_gz):
                print(f"Warning: {path_gz} does not exist, skipping")
                continue
                
            print(f"Processing {unique_file}...")
            
            # Process the file with reduced memory usage
            process_vcf_in_chunks(path_gz, csv_path)
            
            print(f"Successfully created {csv_path}")
            
        except Exception as e:
            print(f"Error processing {unique_file}: {str(e)}")

def main():
    """
    Main function to parse arguments and process directories.
    """
    parser = argparse.ArgumentParser(description='Convert VCF files to CSV format')
    parser.add_argument('--base-path', type=str, default="/work/project/ext_016/RNA-Seq-Variant-Calling_1",
                        help='Base path for the project')
    parser.add_argument('--dirs', type=str, nargs='+', 
                        default=["source_dir", "source_dir_4", "source_dir_6"],
                        help='List of source directories to process')
    parser.add_argument('--chunk-size', type=int, default=10000,
                        help='Number of lines to process at once (default: 10000)')
    parser.add_argument('--memory-limit', type=int, default=7000,
                        help='Approximate memory limit in MB (default: 7000)')
    
    args = parser.parse_args()
    
    # Process each directory
    for source_dir in args.dirs:
        dir_path = os.path.join(args.base_path, source_dir)
        if not os.path.exists(dir_path):
            print(f"Warning: Directory {dir_path} does not exist, skipping")
            continue
        
        process_directory(args.base_path, source_dir)
    
    print("All directories processed successfully")

if __name__ == "__main__":
    main()