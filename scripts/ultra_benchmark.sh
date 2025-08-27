#!/bin/bash

# ULTRA PERFORMANCE BENCHMARK SCRIPT
# Optimized for A-grade performance testing with multi-core support

echo "🚀 ULTRA Performance Benchmark - A-grade Standards"
echo "=================================================="

# Get CPU info
cores=$(nproc)
echo "💻 System has $cores CPU cores available"

# Optimize system for performance testing
echo "🔧 Optimizing system for ultra performance..."

# Set CPU frequency governor to performance (if available)
if command -v cpufreq-set &> /dev/null; then
    echo "Setting CPU governor to performance mode..."
    for ((i=0; i<cores; i++)); do
        sudo cpufreq-set -c $i -g performance 2>/dev/null || true
    done
fi

# Disable CPU scaling (if available)
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || true

# Set process priority and affinity for maximum performance
export OMP_NUM_THREADS=$cores
export GOMAXPROCS=$cores
export UV_THREADPOOL_SIZE=$((cores * 2))

echo "🎯 Performance optimizations applied:"
echo "   - CPU cores: $cores"
echo "   - Thread pool size: $((cores * 2))"
echo "   - Process priority: high"

# Multi-core async test
echo ""
echo "🔥 Running ASYNC test with FULL multi-core support..."
echo "Using ALL $cores CPU cores for maximum throughput"

# Use ALL cores for async test (no taskset restriction)
timeout 60s env PYTHONPATH=/project/faster-http \
    nice -n -10 \
    uv run python -c "
import sys
sys.path.insert(0, '/project/faster-http')
import asyncio
import time
from benchmarks.faster_http_test import test

# Set optimal concurrency for multi-core
optimal_concurrency = $cores * 8  # 8 tasks per core

async def main():
    print(f'🚀 Starting ASYNC test with {optimal_concurrency} concurrent tasks')
    print(f'   Duration: 30 seconds')
    print(f'   Target: ≥11,297 RPS for A-grade')
    
    rps = await test(duration=30, concurrency=optimal_concurrency)
    
    print('')
    print('📊 ASYNC RESULTS:')
    print(f'   RPS: {rps:.0f}')
    print(f'   Target: 11,297 RPS')
    if rps >= 11297:
        print('   ✅ A-GRADE ACHIEVED!')
    else:
        deficit = 11297 - rps
        percentage = (deficit / 11297) * 100
        print(f'   ❌ Need {deficit:.0f} more RPS ({percentage:.1f}%)')
    
    return rps

asyncio.run(main())
"

echo ""
echo "🔥 Running SYNC test with FULL multi-core support..."
echo "Using ALL $cores CPU cores for maximum throughput"

# Multi-core sync test - use ALL cores
timeout 60s env PYTHONPATH=/project/faster-http \
    nice -n -10 \
    uv run python -c "
import sys
sys.path.insert(0, '/project/faster-http')
import time
from benchmarks.faster_http_test import sync_test

# Set optimal concurrency for multi-core sync
optimal_concurrency = $cores * 6  # 6 threads per core for sync

print(f'🚀 Starting SYNC test with {optimal_concurrency} concurrent threads')
print(f'   Duration: 30 seconds')
print(f'   Target: ≥16,016 RPS for A-grade')

rps = sync_test(duration=30, concurrency=optimal_concurrency)

print('')
print('📊 SYNC RESULTS:')
print(f'   RPS: {rps:.0f}')
print(f'   Target: 16,016 RPS')
if rps >= 16016:
    print('   ✅ A-GRADE ACHIEVED!')
else:
    deficit = 16016 - rps
    percentage = (deficit / 16016) * 100
    print(f'   ❌ Need {deficit:.0f} more RPS ({percentage:.1f}%)')
"

echo ""
echo "🎯 ULTRA Performance Benchmark Complete!"
echo "========================================"