#!/bin/bash
#
#SBATCH --job-name=graphblas_512g_test
#SBATCH --output=graphblas_512g_output.txt
#SBATCH --partition=extended_mem
#SBATCH --mem=512G
#SBATCH --cpus-per-task=32
#SBATCH --ntasks=1
#SBATCH --time=01:00:00

# Activate your environment
source ~/.bashrc
conda activate graphblas

# Start memory logger in background
log_memory() {
    JOB_ID=$1
    LOG_FILE="memory_usage_${JOB_ID}.log"
    echo "Starting memory logging to $LOG_FILE"
    echo "Time,RSS (KB),VSZ (KB)" > "$LOG_FILE"

    PYTHON_PID=""
    while [ -z "$PYTHON_PID" ]; do
        PYTHON_PID=$(pgrep -u $USER -f "python graphblas_shortest_path.py")
        sleep 1
    done

    while ps -p "$PYTHON_PID" > /dev/null; do
        ps -p "$PYTHON_PID" -o rss,vsz --no-headers | awk '{print strftime("%Y-%m-%d %H:%M:%S"),$1","$2}' >> "$LOG_FILE"
        sleep 5
    done
}

log_memory $SLURM_JOB_ID &
MONITOR_PID=$!

# Run your Python script
python graphblas_straight.py

# Kill logger and dump summary
kill $MONITOR_PID
echo "Final memory stats:" >> graphblas_512g_output.txt
sacct -j $SLURM_JOB_ID --format=JobID,MaxRSS,MaxVMSize,Elapsed,State >> graphblas_512g_output.txt
