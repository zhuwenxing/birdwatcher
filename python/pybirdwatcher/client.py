"""
Birdwatcher Python Client - Pythonic API for Milvus debugging.
"""

import json
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional, Union

from .binary import get_binary_path
from .models import (
    Collection,
    Checkpoint,
    Database,
    Index,
    Partition,
    Replica,
    Segment,
    SegmentLevel,
    SegmentState,
    Session,
)


class BirdwatcherError(Exception):
    """Exception raised when birdwatcher command fails."""
    pass


class ConnectionError(BirdwatcherError):
    """Exception raised when connection fails."""
    pass


class Birdwatcher:
    """
    Pythonic client for Birdwatcher - Milvus debug and diagnostic tool.

    Example:
        >>> from pybirdwatcher import Birdwatcher
        >>>
        >>> # Using context manager (recommended)
        >>> with Birdwatcher.connect("localhost:2379") as bw:
        ...     for session in bw.sessions:
        ...         print(f"{session.server_name}: {session.address}")
        ...
        ...     for collection in bw.collections:
        ...         print(f"{collection.name}: {len(collection.fields)} fields")
        >>>
        >>> # Without context manager
        >>> bw = Birdwatcher()
        >>> bw.connect("localhost:2379")
        >>> sessions = bw.list_sessions()
    """

    def __init__(self, binary_path: Optional[str] = None):
        """
        Initialize Birdwatcher client.

        Args:
            binary_path: Optional path to birdwatcher binary.
                        If not provided, uses the bundled binary.
        """
        if binary_path:
            self._binary = Path(binary_path)
        else:
            self._binary = get_binary_path()

        self._etcd_addr: Optional[str] = None
        self._root_path: Optional[str] = None
        self._auto_detect: bool = False
        self._timeout = 30

    @classmethod
    @contextmanager
    def connect(
        cls,
        etcd_addr: str,
        root_path: Optional[str] = None,
        auto_detect: bool = True,
        binary_path: Optional[str] = None,
    ) -> Iterator["Birdwatcher"]:
        """
        Context manager for connecting to etcd.

        Args:
            etcd_addr: etcd address (e.g., "localhost:2379")
            root_path: Milvus root path in etcd (e.g., "by-dev")
            auto_detect: Auto detect root path (default True)
            binary_path: Optional path to birdwatcher binary

        Yields:
            Connected Birdwatcher instance

        Example:
            >>> with Birdwatcher.connect("localhost:2379") as bw:
            ...     print(bw.list_sessions())
        """
        client = cls(binary_path)
        client._connect(etcd_addr, root_path, auto_detect)
        try:
            yield client
        finally:
            pass  # No cleanup needed for subprocess-based client

    def _connect(
        self,
        etcd_addr: str,
        root_path: Optional[str] = None,
        auto_detect: bool = True,
    ) -> None:
        """Configure etcd connection."""
        self._etcd_addr = etcd_addr
        self._root_path = root_path
        self._auto_detect = auto_detect

    def set_timeout(self, timeout: int) -> "Birdwatcher":
        """
        Set command timeout.

        Args:
            timeout: Timeout in seconds

        Returns:
            Self for chaining
        """
        self._timeout = timeout
        return self

    def _run_command(self, command: str, timeout: Optional[int] = None) -> str:
        """Run a birdwatcher command and return output."""
        if timeout is None:
            timeout = self._timeout

        full_cmd = command
        if self._etcd_addr and not command.startswith("connect"):
            connect_cmd = f"connect --etcd {self._etcd_addr}"
            if self._root_path:
                connect_cmd += f" --rootPath {self._root_path}"
            if self._auto_detect:
                connect_cmd += " --auto"
            full_cmd = f"{connect_cmd}, {command}"

        try:
            result = subprocess.run(
                [str(self._binary), "-olc", full_cmd],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                if "failed to connect" in error_msg.lower():
                    raise ConnectionError(f"Failed to connect to etcd: {error_msg}")
                raise BirdwatcherError(f"Command failed: {error_msg}")

            return result.stdout

        except subprocess.TimeoutExpired:
            raise BirdwatcherError(f"Command timed out after {timeout}s")
        except FileNotFoundError:
            raise BirdwatcherError(f"Binary not found: {self._binary}")

    def _run_json(self, command: str, timeout: Optional[int] = None) -> Any:
        """Run command with JSON output format."""
        output = self._run_command(f"{command} --format json", timeout)
        if not output.strip():
            return []

        # Find JSON array or object in output (skip any prefix messages)
        json_start = -1
        for i, char in enumerate(output):
            if char in "[{":
                json_start = i
                break

        if json_start == -1:
            return []

        json_str = output[json_start:]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise BirdwatcherError(f"Failed to parse JSON: {e}\nOutput: {output}")

    # ========== Properties for Pythonic access ==========

    @property
    def sessions(self) -> list[Session]:
        """
        Get all online Milvus component sessions.

        Returns:
            List of Session objects
        """
        return self.list_sessions()

    @property
    def collections(self) -> list[Collection]:
        """
        Get all collections.

        Returns:
            List of Collection objects
        """
        return self.list_collections()

    @property
    def segments(self) -> list[Segment]:
        """
        Get all segments.

        Returns:
            List of Segment objects
        """
        return self.list_segments()

    @property
    def databases(self) -> list[Database]:
        """
        Get all databases.

        Returns:
            List of Database objects
        """
        return self.list_databases()

    # ========== Session Methods ==========

    def list_sessions(self) -> list[Session]:
        """List all online Milvus component sessions."""
        data = self._run_json("show session")
        return [Session.from_dict(item) for item in data]

    def get_coordinators(self) -> list[Session]:
        """Get all coordinator sessions."""
        return [s for s in self.list_sessions() if s.is_coordinator]

    def get_nodes(self, component: Optional[str] = None) -> list[Session]:
        """
        Get node sessions.

        Args:
            component: Optional filter by component type
                      (e.g., "querynode", "datanode", "indexnode", "proxy")

        Returns:
            List of node sessions
        """
        sessions = [s for s in self.list_sessions() if not s.is_coordinator]
        if component:
            sessions = [s for s in sessions if component.lower() in s.component_type]
        return sessions

    # ========== Collection Methods ==========

    def list_collections(
        self,
        db_id: Optional[int] = None,
        state: Optional[str] = None,
    ) -> list[Collection]:
        """
        List collections.

        Args:
            db_id: Optional database ID filter
            state: Optional state filter (e.g., "CollectionCreated")

        Returns:
            List of Collection objects
        """
        cmd = "show collections"
        if db_id is not None:
            cmd += f" --dbid {db_id}"
        if state:
            cmd += f" --state {state}"

        data = self._run_json(cmd)
        return [Collection.from_dict(item) for item in data]

    def get_collection(
        self,
        collection_id: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Optional[Collection]:
        """
        Get a specific collection.

        Args:
            collection_id: Collection ID
            name: Collection name

        Returns:
            Collection object or None if not found
        """
        cmd = "show collections"
        if collection_id:
            cmd += f" --id {collection_id}"
        if name:
            cmd += f" --name {name}"

        data = self._run_json(cmd)
        if data:
            return Collection.from_dict(data[0])
        return None

    # ========== Segment Methods ==========

    def list_segments(
        self,
        collection_id: Optional[int] = None,
        partition_id: Optional[int] = None,
        state: Optional[Union[str, SegmentState]] = None,
        level: Optional[Union[str, SegmentLevel]] = None,
    ) -> list[Segment]:
        """
        List segments.

        Args:
            collection_id: Optional collection ID filter
            partition_id: Optional partition ID filter
            state: Optional state filter (e.g., "Flushed", SegmentState.FLUSHED)
            level: Optional level filter (e.g., "L0", SegmentLevel.L0)

        Returns:
            List of Segment objects
        """
        cmd = "show segment"
        if collection_id:
            cmd += f" --collection {collection_id}"
        if partition_id:
            cmd += f" --partition {partition_id}"
        if state:
            state_str = state.name if isinstance(state, SegmentState) else state
            cmd += f" --state {state_str}"
        if level:
            level_str = level.name if isinstance(level, SegmentLevel) else level
            cmd += f" --level {level_str}"

        data = self._run_json(cmd)
        return [Segment.from_dict(item) for item in data]

    def get_segment(self, segment_id: int) -> Optional[Segment]:
        """
        Get a specific segment.

        Args:
            segment_id: Segment ID

        Returns:
            Segment object or None if not found
        """
        cmd = f"show segment --segment {segment_id}"
        data = self._run_json(cmd)
        if data:
            return Segment.from_dict(data[0])
        return None

    def get_small_segments(
        self,
        collection_id: Optional[int] = None,
        threshold: float = 0.2,
    ) -> list[Segment]:
        """
        Get segments with low fill ratio.

        Args:
            collection_id: Optional collection ID filter
            threshold: Fill ratio threshold (default 0.2 = 20%)

        Returns:
            List of small segments
        """
        segments = self.list_segments(
            collection_id=collection_id,
            state=SegmentState.FLUSHED,
        )
        return [s for s in segments if s.fill_ratio < threshold]

    # ========== Database Methods ==========

    def list_databases(self) -> list[Database]:
        """List all databases."""
        data = self._run_json("show database")
        return [Database.from_dict(item) for item in data]

    # ========== Partition Methods ==========

    def list_partitions(self, collection_id: int) -> list[Partition]:
        """
        List partitions for a collection.

        Args:
            collection_id: Collection ID

        Returns:
            List of Partition objects
        """
        cmd = f"show partition --collection {collection_id}"
        data = self._run_json(cmd)
        return [Partition.from_dict(item) for item in data]

    # ========== Index Methods ==========

    def list_indexes(self, collection_id: Optional[int] = None) -> list[Index]:
        """
        List indexes.

        Args:
            collection_id: Optional collection ID filter

        Returns:
            List of Index objects
        """
        cmd = "show index"
        if collection_id:
            cmd += f" --collection {collection_id}"
        data = self._run_json(cmd)
        return [Index.from_dict(item) for item in data]

    # ========== Replica Methods ==========

    def list_replicas(self, collection_id: Optional[int] = None) -> list[Replica]:
        """
        List replicas.

        Args:
            collection_id: Optional collection ID filter

        Returns:
            List of Replica objects
        """
        cmd = "show replica"
        if collection_id:
            cmd += f" --collection {collection_id}"
        data = self._run_json(cmd)
        return [Replica.from_dict(item) for item in data]

    # ========== Checkpoint Methods ==========

    def list_checkpoints(self, collection_id: int) -> list[Checkpoint]:
        """
        List channel checkpoints.

        Args:
            collection_id: Collection ID

        Returns:
            List of Checkpoint objects
        """
        cmd = f"show checkpoint --collection {collection_id}"
        data = self._run_json(cmd)
        return [Checkpoint.from_dict(item) for item in data]

    # ========== Health Check ==========

    def healthz(self) -> list[dict]:
        """
        Run health check.

        Returns:
            List of health check results
        """
        return self._run_json("healthz")

    # ========== Utility Methods ==========

    def version(self) -> str:
        """Get birdwatcher version."""
        return self._run_command("version").strip()

    def run(self, command: str, json_output: bool = False) -> Any:
        """
        Run arbitrary birdwatcher command.

        Args:
            command: The command to run
            json_output: If True, parse output as JSON

        Returns:
            Command output (parsed JSON if json_output=True)
        """
        if json_output:
            return self._run_json(command)
        return self._run_command(command)

    # ========== Statistics ==========

    def get_segment_stats(
        self,
        collection_id: Optional[int] = None,
    ) -> dict:
        """
        Get segment statistics.

        Args:
            collection_id: Optional collection ID filter

        Returns:
            Dictionary with segment statistics
        """
        segments = self.list_segments(collection_id=collection_id)

        stats = {
            "total": len(segments),
            "by_state": {},
            "by_level": {},
            "total_rows": 0,
            "healthy_segments": 0,
            "small_segments": 0,
        }

        for seg in segments:
            # Count by state
            state_name = seg.state.name
            stats["by_state"][state_name] = stats["by_state"].get(state_name, 0) + 1

            # Count by level
            level_name = seg.level.name
            stats["by_level"][level_name] = stats["by_level"].get(level_name, 0) + 1

            # Accumulate rows (exclude dropped)
            if seg.state != SegmentState.DROPPED:
                stats["total_rows"] += seg.num_rows
                stats["healthy_segments"] += 1

            # Count small segments
            if seg.state == SegmentState.FLUSHED and seg.is_small:
                stats["small_segments"] += 1

        return stats

    def get_cluster_summary(self) -> dict:
        """
        Get cluster summary.

        Returns:
            Dictionary with cluster summary
        """
        sessions = self.list_sessions()
        collections = self.list_collections()

        components = {}
        for s in sessions:
            comp = s.component_type
            if comp not in components:
                components[comp] = []
            components[comp].append({
                "id": s.server_id,
                "address": s.address,
                "version": s.version,
            })

        return {
            "total_components": len(sessions),
            "components": components,
            "total_collections": len(collections),
            "collections": [
                {"id": c.id, "name": c.name, "state": c.state.name}
                for c in collections
            ],
        }
