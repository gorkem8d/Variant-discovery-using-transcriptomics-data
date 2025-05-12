#!/usr/bin/env python3

import os
import glob
import pandas as pd
import numpy as np

# Constants
epsilon = 1e-10

def extract_format_values(row, sample_column):
    """Extract GQ and DP values from FORMAT field"""
    try:
        format_fields = row['FORMAT'].split(':')
        sample_values = row[sample_column].split(':')
        format_dict = dict(zip(format_fields, sample_values))
        
        return pd.Series({
            'GQ': format_dict.get('GQ', 'NA'),
            'DP': format_dict.get('DP', 'NA')
        })
    except Exception as e:
        print(f"Error extracting format values: {str(e)}")
        return pd.Series({'GQ': 'NA', 'DP': 'NA'})

def process_file(input_file, output_file, pos_min, pos_max):
    """Process a single file and save the results"""
    try:
        # Get file name without extension
        unique_file = os.path.basename(input_file).split(".")[0]
        
        print(f"  Reading {unique_file}...")
        # Read the CSV file into a DataFrame
        temp = pd.read_csv(input_file)
        
        if "POS" not in temp.columns:
            print(f"  Warning: File {input_file} does not have a POS column. Skipping.")
            return False, "Missing POS column"
        
        # Filter positions within the range
        df = temp[(temp["POS"] >= pos_min) & (temp["POS"] <= pos_max)]
        
        if df.empty:
            print(f"  Warning: No positions within range {pos_min}-{pos_max} in {input_file}. Skipping.")
            return False, "No positions in range"
        
        # Extract values - using the filename as the sample column name
        if unique_file not in df.columns:
            print(f"  Finding sample column for {unique_file}...")
            # Try to find a suitable sample column - often it's the last column
            sample_columns = [col for col in df.columns if col not in ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO', 'FORMAT']]
            if not sample_columns:
                print(f"  Error: Could not identify sample column in {input_file}. Skipping.")
                return False, "Could not identify sample column"
            sample_column = sample_columns[0]
        else:
            sample_column = unique_file
        
        # Extract values
        format_values = df.apply(lambda row: extract_format_values(row, sample_column), axis=1)
        df = pd.concat([df, format_values], axis=1)
        
        # Convert to numeric
        df['GQ'] = pd.to_numeric(df['GQ'], errors='coerce')
        df['DP'] = pd.to_numeric(df['DP'], errors='coerce')
        
        # Calculate individual confidence components
        # GQ confidence (Phred-scaled)
        df['gq_conf'] = 1 - np.power(10, -df['GQ']/10) 
        
        # Cap QUAL values at 50 before calculating confidence
        capped_qual = np.minimum(df['QUAL'], 50)
        df['qual_conf'] = 1 - np.power(10, -capped_qual/10)
        
        # DP confidence (using logistic function to normalize depth)
        df['dp_conf'] = 1 / (1 + np.exp(-0.22 * (df['DP'] - 20))) 
        
        # Combined confidence using weighted arithmetic mean
        # Weights: GQ=0.4, QUAL=0.4, DP=0.2
        df['confidence'] = (
            0.4 * df['gq_conf'] + 
            0.4 * df['qual_conf'] + 
            0.2 * df['dp_conf']
        )
        
        # Keep only the necessary columns
        df = df[['POS', 'GQ', 'QUAL', 'DP', 'gq_conf', 'qual_conf', 'dp_conf', 'confidence', 'FILTER']]
        
        # Save the csv
        df.to_csv(output_file, index=False)
        
        return True, f"Successfully processed {os.path.basename(input_file)}"
    except Exception as e:
        return False, f"Error processing {input_file}: {str(e)}"

def main():
    # Define source directories and their corresponding output directories
    base_dir = "/work/project/ext_016/RNA-Seq-Variant-Calling_1"
    source_dirs = [
        f"{base_dir}/source_dir/filtered/csv_files",
        f"{base_dir}/source_dir_4/filtered/csv_files", 
        f"{base_dir}/source_dir_6/filtered/csv_files"
    ]
    out_dirs = [
        f"{base_dir}/source_dir/filtered",
        f"{base_dir}/source_dir_4/filtered", 
        f"{base_dir}/source_dir_6/filtered"
    ]
    
    pos_min = 67990100
    pos_max = 68005097
    
    # Counter for statistics
    success_count = 0
    skipped_count = 0
    failed_count = 0
    already_exists_count = 0
    
    # Process each source directory
    for source_dir in source_dirs:
        print(f"\nProcessing directory: {source_dir}")
        
        # Check if directory exists
        if not os.path.exists(source_dir):
            print(f"Directory {source_dir} does not exist. Skipping.")
            skipped_count += 1
            continue
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(out_dirs), "Confidence")
        os.makedirs(output_dir, exist_ok=True)
        
        # Get list of files to process
        file_pattern = os.path.join(source_dir, "*.csv")
        file_list = glob.glob(file_pattern)
        
        if not file_list:
            print(f"No CSV files found in {source_dir}. Skipping.")
            skipped_count += 1
            continue
            
        print(f"Found {len(file_list)} files to process")
        
        # Process each file
        for input_file in file_list:
            unique_file = os.path.basename(input_file).split(".")[0]
            output_file = os.path.join(output_dir, f"{unique_file}_confidence.csv")
            
            # Check if output file already exists
            if os.path.exists(output_file):
                print(f"Output file for {unique_file} already exists. Skipping.")
                already_exists_count += 1
                continue
            
            print(f"Processing {unique_file}...")
            success, message = process_file(input_file, output_file, pos_min, pos_max)
            
            if success:
                success_count += 1
                print(f"  {message}")
            else:
                failed_count += 1
                print(f"  {message}")
    
    # Print summary
    print("\nSummary:")
    print(f"Total files successfully processed: {success_count}")
    print(f"Total files already existed and skipped: {already_exists_count}")
    print(f"Total files skipped/failed: {skipped_count + failed_count}")

if __name__ == "__main__":
    main()