"""
CLI entry point for pybirdwatcher.

This module provides a command-line interface that passes through
all arguments to the bundled birdwatcher binary.
"""

import subprocess
import sys

from .binary import get_binary_path


def main():
    """
    Main CLI entry point - passes through to birdwatcher binary.

    Usage:
        pybirdwatcher [birdwatcher args...]
        pybirdwatcher which  # Print path to bundled binary

    Examples:
        pybirdwatcher -olc "connect --etcd localhost:2379 --auto, show session"
        pybirdwatcher --simple
    """
    # Subcommand to print binary path (like "which birdwatcher")
    if len(sys.argv) > 1 and sys.argv[1] == "which":
        print(get_binary_path())
        return 0

    # Pass all arguments to birdwatcher binary
    binary = get_binary_path()
    return subprocess.call([str(binary)] + sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
