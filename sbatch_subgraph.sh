#!/bin/bash
#
#SBATCH --job-name=001
#SBATCH --output=subgraph.txt
#SBATCH --partition=extended_mem
#SBATCH --mem=800G
#SBATCH --cpus-per-task=16  # Number of CPU cores per task
#SBATCH --ntasks=1          # Number of tasks (set to 1 if you only need one task)
#SBATCH --time=14-00:00:00  # Set time limit to maximum allowed (14 days)

# Initialize conda for bash (assuming bash shell)
source ~/.bashrc

# Activate the conda environment
conda activate graphblas

# Run your Python script
python subgraph_graphblas.py
