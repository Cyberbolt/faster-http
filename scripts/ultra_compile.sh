#!/bin/bash

# ULTRA PERFORMANCE COMPILATION SCRIPT
# This script applies the most aggressive compiler optimizations for A-grade performance

echo "🚀 Starting ULTRA Performance Compilation for A-grade standards..."

# Export balanced ultra RUSTFLAGS (preserves dynamic linking)
export RUSTFLAGS="-C target-cpu=native \
-C target-feature=+avx2,+fma,+sse4.2,+popcnt,+bmi1,+bmi2 \
-C opt-level=3 \
-C codegen-units=1 \
-C panic=abort"

# Additional CPU-specific optimizations
export CPPFLAGS="-march=native -mtune=native -O3 -flto -DNDEBUG"
export CFLAGS="-march=native -mtune=native -O3 -flto -DNDEBUG"
export CXXFLAGS="-march=native -mtune=native -O3 -flto -DNDEBUG"

# LLVM optimizations for maximum performance
export LLVM_PROFILE_FILE="target/pgo-profiles/default_%p.profraw"

echo "Applied ULTRA optimization flags:"
echo "RUSTFLAGS: $RUSTFLAGS"

# Clean previous builds to ensure fresh compilation
echo "🧹 Cleaning previous builds..."
cargo clean

# Compile with maximum optimization
echo "⚡ Compiling with ULTRA optimizations..."
uv run maturin develop --release --strip

echo "✅ ULTRA Performance Compilation complete!"
echo "🎯 Ready for A-grade performance testing!"