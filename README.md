# GATK Variant Discovery Pipeline for RNA-seq Data
## Analysis of UNC93B1 Variants in Systemic Lupus Erythematosus

A comprehensive bioinformatics pipeline for identifying genetic variants from RNA-sequencing data, specifically designed to discover novel variants in the UNC93B1 gene associated with SLE pathogenesis.

---

## 📋 Overview

This pipeline implements GATK's RNA-seq short variant discovery workflow to identify SNPs and insertions/deletions (indels) from transcriptomics data. The workflow was developed to analyze UNC93B1 genetic variations in SLE patients compared to healthy controls, integrating variant calling, quality control, and machine learning-based variant prioritization.

**Pipeline Version:** GATK v4.2.6.1  
**Reference Genome:** hg38  
**Target Gene:** UNC93B1 (Chromosome 11)

---

## 🔬 Datasets Analyzed

The pipeline was validated on three independent RNA-seq datasets:

### Dataset A (PRJNA439269)
- **Samples:** 31 SLE patients, 29 healthy controls
- **Sample Type:** Blood (PAXgene tubes)
- **Technical Replicates:** 2 per sample
- **Sequencing:** Single-end, Illumina HiSeq 2500

### Dataset B (PRJNA294172)
- **Samples:** 99 SLE patients, 18 healthy controls
- **Sample Type:** Blood (PAXgene tubes)
- **Sequencing:** Single-end, Illumina HiSeq 2500

### Dataset C (PRJNA294172)
- **Samples:** 18 SLE patients, 6 healthy controls
- **Sample Type:** PBMCs (heparin tubes)
- **Sequencing:** Paired-end, Illumina HiSeq 2500 & NextSeq 500

---

## 🛠️ Pipeline Architecture

### Workflow Management
- **System:** Snakemake workflow management
- **Execution:** High-performance computing (HPC) cluster with parallel processing


---

## 📊 Pipeline Steps

### 1. Quality Control & Preprocessing

#### 1.1 Initial QC
```bash
fastqc [input_fastq] -o [output_dir]
```

#### 1.2 Adapter Trimming
```bash
trim-galore-pe \
  --quality 20 \
  --length 20 \
  [input_R1.fastq] [input_R2.fastq]
```
**Parameters:**
- Quality threshold: Phred score > 20
- Minimum read length: 20 bp

### 2. Two-Pass STAR Alignment

#### 2.1 First Pass Alignment
Generate splice junction information for all samples:
```bash
STAR \
  --genomeDir [genome_index] \
  --readFilesIn [trimmed_reads] \
  --outFileNamePrefix [sample_prefix] \
  --outSAMtype BAM Unsorted
```

#### 2.2 Splice Junction Database
Merge splice junctions across all samples and regenerate genome index:
```bash
# Merge all SJ.out.tab files
cat */SJ.out.tab > merged_SJ.out.tab

# Regenerate STAR genome index with known junctions
STAR \
  --runMode genomeGenerate \
  --genomeDir [genome_dir_2pass] \
  --genomeFastaFiles [reference.fa] \
  --sjdbFileChrStartEnd merged_SJ.out.tab
```

#### 2.3 Second Pass Alignment
Align with improved junction database:
```bash
STAR \
  --genomeDir [genome_dir_2pass] \
  --readFilesIn [trimmed_reads] \
  --outFileNamePrefix [sample_prefix] \
  --outSAMtype BAM SortedByCoordinate
```

### 3. BAM Processing

#### 3.1 Add Read Groups
```bash
picard AddOrReplaceReadGroups \
  I=[input.bam] \
  O=[output.bam] \
  RGID=[sample_id] \
  RGLB=[library] \
  RGPL=ILLUMINA \
  RGPU=[unit] \
  RGSM=[sample_name]
```

#### 3.2 Mark Duplicates
```bash
picard MarkDuplicates \
  I=[input.bam] \
  O=[marked.bam] \
  M=[metrics.txt] \
  OPTICAL_DUPLICATE_PIXEL_DISTANCE=100
```
**Key Parameter:** Optical duplicate distance = 100 pixels

#### 3.3 Split N Cigar Reads
Splits reads spanning splice junctions and hard-clips intronic overhangs:
```bash
gatk SplitNCigarReads \
  -R [reference.fa] \
  -I [marked.bam] \
  -O [split.bam]
```

#### 3.4 Base Quality Score Recalibration (BQSR)

**Known Variant Sites Used:**
1. SNPs from 1000 Genomes Project
2. Gold standard indels (Mills et al., 2011)
3. dbSNP build 138 (mapped to hg38)

```bash
# First pass - build recalibration model
gatk BaseRecalibrator \
  -R [reference.fa] \
  -I [split.bam] \
  --known-sites [1000G_snps.vcf] \
  --known-sites [Mills_indels.vcf] \
  --known-sites [dbsnp_138.hg38.vcf] \
  -O [recal_data.table]

# Second pass - apply recalibration
gatk ApplyBQSR \
  -R [reference.fa] \
  -I [split.bam] \
  --bqsr-recal-file [recal_data.table] \
  -O [recalibrated.bam]
```

### 4. Variant Calling

#### 4.1 HaplotypeCaller
```bash
gatk HaplotypeCaller \
  -R [reference.fa] \
  -I [recalibrated.bam] \
  -O [raw_variants.vcf] \
  --standard-min-confidence-threshold-for-calling 10.0 \
  --kmer-size 25
```

**Key Parameters:**
- **Activity score threshold:** 10.0 (sliding window method)
- **Assembly algorithm:** De Bruijn graphs
- **K-mer size:** 25
- **Output format:** VCF (Variant Call Format)

#### 4.2 Variant Filtration
```bash
gatk VariantFiltration \
  -R [reference.fa] \
  -V [raw_variants.vcf] \
  -O [filtered_variants.vcf] \
  --filter-expression "QD < 2.0" --filter-name "QD2" \
  --filter-expression "FS > 30.0" --filter-name "FS30" \
  --filter-expression "DP < 10" --filter-name "DP10" \
  --genotype-filter-expression "GQ < 20" --genotype-filter-name "GQ20"
```

**Quality Metrics:**
- **QD (Quality by Depth):** < 2.0 filtered out
- **FS (Fisher Strand Bias):** > 30.0 filtered out
- **DP (Read Depth):** < 10 filtered out
- **GQ (Genotype Quality):** < 20 filtered out

---

## 🔍 Variant Analysis & Prioritization

### 5. Coverage Threshold Selection

**Optimal Coverage:** 4x selected based on systematic analysis

**Rationale:**
- Mutation rates peak at 4x coverage across all datasets
- Quality scores (QUAL ~60-80) reach practical utility thresholds
- Balances variant discovery with quality control
- Higher thresholds (6x-8x) show quality inflation without proportional reliability improvement

**Normalized Mutation Rate:**
```
μ_norm = M / R_c>4
```
Where:
- M = number of observed mutations
- R_c>4 = number of bases with coverage > 4

### 6. Confidence Score Calculation

Integrates three quality metrics using weighted scoring:

#### 6.1 Component Scores

**Genotype Quality (GQ):**
```
GQ_conf = 1 - 10^(-GQ/10)
```

**Variant Quality (QUAL):**
```
QUAL_conf = 1 - 10^(-QUAL/10)
```

**Read Depth (DP) - Logistic Function:**
```
DP_conf = 1 / (1 + e^(-0.15(DP-15)))
```

Parameters optimized for:
- High coverage (30x) → 0.95 confidence
- Low coverage (10x) → 0.1 confidence
- Midpoint: 20x

#### 6.2 Combined Confidence Score
```
Confidence = 0.4 × GQ_conf + 0.4 × QUAL_conf + 0.2 × DP_conf
```

**Weighting Rationale:**
- GQ (40%): Confidence in specific genotype call
- QUAL (40%): Overall variant quality
- DP (20%): Coverage contribution plateaus after threshold

---

## 🎯 Variant Effect Prediction

### 7. Variant Effect Predictor (VEP)

All variants analyzed using Ensembl VEP to determine:
- Amino acid changes
- Variant consequences (missense, synonymous, stop-gained, etc.)
- Functional impact predictions
- Biotype classification

```bash
vep \
  --input_file [filtered_variants.vcf] \
  --output_file [annotated_variants.vcf] \
  --format vcf \
  --vcf \
  --species homo_sapiens \
  --assembly GRCh38 \
  --cache \
  --plugin PolyPhen \
  --plugin SIFT \
  --plugin CADD \
  --plugin ClinPred
```

**Prediction Tools Integrated:**
- **PolyPhen-2:** Protein function impact
- **SIFT:** Deleterious variant prediction
- **CADD:** Combined deleteriousness score
- **ClinPred:** Clinical pathogenicity

---

## 🤖 Machine Learning Variant Scoring

### 8. Dual-Method Scoring System

#### 8.1 Manual Weighted Ranking

Based on Curtis et al. (2019) framework:

**Base Scores by Consequence:**
- Frameshift/Stop-gained: 20 points
- Missense: 10-15 points
- Synonymous: 3-5 points
- Intergenic: 1 point

**Bonus Criteria (+10 points each):**
- PolyPhen > 0.447 (possibly/probably damaging)
- SIFT < 0.05 (deleterious)
- CADD phred ≥ 20 (top 1% deleterious variants)
- Allele frequency < 0.01 (rare variant)
- SLE-specific occurrence (>0.56% SLE, 0% healthy)

#### 8.2 ML-Based Scoring

**Unsupervised anomaly detection approach:**

**Feature Extraction Domains:**
1. Disease-specific association (SLE vs healthy frequency)
2. Variant consequence severity
3. Pathogenicity predictions (PolyPhen, SIFT, CADD, ClinPred)
4. Protein structure impact (amino acid property changes)
5. Population frequency metrics

**ML Components:**
- **Dimensionality Reduction:** PCA (preserves 95% variance)
- **Anomaly Detection Ensemble:**
  - Isolation Forest (multiple contamination parameters)
  - Local Outlier Factor (varying neighborhood sizes)
- **Distance-based Metrics:** PCA space distance from origin

**Missing Data Handling:**
Novel approach for variants lacking prediction scores:
- Calculate missing data ratio (0-1)
- Apply calibrated score adjustments based on:
  - Extent of missing data (25-50%, 50-75%, >75%)
  - Strength of alternative evidence
  - SLE-specificity, consequence severity

**Score Transformation:**
```python
# Sigmoid transformation
f(x) = 1 / (1 + e^(-k(x-x0)))

# Where:
# k = steepness parameter (adjusted by data completeness)
# x0 = midpoint (positioned to optimize high-risk variant identification)
```

**Risk Categories:**
- Very high risk: 85-100
- High risk: 70-84
- Moderate-high risk: 55-69
- Moderate risk: 40-54
- Low-moderate risk: 25-39
- Low risk: 10-24
- Very low risk: 0-9

#### 8.3 Combined Final Score

Integration of both methods provides:
- Moderate positive correlation (r = 0.502)
- Strong agreement at risk extremes
- Complementary assessment for intermediate-risk variants

**Validation threshold:** Score ≥ 53
- Based on distribution of known SLE-associated variants (60-72 range)
- Buffer zone below established pathogenic range
- Natural break point in data distribution

---

## 📈 Key Results

### Validation Against Literature
Successfully identified known SLE-associated variant positions:
- **E92V** (Lit: E92G) - Score: 59.2
- **I317T** (Lit: I317M) - Score: 71.7
- **I317V** (Lit: I317M) - Score: 60.9
- **R466Ter** (Lit: R466S) - Score: 71.7

### Novel Candidate Variants
**252 candidate variants** exceeded threshold score of 53

**Top Scoring Variants:**
1. **L129I** (chr11:68003029) - Score: 92.9 (Very high risk)
   - Found in 3 SLE patients, 0 healthy
   - CADD: 26.0
   
2. **P209L** (chr11:67999234) - Score: 85.9 (Very high risk)
   - Found in 3 SLE patients, 0 healthy
   - CADD: 25.4

3. **G591E** (chr11:67991568) - Score: 82.3 (High risk)
   - Found in 1 SLE patient, 0 healthy
   - CADD: 17.5

---

## 💻 Technical Requirements

### Software Dependencies
```bash
# Core tools
fastqc >= 0.11.9
trim-galore >= 0.6.6
STAR >= 2.7.9a
samtools >= 1.12
picard >= 2.25.0
gatk >= 4.2.6.1
bcftools >= 1.12

# Variant annotation
ensembl-vep >= 104

# Python environment
python >= 3.8
pandas >= 1.3.0
numpy >= 1.21.0
scikit-learn >= 0.24.2
scipy >= 1.7.0
```

### Python Packages for ML Scoring
```python
# Machine learning
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

# Data processing
import pandas as pd
import numpy as np
```

### Computational Resources
- **HPC Environment:** SLURM job scheduler
- **Memory:** Minimum 32GB RAM per sample
- **Storage:** ~100GB per sample (including intermediate files)
- **CPU:** Multi-core processing (8-16 cores recommended)

### Reference Files Required
```
reference_genome/
├── hg38.fa
├── hg38.fa.fai
├── hg38.dict
└── STAR_index/
    └── [STAR genome index files]

known_sites/
├── 1000G_phase1.snps.high_confidence.hg38.vcf.gz
├── Mills_and_1000G_gold_standard.indels.hg38.vcf.gz
└── dbsnp_138.hg38.vcf.gz
```

---

## 📂 Output Files

### Directory Structure
```
project/
├── fastqc/                    # QC reports
├── trimmed/                   # Trimmed FASTQ files
├── aligned/                   # BAM files
│   ├── pass1/                 # First pass alignments
│   └── pass2/                 # Second pass alignments
├── processed/                 # Processed BAMs
│   ├── marked_duplicates/
│   ├── split_reads/
│   └── recalibrated/
├── variants/                  # VCF files
│   ├── raw/
│   ├── filtered/
│   └── annotated/
├── analysis/                  # Analysis outputs
│   ├── coverage_stats/
│   ├── confidence_scores/
│   ├── vep_annotations/
│   └── variant_rankings/
└── results/                   # Final results
    ├── high_priority_variants.csv
    ├── combined_scores.csv
    └── visualizations/
```

### Key Output Files
- **filtered_variants.vcf:** High-confidence variant calls
- **annotated_variants.vcf:** VEP-annotated variants
- **variant_table.csv:** Comprehensive variant information with scores
- **high_priority_candidates.csv:** Variants exceeding threshold (≥53)
- **confidence_metrics.csv:** Quality scores for all variants

---

## 🔧 Usage Example

### Complete Pipeline Execution

```bash
# 1. Create project directory
mkdir -p sle_variant_analysis
cd sle_variant_analysis

# 2. Set up reference files
ln -s /path/to/reference_genome ./reference
ln -s /path/to/known_sites ./known_sites

# 3. Run Snakemake workflow
snakemake \
  --snakefile Snakefile \
  --cores 16 \
  --use-conda \
  --cluster "sbatch --cpus-per-task=8 --mem=32G"

# 4. Run variant analysis
python scripts/analyze_variants.py \
  --vcf variants/filtered/all_samples.vcf \
  --metadata sample_metadata.csv \
  --gene UNC93B1 \
  --coverage-threshold 4 \
  --output analysis/

# 5. Generate variant scores
python scripts/score_variants.py \
  --input analysis/variant_table.csv \
  --output results/scored_variants.csv \
  --threshold 53
```

---

## 📊 Quality Metrics

### Pipeline Performance Indicators

**Variant Quality Distribution:**
- Mean QUAL at 4x coverage: 60-80 (practical utility threshold)
- Mean GQ: >20 (high confidence genotype calls)
- Mean DP: 15-30x (optimal range)

**Filtering Efficiency:**
- ~70% variants pass quality filters
- False positive rate minimized through dual-method scoring
- True positive rate validated by literature-confirmed variants

---

## 🔬 Biological Interpretation

### UNC93B1 Function
- **Role:** TLR chaperone protein (12 transmembrane domains)
- **Location:** Endoplasmic reticulum → Endolysosomal compartment
- **Critical for:** TLR3, TLR7, TLR8, TLR9 trafficking and signaling

### SLE Disease Mechanism
Identified variants may contribute to SLE through:
1. Enhanced TLR7 binding site accessibility
2. Disrupted TLR7/TLR8 interaction dynamics
3. Impaired protein stability
4. Altered TLR signaling termination
5. Loss of C-terminal regulatory domains

### Biochemical Impact Examples

**E92V (Dataset) vs E92G (Literature):**
- Dataset: Hydrophobic substitution may enhance TLR7 binding
- Literature: Increased flexibility disrupts UNC93B1-TLR7 interaction

**R466Ter (Stop-gained):**
- Premature termination → truncated protein
- Loss of C-terminal domains
- Reduced TLR8 signaling → amplified TLR7 activity
- Known TLR7 hyperactivation pathway to lupus

---

## 📚 Citations & References

### Pipeline Development
This pipeline was developed as part of:

**Durmaz, M. G. (2025).** *Analysis of Systemic Lupus Erythematosus Variants in the UNC93B1 Gene Using Patient Transcriptomics Data.* Master's thesis, Ludwig-Maximilians-Universität München.

### Key References
- **GATK Best Practices:** Van der Auwera et al. (2013)
- **Manual Scoring Framework:** Curtis (2019)
- **CADD Scoring:** Kircher et al. (2014)
- **VEP:** McLaren et al. (2016)
- **UNC93B1 in SLE:** Wolf et al. (2024), David et al. (2024), Al-Azab et al. (2024)

---

## 🤝 Acknowledgments

**Supervision:**
- Prof. Dr. Johanna Klughammer (Primary Supervisor)
- Prof. Dr. Wolfgang Enard (Internal Supervisor)
- Dr. Tobias Straub (HPC Technical Support - BMC Bioinformatics Core Facility)

**Institution:**
- Faculty of Biology, Ludwig-Maximilians-Universität München
- Gene Center Munich (Klughammer Lab - Systems Biology)

---

## 📧 Contact

**Author:** Merve Görkem Durmaz  
**Email:** m.gorkemdurmaz@gmail.com  
**LinkedIn:** [linkedin.com/in/merve-görkem-durmaz-50902616a](https://www.linkedin.com/in/merve-goerkem-durmaz-50902616a)  
**GitHub:** [github.com/gorkem8d](https://github.com/gorkem8d)  
**ORCID:** [0000-0003-2106-2860](https://orcid.org/0000-0003-2106-2860)

---

## 📝 License

This pipeline and methodology are available for academic and research purposes. For commercial use or collaboration inquiries, please contact the author.

---

## ⚠️ Important Notes

1. **RNA-seq Limitations:** Variant calling from RNA-seq has inherent limitations compared to DNA sequencing
2. **Coverage Variability:** Gene expression levels affect coverage, requiring normalization
3. **RNA Editing:** Pipeline accounts for RNA editing events that could be mistaken for genomic variants
4. **Validation Required:** All high-priority variants should undergo experimental validation
5. **Clinical Application:** This is a research tool; clinical decisions require comprehensive genetic counseling

---

**Last Updated:** April 2025  
**Pipeline Version:** 1.0  
**GATK Version:** 4.2.6.1
