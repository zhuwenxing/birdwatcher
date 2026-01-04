"""
Hatch build hook to compile Go binary and set platform-specific wheel tags.
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


# Platform tag mappings
PLATFORM_TAGS = {
    ("linux", "amd64"): "manylinux_2_17_x86_64",
    ("linux", "arm64"): "manylinux_2_17_aarch64",
    ("darwin", "amd64"): "macosx_10_9_x86_64",
    ("darwin", "arm64"): "macosx_11_0_arm64",
}


def get_platform_info():
    """Get normalized OS and architecture."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        raise RuntimeError(f"Unsupported architecture: {machine}")

    if system == "darwin":
        os_name = "darwin"
    elif system == "linux":
        os_name = "linux"
    else:
        raise RuntimeError(
            f"Unsupported operating system: {system}. "
            "Only Linux and macOS are supported."
        )

    return os_name, arch


class GoBuildHook(BuildHookInterface):
    """Build hook that compiles Go binary and sets platform wheel tag."""

    PLUGIN_NAME = "go-build"

    def initialize(self, version, build_data):
        """Called before the build process starts."""
        if self.target_name != "wheel":
            return

        # Allow override via environment variables (for cross-compilation in CI)
        target_os = os.environ.get("PYBW_TARGET_OS")
        target_arch = os.environ.get("PYBW_TARGET_ARCH")

        if target_os and target_arch:
            os_name, arch = target_os, target_arch
        else:
            os_name, arch = get_platform_info()

        # Set platform-specific wheel tag
        platform_tag = PLATFORM_TAGS.get((os_name, arch))
        if not platform_tag:
            raise RuntimeError(f"No wheel tag for {os_name}/{arch}")

        build_data["tag"] = f"py3-none-{platform_tag}"
        print(f"Building wheel for: {os_name}/{arch} (tag: {build_data['tag']})")

        # Binary name (simple, no platform suffix)
        binary_name = "birdwatcher"

        # Paths
        project_root = Path(self.root)
        go_root = project_root.parent  # birdwatcher go project root
        bin_dir = project_root / "pybirdwatcher" / "bin"
        binary_path = bin_dir / binary_name

        # Check if Go source exists
        go_main = go_root / "cmd" / "birdwatcher" / "main.go"
        if not go_main.exists():
            print(f"Warning: Go source not found at {go_main}, skipping Go build")
            return

        # Always rebuild to ensure correct platform binary
        print(f"Building Go binary for {os_name}/{arch}...")

        # Create bin directory
        bin_dir.mkdir(parents=True, exist_ok=True)

        # Build command
        env = os.environ.copy()
        env["CGO_ENABLED"] = "0"
        env["GOOS"] = os_name
        env["GOARCH"] = arch

        cmd = [
            "go", "build",
            "-ldflags=-s -w",
            "-o", str(binary_path),
            "./cmd/birdwatcher",
        ]

        try:
            subprocess.run(
                cmd,
                cwd=str(go_root),
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            print(f"Successfully built: {binary_path}")

            # Make executable
            os.chmod(binary_path, 0o755)

        except subprocess.CalledProcessError as e:
            print(f"Error building Go binary: {e.stderr}", file=sys.stderr)
            raise RuntimeError(f"Failed to build Go binary: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError("'go' command not found. Please install Go.")
