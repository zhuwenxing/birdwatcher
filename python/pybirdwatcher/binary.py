"""
Locate the bundled birdwatcher binary.
"""

import os
import platform
from pathlib import Path


def get_binary_path() -> Path:
    """
    Get the path to the bundled birdwatcher binary.

    The binary is located in the 'bin' directory within the package.
    Each platform-specific wheel contains a single 'birdwatcher' binary
    compiled for that platform.
    """
    # Validate current platform is supported
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    if system not in ("darwin", "linux"):
        raise RuntimeError(
            f"Unsupported operating system: {system}. "
            "Only Linux and macOS are supported."
        )

    # Look for binary in package's bin directory
    package_dir = Path(__file__).parent
    binary_path = package_dir / "bin" / "birdwatcher"

    if not binary_path.exists():
        raise FileNotFoundError(
            f"Birdwatcher binary not found at {binary_path}. "
            f"This wheel may not be built for {system}-{arch}. "
            "Please install the correct platform-specific wheel."
        )

    # Ensure executable permission
    if not os.access(binary_path, os.X_OK):
        os.chmod(binary_path, 0o755)

    return binary_path
