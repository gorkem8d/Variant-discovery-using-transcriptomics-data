#!/bin/bash
#SBATCH --mem=4000 
#SBATCH --ntasks=1
#SBATCH --time=72:00:00
#SBATCH --job-name=variant_calling
#SBATCH --output=snakemake_%j.out
#SBATCH --error=snakemake_%j.err

# Find an appropriate location for temporary files
if [ -d "/scratch" ]; then
  # If /scratch exists, make sure directory exists
  mkdir -p /scratch/gdurmaz
  TEMP_DIR="/scratch/gdurmaz/tmp.$(date +%s)"
elif [ -d "/tmp" ]; then
  # Fall back to /tmp which exists on most systems
  mkdir -p /tmp/gdurmaz
  TEMP_DIR="/tmp/gdurmaz/tmp.$(date +%s)"
elif [ -n "$SLURM_TMPDIR" ]; then
  # Use SLURM's temporary directory if available
  TEMP_DIR="$SLURM_TMPDIR/tmp.$(date +%s)"
else
  # Last resort - create in current working directory
  TEMP_DIR="$(pwd)/tmp.$(date +%s)"
fi

# Create the temp directory
mkdir -p $TEMP_DIR
export TMPDIR=$TEMP_DIR
echo "Created temporary directory: $TMPDIR"

# Detect available partitions on this HPC system
PARTITION=$(sinfo -h -o "%R" | head -1)
echo "Using partition: $PARTITION"

# Create a cluster config file based on Snakefile's resource requirements
cat > cluster.yaml << EOL
__default__:
  partition: $PARTITION
  time: "2:00:00"
  mem: "4G"
  cpus-per-task: 1

AddRG:
  mem: "8G"
  cpus-per-task: 4
  time: "2:00:00"

mark_dups:
  mem: "12G"
  cpus-per-task: 4
  time: "4:00:00"

index:
  mem: "8G"
  cpus-per-task: 2
  time: "2:00:00"

splitNcigar:
  mem: "50G"
  cpus-per-task: 2
  time: "10:00:00"

BQSR_Pass1:
  mem: "45G"
  cpus-per-task: 4
  time: "12:00:00"

ApplyBQSR:
  mem: "40G"
  cpus-per-task: 2
  time: "6:00:00"

BQSR_Pass2:
  mem: "45G"
  cpus-per-task: 4
  time: "12:00:00"

ApplyBQSR_2:
  mem: "40G"
  cpus-per-task: 2
  time: "6:00:00"

gatk_HaplotypeCaller:
  mem: "45G"
  cpus-per-task: 2
  time: "30:00:00"

VariantFiltration:
  mem: "35G"
  cpus-per-task: 2
  time: "4:00:00"
EOL

# Show available resources on the system
echo "All available partitions and resources:"
sinfo -o "%P %l %c %m"

# Create log directory if it doesn't exist
mkdir -p logs/slurm

# Unlock in case the workflow was interrupted
snakemake --unlock

# Before starting, clean any incomplete output files
find $(grep -o "config\['datadirs'\]\['[^']*'\]" Snakefile | sort -u | sed "s/config\['datadirs'\]\['\([^']*\)'\]/\1/g" | while read dir; do grep -q "^$dir:" config.yaml && grep -A1 "^$dir:" config.yaml | tail -n1 | sed 's/.*: *//'; done) -name "*.tmp*" -delete

# Run Snakemake with SLURM - using 10 concurrent jobs
snakemake -j 16 --latency-wait 300 --rerun-incomplete --configfile config.yaml \
  --cluster-config cluster.yaml \
  --resources mem_mb=250000 \
  --use-conda \
  --keep-going \
  --cluster "sbatch -p {cluster.partition} -J {rule}_{wildcards} --mem={cluster.mem} --cpus-per-task={threads} --time={cluster.time} -o logs/slurm/{rule}_{wildcards}.%j.out -e logs/slurm/{rule}_{wildcards}.%j.err" 


# Clean up the temp directory
rm -rf $TMPDIR
echo "Cleaned up temporary directory: $TMPDIR"