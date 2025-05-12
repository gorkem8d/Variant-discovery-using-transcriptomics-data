#!/usr/bin/env python
"""
This script processes coverage data for RNA-Seq samples and updates metadata files
with coverage statistics for multiple directories.
"""
import pandas as pd
import glob
import os
import argparse
import sys
from pathlib import Path

def process_directory(base_path, dir_name):
    """
    Process coverage data for a specific directory.
    
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
    
    # Path to the input CSV file
    input_file = os.path.join(base_path, dir_name, "filtered", f"mutation_counts_metadata_{ds_suffix}.csv")
    
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}. Skipping {dir_name}.")
        return False
    
    print(f"Processing {dir_name} with input file: {input_file}")
    
    try:
        # Load the main DataFrame
        df = pd.read_csv(input_file)
        if "Average_Depth_UNC" in df.columns:
            print(f"Error: process previously done. Skipping {dir_name}.")
            return False
        
        # Process UNC coverage
        print(f"Processing UNC coverage for {len(df['Run'])} samples in {dir_name}...")
        
        # Initialize the DataFrame with additional columns for the coverage thresholds
        depth_df = pd.DataFrame(columns=["Run", "Average_Depth_UNC", "Coverage_>2", "Coverage_>4", "Coverage_>8", "Coverage_>10"])
        samples = []
        average_depths = []
        coverage_over_2 = []
        coverage_over_4 = []
        coverage_over_8 = []
        coverage_over_10 = []
        
        # Track if any files were found for this directory
        any_unc_files_found = False
        
        # Iterate over the samples in the original DataFrame
        for sample in df["Run"]:
            
            file_pattern = os.path.join(base_path, dir_name, "pass2", f"{sample}*_Aligned.sortedByCoord.out_UNC_coverage.txt")
            
            matching_files = glob.glob(file_pattern)
            if matching_files:
                any_unc_files_found = True
                for file in matching_files:
                    if os.path.exists(file):
                        depth_data = pd.read_csv(file, sep="\t", header=None, names=["Ref", "Pos", "Depth"])
                        average_depth = depth_data["Depth"].mean()
                        
                        # Count the number of bases that exceed the thresholds
                        over_2 = depth_data[depth_data["Depth"] > 2].shape[0]
                        over_4 = depth_data[depth_data["Depth"] > 4].shape[0]
                        over_8 = depth_data[depth_data["Depth"] > 8].shape[0]
                        over_10 = depth_data[depth_data["Depth"] > 10].shape[0]
                        
                        # Append results to lists
                        samples.append(sample)
                        average_depths.append(average_depth)
                        coverage_over_2.append(over_2)
                        coverage_over_4.append(over_4)
                        coverage_over_8.append(over_8)
                        coverage_over_10.append(over_10)
            else:
                print(f"Warning: No UNC coverage files found for sample {sample} in {dir_name}")
        
        # Check if no UNC files were found for the entire directory
        if not any_unc_files_found:
            print(f"Warning: No UNC coverage files found for any samples in {dir_name}. Skipping UNC coverage processing.")
            # Still continue to process chr11 coverage
        else:
            # Assign the lists to the DataFrame
            depth_df["Run"] = samples
            depth_df["Average_Depth_UNC"] = average_depths
            depth_df["Coverage_>2"] = coverage_over_2
            depth_df["Coverage_>4"] = coverage_over_4
            depth_df["Coverage_>8"] = coverage_over_8
            depth_df["Coverage_>10"] = coverage_over_10
        
        # Process chr11 coverage
        print(f"Processing chr11 coverage for {len(df['Run'])} samples in {dir_name}...")
        
        # Initialize the DataFrame with additional columns for the coverage thresholds
        depth_df_chr11 = pd.DataFrame(columns=["Run", "Coverage_>2_chr11", "Coverage_>4_chr11", "Coverage_>8_chr11", "Coverage_>10_chr11"])
        samples_chr11 = []
        coverage_over_2_chr11 = []
        coverage_over_4_chr11 = []
        coverage_over_8_chr11 = []
        coverage_over_10_chr11 = []
        
        # Track if any chr11 files were found for this directory
        any_chr11_files_found = False
        
        # Iterate over the samples in the original DataFrame
        for sample in df["Run"]:
            
            file_pattern = os.path.join(base_path, dir_name, "pass2", f"{sample}*_Aligned.sortedByCoord.out_chr11_coverage.txt")
            
            matching_files = glob.glob(file_pattern)
            if matching_files:
                any_chr11_files_found = True
                for file in matching_files:
                    if os.path.exists(file):
                        depth_data = pd.read_csv(file, sep="\t", header=None, names=["Ref", "Pos", "Depth"])
                        
                        # Count the number of bases that exceed the thresholds
                        over_2 = depth_data[depth_data["Depth"] > 2].shape[0]
                        over_4 = depth_data[depth_data["Depth"] > 4].shape[0]
                        over_8 = depth_data[depth_data["Depth"] > 8].shape[0]
                        over_10 = depth_data[depth_data["Depth"] > 10].shape[0]
                        
                        # Append results to lists
                        samples_chr11.append(sample)
                        coverage_over_2_chr11.append(over_2)
                        coverage_over_4_chr11.append(over_4)
                        coverage_over_8_chr11.append(over_8)
                        coverage_over_10_chr11.append(over_10)
            else:
                print(f"Warning: No chr11 coverage files found for sample {sample} in {dir_name}")
        
        # Check if no chr11 files were found for the entire directory
        if not any_chr11_files_found:
            print(f"Warning: No chr11 coverage files found for any samples in {dir_name}. Skipping chr11 coverage processing.")
            # Continue with what data we have
        else:
            # Assign the lists to the DataFrame
            depth_df_chr11["Run"] = samples_chr11
            depth_df_chr11["Coverage_>2_chr11"] = coverage_over_2_chr11
            depth_df_chr11["Coverage_>4_chr11"] = coverage_over_4_chr11
            depth_df_chr11["Coverage_>8_chr11"] = coverage_over_8_chr11
            depth_df_chr11["Coverage_>10_chr11"] = coverage_over_10_chr11
        
        # Check if we have any data to merge
        if (not any_unc_files_found) and (not any_chr11_files_found):
            print(f"Warning: No coverage files found for {dir_name}. Skipping merge and save.")
            return False
        
        # Merge df and coverage DataFrames on the "Run" column
        print(f"Merging coverage data with metadata for {dir_name}...")
        
        # Create a backup of the original file
        backup_file = input_file + ".bak"
        df.to_csv(backup_file, index=False)
        print(f"Backup created: {backup_file}")
        
        # Drop existing coverage columns if they exist
        for col in df.columns:
            if col.startswith("Coverage_>") or col == "Average_Depth_UNC":
                df = df.drop(col, axis=1)
        
        # Merge the new coverage data if available
        if any_unc_files_found and not depth_df.empty:
            df = df.merge(depth_df, on='Run', how='left')
        
        if any_chr11_files_found and not depth_df_chr11.empty:
            df = df.merge(depth_df_chr11, on='Run', how='left')
        
        # Save the updated DataFrame to CSV
        output_file = input_file  # Overwrite the original file
        df.to_csv(output_file, index=False)
        print(f"Processing complete for {dir_name}. Output saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"Error processing {dir_name}: {str(e)}")
        return False

def main():
    """
    Main function to parse arguments and process directories.
    """
    parser = argparse.ArgumentParser(description='Process coverage data for RNA-Seq samples')
    parser.add_argument('--base-path', type=str, default="/work/project/ext_016/RNA-Seq-Variant-Calling_1",
                        help='Base path for the project')
    parser.add_argument('--dirs', type=str, nargs='+', 
                        default=["source_dir", "source_dir_4", "source_dir_6"],
                        help='List of source directories to process')
    
    args = parser.parse_args()
    
    success_count = 0
    attempted_count = 0
    
    # Process each directory
    for dir_name in args.dirs:
        dir_path = os.path.join(args.base_path, dir_name)
        if not os.path.exists(dir_path):
            print(f"Warning: Directory {dir_path} does not exist, skipping")
            continue
        
        attempted_count += 1
        if process_directory(args.base_path, dir_name):
            success_count += 1
        else:
            print(f"Note: Skipped or failed processing directory {dir_name}, but continuing with remaining directories")
    
    print(f"Completed processing {success_count} out of {attempted_count} directories")
    
    # Return success if at least one directory was processed successfully
    if success_count > 0:
        return 0
    else:
        print("Error: No directories were successfully processed")
        return 1

if __name__ == "__main__":
    sys.exit(main())