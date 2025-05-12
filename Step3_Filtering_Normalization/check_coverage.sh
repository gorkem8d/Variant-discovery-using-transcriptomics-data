#!/bin/bash
#SBATCH --mem=40000 
#SBATCH --ntasks=1

module load ngs/samtools/1.9
# Check if samtools is available
if ! command -v samtools &> /dev/null; then
    echo "Error: samtools is not installed or not in the PATH"
    echo "Please load the samtools module or make sure it's installed"
    exit 1
fi

# Print samtools version for logging purposes
echo "Using samtools version: $(samtools --version | head -n 1)"

# Create a log file for the run
LOG_FILE="coverage_analysis_$(date +%Y%m%d_%H%M%S).log"
echo "Starting analysis run at $(date)" | tee -a "$LOG_FILE"
echo "Logs will be saved to $LOG_FILE"

# Base directory
BASE_DIR="/work/project/ext_016/RNA-Seq-Variant-Calling_1"

# Directories to process
SOURCE_DIRS=("source_dir" "source_dir_4" "source_dir_6")

# Function to log messages with timestamps
log_message() {
    echo "[$(date +%Y-%m-%d\ %H:%M:%S)] $1" | tee -a "$LOG_FILE"
}

# Loop through each source directory
for SOURCE in "${SOURCE_DIRS[@]}"
do
    # Full path to the BAM files directory
    BAM_DIR="${BASE_DIR}/${SOURCE}/pass2"
    
    # Check if the directory exists
    if [ ! -d "$BAM_DIR" ]; then
        log_message "Directory $BAM_DIR does not exist, skipping..."
        continue
    fi
    
    log_message "Processing directory: $BAM_DIR"
    
    # Check if any BAM files exist in the directory
    shopt -s nullglob  # Set nullglob to make patterns expand to nothing if no matches
    BAM_FILES=($BAM_DIR/*_Aligned.sortedByCoord.out.bam)
    shopt -u nullglob  # Unset nullglob
    
    if [ ${#BAM_FILES[@]} -eq 0 ]; then
        log_message "No BAM files found in $BAM_DIR, skipping..."
        continue
    fi
    
    # Loop through each BAM file in the directory
    for BAM_FILE in "${BAM_FILES[@]}"
    do
        BAM_BASENAME=$(basename "$BAM_FILE")
        log_message "Processing $BAM_BASENAME"
        
        # Check if the index file doesn't exist and create it
        if [ ! -f "${BAM_FILE}.bai" ]; then
            log_message "Creating index for $BAM_BASENAME"
            samtools index $BAM_FILE
            log_message "Index creation completed for $BAM_BASENAME"
        else
            log_message "Index file for $BAM_BASENAME already exists, skipping indexing"
        fi
        
        # Define regions of interest
        UNC_REGION="chr11:67991100-68004982"
        CHR_REGION="chr11"
        
        # Output file names
        UNC_OUTPUT="${BAM_FILE%.bam}_UNC_coverage.txt"
        CHR_OUTPUT="${BAM_FILE%.bam}_chr11_coverage.txt"
        
        # Calculate coverage for UNC gene region if the file doesn't exist
        if [ ! -f "$UNC_OUTPUT" ]; then
            log_message "Calculating UNC gene coverage for $BAM_BASENAME"
            samtools depth -a -r $UNC_REGION $BAM_FILE > "$UNC_OUTPUT.tmp"
            # Only move the file if command was successful
            if [ $? -eq 0 ]; then
                mv "$UNC_OUTPUT.tmp" "$UNC_OUTPUT"
                log_message "UNC gene coverage written to $UNC_OUTPUT"
            else
                log_message "Error calculating UNC gene coverage for $BAM_BASENAME"
                rm -f "$UNC_OUTPUT.tmp"
            fi
        else
            log_message "UNC gene coverage file for $BAM_BASENAME already exists, skipping"
        fi
        
        # Calculate coverage for chromosome 11 if the file doesn't exist
        if [ ! -f "$CHR_OUTPUT" ]; then
            log_message "Calculating chromosome 11 coverage for $BAM_BASENAME"
            samtools depth -a -r $CHR_REGION $BAM_FILE > "$CHR_OUTPUT.tmp"
            # Only move the file if command was successful
            if [ $? -eq 0 ]; then
                mv "$CHR_OUTPUT.tmp" "$CHR_OUTPUT"
                log_message "Chromosome 11 coverage written to $CHR_OUTPUT"
            else
                log_message "Error calculating chromosome 11 coverage for $BAM_BASENAME"
                rm -f "$CHR_OUTPUT.tmp"
            fi
        else
            log_message "Chromosome 11 coverage file for $BAM_BASENAME already exists, skipping"
        fi
        
        log_message "Completed processing $BAM_BASENAME"
    done
    
    log_message "Completed processing directory $BAM_DIR"
done

log_message "Coverage analysis completed for all directories."