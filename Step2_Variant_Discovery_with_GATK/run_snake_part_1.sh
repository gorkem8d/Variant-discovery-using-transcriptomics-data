#!/bin/bash
#SBATCH --mem=4000 
#SBATCH --ntasks=1
#SBATCH --time=48:00:00
# Detect available partitions on this HPC system
PARTITION=$(sinfo -h -o "%R" | head -1)
echo "Using partition: $PARTITION"
# Create a cluster config file with detected partition
cat > cluster.yaml << EOL
__default__:
  time: "1:00:00"  # Short time for better priority
  mem: "2G"        # Minimal memory
  ntasks: 1
fastqc:
  mem: "4G"
  ntasks: 2
pass1:
  mem: "40G"  # Reduced from 40G
  ntasks: 10   # Reduced from 16
pass2:
  mem: "50G"  # Reduced from 50G
  ntasks: 10   # Reduced from 16
SJ_Merge:
  mem: "4G"
  ntasks: 1
EOL
# Also print available partitions for reference
echo "All available partitions:"
sinfo -o "%P %l %c %m"
# Unlock the workflow
snakemake --unlock -s Snakefile_paired_end_part1
# Run snakemake in cluster mode with detected partition
snakemake -j 10 --latency-wait 120 --rerun-incomplete --configfile config_part1.yaml \
  --cluster-config cluster.yaml \
  --cluster "sbatch -p $PARTITION --mem={cluster.mem} --ntasks={cluster.ntasks} --time={cluster.time}" \
  --keep-going -s Snakefile_paired_end_part1