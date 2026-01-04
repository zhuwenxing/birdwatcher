"""
PyBirdwatcher - Python wrapper for Birdwatcher (Milvus debug tool)
"""

from .client import Birdwatcher, BirdwatcherError, ConnectionError
from .models import (
    Collection,
    Checkpoint,
    CollectionState,
    Database,
    DataType,
    FieldSchema,
    Index,
    Partition,
    Replica,
    Segment,
    SegmentLevel,
    SegmentState,
    Session,
)
from .version import __version__

__all__ = [
    # Client
    "Birdwatcher",
    "BirdwatcherError",
    "ConnectionError",
    # Models
    "Collection",
    "Checkpoint",
    "CollectionState",
    "Database",
    "DataType",
    "FieldSchema",
    "Index",
    "Partition",
    "Replica",
    "Segment",
    "SegmentLevel",
    "SegmentState",
    "Session",
    # Version
    "__version__",
]
