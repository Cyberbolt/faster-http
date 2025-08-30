#!/bin/bash

# taskset script to assign a free CPU core for command execution and ensure it runs only on that core
# Usage: ./auto_taskset.sh "command"

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"command\"" >&2
    echo "Example: $0 \"echo Hello\"" >&2
    exit 1
fi

# Check if taskset is available
if ! command -v taskset >/dev/null 2>&1; then
    echo "Error: taskset command not found. Please install util-linux package." >&2
    exit 1
fi

# Get number of CPU cores
cores=$(nproc)
if [ $? -ne 0 ] || [ "$cores" -le 0 ]; then
    echo "Error: Failed to get CPU core count" >&2
    exit 1
fi

echo "System has $cores CPU cores"

# Simple strategy: avoid core 0, rotate through other cores
if [ "$cores" -gt 1 ]; then
    # Randomly select a core between 1 and cores-1
    core=$((1 + RANDOM % (cores - 1)))
else
    core=0
fi

# Validate selected core
if [ "$core" -lt 0 ] || [ "$core" -ge "$cores" ]; then
    echo "Error: Invalid CPU core selected: $core" >&2
    exit 1
fi

echo "Selected CPU core: $core"
echo "Executing: taskset -c $core $1"

# Execute command and preserve exit code
taskset -c $core $1
exit_code=$?

# Exit with the same code as the executed command
exit $exit_code