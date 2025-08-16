#!/bin/bash

# taskset script to assign a free CPU core for command execution and ensure it runs only on that core
# Usage: ./auto_taskset.sh "command"

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"command\""
    echo "Example: $0 \"echo Hello\""
    exit 1
fi

# Get number of CPU cores
cores=$(nproc)
echo "System has $cores CPU cores"

# Simple strategy: avoid core 0, rotate through other cores
if [ "$cores" -gt 1 ]; then
    # Randomly select a core between 1 and cores-1
    core=$((1 + RANDOM % (cores - 1)))
else
    core=0
fi

echo "Selected CPU core: $core"
echo "Executing: taskset -c $core $1"

# Execute command
taskset -c $core $1