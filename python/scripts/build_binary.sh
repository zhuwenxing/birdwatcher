#!/bin/bash
# Build birdwatcher binary for the current platform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON_ROOT="$SCRIPT_DIR/.."
BIN_DIR="$PYTHON_ROOT/pybirdwatcher/bin"

# Detect OS and architecture
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64|amd64)
        ARCH="amd64"
        ;;
    arm64|aarch64)
        ARCH="arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

case "$OS" in
    darwin)
        OS="darwin"
        ;;
    linux)
        OS="linux"
        ;;
    mingw*|msys*|cygwin*)
        OS="windows"
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac

BINARY_NAME="birdwatcher-${OS}-${ARCH}"
if [ "$OS" = "windows" ]; then
    BINARY_NAME="${BINARY_NAME}.exe"
fi

echo "Building birdwatcher for ${OS}/${ARCH}..."

mkdir -p "$BIN_DIR"

cd "$PROJECT_ROOT"

# Build with CGO disabled for maximum portability
CGO_ENABLED=0 GOOS=$OS GOARCH=$ARCH go build \
    -ldflags="-s -w" \
    -o "$BIN_DIR/$BINARY_NAME" \
    ./cmd/birdwatcher

echo "Built: $BIN_DIR/$BINARY_NAME"
ls -lh "$BIN_DIR/$BINARY_NAME"
