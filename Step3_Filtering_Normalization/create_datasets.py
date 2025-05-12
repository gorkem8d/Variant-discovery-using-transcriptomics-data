#!/usr/bin/env python
"""
This script counts mutations in CSV files across multiple source directories
and merges the counts with metadata.
"""

import io
import os
import glob
import gzip
import pandas as pd
import argparse
import sys
from pathlib import Path


def process_directory(base_path, dir_name):
    """
    Process mutation counts for a specific directory.
    
    Args:
        base_path (str): Base project path
        dir_name (str): Directory name (e.g., 'source_dir_4')
    
    Returns:
        bool: True if processing was successful, False otherwise
    """
    # Determine the dataset suffix based on the directory name
    if dir_name == "source_dir":
        ds_suffix = "ds1"
    elif dir_name == "source_dir_4":
        ds_suffix = "ds4"
    elif dir_name == "source_dir_6":
        ds_suffix = "ds6"
    else:
        print(f"Error: Unknown directory {dir_name}")
        return False
    
    print(f"Processing {dir_name}...")
    
    try:
        # Set paths
        csv_dir = os.path.join(base_path, dir_name, "filtered", "csv_files")
        output_file = os.path.join(base_path, dir_name, "filtered", f"mutation_counts_metadata_{ds_suffix}.csv")
        # Fixed path for SRA info file - now points to /source_dir/filtered/srainfo/SraRunTable.csv
        sra_info_file = os.path.join(base_path, dir_name, "filtered", "srainfo", "SraRunTable.csv")
        
        # Check if csv directory exists
        if not os.path.exists(csv_dir):
            print(f"Skipping {dir_name}: CSV directory not found: {csv_dir}")
            return False

        # Check if output file already exists - skip if it does
        if os.path.exists(output_file):
            print(f"Skipping {dir_name}: Output file already exists: {output_file}")
            return True
            
        # Check if SRA info file exists
        if not os.path.exists(sra_info_file):
            print(f"Skipping {dir_name}: SRA info file not found: {sra_info_file}")
            return False
        
        # Get all CSV files
        directory_path = os.path.join(csv_dir, "*.csv")
        file_list = glob.glob(directory_path)
        
        if not file_list:
            print(f"Skipping {dir_name}: No CSV files found in {csv_dir}")
            return False
        
        # Extract unique filenames without extensions
        unique_file_list = list(set([os.path.basename(file_path).split(".")[0] for file_path in file_list]))
        print(f"Found {len(unique_file_list)} unique samples in {dir_name}")
        
        # Create new dataframe to count number of mutations of unc and chr11
        columns = ["Run", "unc_mut", "chr11_mut"]
        df = pd.DataFrame(columns=columns)
        
        # Process each sample
        for sample in unique_file_list:
            sample_file = os.path.join(csv_dir, f"{sample}.csv")
            
            if not os.path.exists(sample_file):
                print(f"Warning: File not found for sample {sample}, skipping")
                continue
                
            try:
                # Read the CSV file
                data = pd.read_csv(sample_file)
                
                # Get the total number of lines (chr11 mutations)
                chr11_mut = len(data)
                
                # Get the number of lines where POS is within the UNC range
                unc_mut = len(data[(data['POS'] >= 67991100) & (data['POS'] <= 68005150)])
                
                # Create a new row for the current file
                new_row = pd.DataFrame({"Run": [sample], "unc_mut": [unc_mut], "chr11_mut": [chr11_mut]})
                
                # Concatenate the new row to the existing DataFrame
                df = pd.concat([df, new_row], ignore_index=True)
                
            except Exception as e:
                print(f"Error processing sample {sample}: {str(e)}")
        
        # Check if we have any data
        if len(df) == 0:
            print(f"Error: No mutation data collected for {dir_name}")
            return False
            
        print(f"Processed {len(df)} samples with mutation counts")
        
        # Merge with metadata
        try:
            meta_data = pd.read_csv(sra_info_file, sep=",")
            merged_df = pd.merge(df, meta_data, on="Run", how="left")
            
            # Check if merge was successful
            if len(merged_df) != len(df):
                print(f"Warning: Merge resulted in {len(merged_df)} rows, but expected {len(df)} rows")
                
            # If an existing file, create backup
            if os.path.exists(output_file):
                backup_file = output_file + ".bak"
                print(f"Creating backup of existing file: {backup_file}")
                os.rename(output_file, backup_file)
                
            # Save the merged CSV
            merged_df.to_csv(output_file, index=False)
            print(f"Successfully saved mutation counts to: {output_file}")
            
            return True
            
        except Exception as e:
            print(f"Error merging with metadata: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Error processing directory {dir_name}: {str(e)}")
        return False


def main():
    """
    Main function to parse arguments and process directories.
    """
    parser = argparse.ArgumentParser(description='Count mutations in CSV files across directories')
    parser.add_argument('--base-path', type=str, default="/work/project/ext_016/RNA-Seq-Variant-Calling_1",
                        help='Base path for the project')
    parser.add_argument('--dirs', type=str, nargs='+', 
                        default=["source_dir"],  # Changed to only process source_dir by default
                        help='List of source directories to process')
    
    args = parser.parse_args()
    
    success_count = 0
    attempted_count = 0
    
    print("Starting mutation count analysis...")
    
    # Process each directory
    for dir_name in args.dirs:
        dir_path = os.path.join(args.base_path, dir_name)
        if not os.path.exists(dir_path):
            print(f"Skipping {dir_name}: Directory {dir_path} does not exist")
            continue
        
        attempted_count += 1
        if process_directory(args.base_path, dir_name):
            success_count += 1
    
    print(f"Completed processing {success_count} out of {attempted_count} attempted directories")
    
    # Changed return logic - consider successful if at least one directory was processed
    if success_count > 0:
        print("Job completed successfully")
        return 0
    elif attempted_count == 0:
        print("No directories were processed")
        return 1
    else:
        print("Job failed - could not process any directories")
        return 1


if __name__ == "__main__":
    sys.exit(main())