#!/bin/bash

# Release Build Compilation Script
# This script applies compiler configurations for release builds

echo "Starting release compilation..."

# Export release build RUSTFLAGS (preserves dynamic linking)
export RUSTFLAGS="-C target-cpu=native \
-C target-feature=+avx2,+fma,+sse4.2,+popcnt,+bmi1,+bmi2 \
-C opt-level=3 \
-C codegen-units=1 \
-C panic=abort"

# Additional CPU-specific configurations
export CPPFLAGS="-march=native -mtune=native -O3 -flto -DNDEBUG"
export CFLAGS="-march=native -mtune=native -O3 -flto -DNDEBUG"
export CXXFLAGS="-march=native -mtune=native -O3 -flto -DNDEBUG"

# LLVM configurations for release builds
export LLVM_PROFILE_FILE="target/pgo-profiles/default_%p.profraw"

echo "Applied release build flags:"
echo "RUSTFLAGS: $RUSTFLAGS"

# Clean previous builds to ensure fresh compilation
echo "Cleaning previous builds..."
cargo clean

# Compile with release configuration
echo "Compiling with release settings..."
uv run maturin develop --release --strip

echo "Release compilation complete."
echo "Build ready for testing."