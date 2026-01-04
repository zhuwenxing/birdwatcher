#!/bin/bash
# Build birdwatcher binaries for all supported platforms
# Creates platform-suffixed binaries for local development/testing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_ROOT="$SCRIPT_DIR/.."
BIN_DIR="$PYTHON_ROOT/pybirdwatcher/bin"

mkdir -p "$BIN_DIR"

cd "$PROJECT_ROOT"

# Define platforms (Windows not supported by birdwatcher)
PLATFORMS=(
    "linux/amd64"
    "linux/arm64"
    "darwin/amd64"
    "darwin/arm64"
)

for platform in "${PLATFORMS[@]}"; do
    OS="${platform%/*}"
    ARCH="${platform#*/}"
    # Use platform suffix for multi-platform builds
    BINARY_NAME="birdwatcher-${OS}-${ARCH}"

    echo "Building for ${OS}/${ARCH}..."

    CGO_ENABLED=0 GOOS=$OS GOARCH=$ARCH go build \
        -ldflags="-s -w" \
        -o "$BIN_DIR/$BINARY_NAME" \
        ./cmd/birdwatcher

    echo "  -> $BIN_DIR/$BINARY_NAME"
done

echo ""
echo "All binaries built:"
ls -lh "$BIN_DIR"
