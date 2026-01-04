# PyBirdwatcher

Python wrapper for [Birdwatcher](https://github.com/milvus-io/birdwatcher) - a debug and diagnostic tool for Milvus 2.0+.

## Installation

```bash
pip install pybirdwatcher
```

The package includes pre-compiled binaries for:
- Linux (amd64, arm64)
- macOS (amd64, arm64)
- Windows (amd64)

## Quick Start

```python
from pybirdwatcher import Birdwatcher

# Using context manager (recommended)
with Birdwatcher.connect("localhost:2379") as bw:
    # List sessions
    for session in bw.sessions:
        print(f"{session.server_name}: {session.address}")

    # List collections
    for collection in bw.collections:
        print(f"{collection.name}: {len(collection.fields)} fields")
```

## Pythonic API

### Sessions

```python
from pybirdwatcher import Birdwatcher

with Birdwatcher.connect("localhost:2379") as bw:
    # Property access
    sessions = bw.sessions

    # Get coordinators only
    coords = bw.get_coordinators()

    # Get specific node types
    querynodes = bw.get_nodes("querynode")
    datanodes = bw.get_nodes("datanode")

    for s in sessions:
        print(f"ID: {s.server_id}")
        print(f"Name: {s.server_name}")
        print(f"Address: {s.address}")
        print(f"Version: {s.version}")
        print(f"Is Coordinator: {s.is_coordinator}")
```

### Collections

```python
from pybirdwatcher import Birdwatcher, CollectionState

with Birdwatcher.connect("localhost:2379") as bw:
    # List all collections
    collections = bw.collections

    # Filter by database ID
    collections = bw.list_collections(db_id=1)

    # Get specific collection
    coll = bw.get_collection(name="my_collection")

    if coll:
        print(f"ID: {coll.id}")
        print(f"Name: {coll.name}")
        print(f"State: {coll.state}")
        print(f"Shards: {coll.num_shards}")

        # Access fields
        for field in coll.fields:
            print(f"  Field: {field.name} ({field.data_type})")

        # Get primary key field
        pk = coll.pk_field
        print(f"PK Field: {pk.name}")

        # Get vector fields
        for vf in coll.vector_fields:
            print(f"Vector: {vf.name}")
```

### Segments

```python
from pybirdwatcher import Birdwatcher, SegmentState, SegmentLevel

with Birdwatcher.connect("localhost:2379") as bw:
    # List all segments
    segments = bw.segments

    # Filter by collection
    segments = bw.list_segments(collection_id=123)

    # Filter by state (using enum or string)
    flushed = bw.list_segments(state=SegmentState.FLUSHED)
    growing = bw.list_segments(state="Growing")

    # Filter by level
    l0_segments = bw.list_segments(level=SegmentLevel.L0)

    # Get small segments (low fill ratio)
    small = bw.get_small_segments(collection_id=123, threshold=0.2)

    for seg in segments:
        print(f"ID: {seg.id}")
        print(f"State: {seg.state}")
        print(f"Level: {seg.level}")
        print(f"Rows: {seg.num_rows}/{seg.max_rows}")
        print(f"Fill Ratio: {seg.fill_ratio:.2%}")
        print(f"Is Small: {seg.is_small}")
```

### Statistics

```python
from pybirdwatcher import Birdwatcher

with Birdwatcher.connect("localhost:2379") as bw:
    # Get segment statistics
    stats = bw.get_segment_stats(collection_id=123)
    print(f"Total segments: {stats['total']}")
    print(f"Healthy segments: {stats['healthy_segments']}")
    print(f"Small segments: {stats['small_segments']}")
    print(f"Total rows: {stats['total_rows']}")
    print(f"By state: {stats['by_state']}")
    print(f"By level: {stats['by_level']}")

    # Get cluster summary
    summary = bw.get_cluster_summary()
    print(f"Components: {summary['total_components']}")
    print(f"Collections: {summary['total_collections']}")
```

### Other Resources

```python
with Birdwatcher.connect("localhost:2379") as bw:
    # Databases
    databases = bw.databases

    # Partitions
    partitions = bw.list_partitions(collection_id=123)

    # Indexes
    indexes = bw.list_indexes(collection_id=123)

    # Replicas
    replicas = bw.list_replicas(collection_id=123)

    # Checkpoints
    checkpoints = bw.list_checkpoints(collection_id=123)

    # Health check
    health = bw.healthz()
```

### Raw Commands

```python
with Birdwatcher.connect("localhost:2379") as bw:
    # Run any birdwatcher command
    output = bw.run("show channel-watch")

    # Get JSON output
    data = bw.run("show session", json_output=True)
```

## Data Models

All data is returned as Python dataclasses with proper typing:

```python
from pybirdwatcher import (
    Session,
    Collection,
    Segment,
    SegmentState,
    SegmentLevel,
    CollectionState,
    DataType,
    FieldSchema,
)

# Enums for filtering
SegmentState.FLUSHED
SegmentState.GROWING
SegmentState.DROPPED

SegmentLevel.L0
SegmentLevel.L1
SegmentLevel.L2

CollectionState.COLLECTION_CREATED

DataType.FLOAT_VECTOR
DataType.INT64
```

## Building from Source

```bash
cd python

# Build binary for current platform
./scripts/build_binary.sh

# Build for all platforms
./scripts/build_all_platforms.sh

# Build wheel
pip install build
python -m build
```

## License

Apache License 2.0
