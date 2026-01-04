"""
Data models for Birdwatcher.

These models provide Pythonic representations of Milvus metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class SegmentState(Enum):
    """Segment state enumeration."""
    SEGMENT_STATE_NONE = 0
    NOT_EXIST = 1
    GROWING = 2
    SEALED = 3
    FLUSHED = 4
    FLUSHING = 5
    DROPPED = 6
    IMPORTING = 7

    @classmethod
    def from_string(cls, s: str) -> "SegmentState":
        mapping = {
            "SegmentStateNone": cls.SEGMENT_STATE_NONE,
            "NotExist": cls.NOT_EXIST,
            "Growing": cls.GROWING,
            "Sealed": cls.SEALED,
            "Flushed": cls.FLUSHED,
            "Flushing": cls.FLUSHING,
            "Dropped": cls.DROPPED,
            "Importing": cls.IMPORTING,
        }
        return mapping.get(s, cls.SEGMENT_STATE_NONE)


class SegmentLevel(Enum):
    """Segment level enumeration."""
    LEGACY = 0
    L0 = 1
    L1 = 2
    L2 = 3

    @classmethod
    def from_string(cls, s: str) -> "SegmentLevel":
        mapping = {
            "Legacy": cls.LEGACY,
            "L0": cls.L0,
            "L1": cls.L1,
            "L2": cls.L2,
        }
        return mapping.get(s, cls.LEGACY)


class CollectionState(Enum):
    """Collection state enumeration."""
    COLLECTION_CREATED = 0
    COLLECTION_CREATING = 1
    COLLECTION_DROPPING = 2
    COLLECTION_DROPPED = 3

    @classmethod
    def from_string(cls, s: str) -> "CollectionState":
        mapping = {
            "CollectionCreated": cls.COLLECTION_CREATED,
            "CollectionCreating": cls.COLLECTION_CREATING,
            "CollectionDropping": cls.COLLECTION_DROPPING,
            "CollectionDropped": cls.COLLECTION_DROPPED,
        }
        return mapping.get(s, cls.COLLECTION_CREATED)


class DataType(Enum):
    """Field data type enumeration."""
    NONE = 0
    BOOL = 1
    INT8 = 2
    INT16 = 3
    INT32 = 4
    INT64 = 5
    FLOAT = 10
    DOUBLE = 11
    STRING = 20
    VARCHAR = 21
    ARRAY = 22
    JSON = 23
    GEOMETRY = 24
    TIMESTAMPTZ = 26
    BINARY_VECTOR = 100
    FLOAT_VECTOR = 101
    FLOAT16_VECTOR = 102
    BFLOAT16_VECTOR = 103
    SPARSE_FLOAT_VECTOR = 104
    INT8_VECTOR = 105

    @classmethod
    def from_value(cls, val) -> "DataType":
        """Convert from int or string to DataType."""
        if isinstance(val, int):
            for member in cls:
                if member.value == val:
                    return member
            return cls.NONE
        elif isinstance(val, str):
            return cls.__members__.get(val.upper().replace(" ", "_"), cls.NONE)
        return cls.NONE


@dataclass
class Session:
    """Milvus component session."""
    server_id: int
    server_name: str
    address: str
    hostname: str
    version: str
    lease_id: int
    exclusive: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            server_id=data.get("ServerID", 0),
            server_name=data.get("ServerName", ""),
            address=data.get("Address", ""),
            hostname=data.get("HostName", ""),
            version=data.get("Version", ""),
            lease_id=data.get("LeaseID", 0),
            exclusive=data.get("Exclusive", False),
        )

    @property
    def is_coordinator(self) -> bool:
        """Check if this session is a coordinator."""
        return "coord" in self.server_name.lower()

    @property
    def component_type(self) -> str:
        """Get the component type (e.g., 'querynode', 'datanode')."""
        return self.server_name.lower()


@dataclass
class FieldSchema:
    """Collection field schema."""
    field_id: int
    name: str
    data_type: DataType
    is_primary_key: bool = False
    auto_id: bool = False
    is_partition_key: bool = False
    is_clustering_key: bool = False
    is_dynamic: bool = False
    nullable: bool = False
    type_params: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "FieldSchema":
        return cls(
            field_id=data.get("fieldID", 0),
            name=data.get("name", ""),
            data_type=DataType.from_value(data.get("data_type", 0)),
            is_primary_key=data.get("is_primary_key", False),
            auto_id=data.get("autoID", False),
            is_partition_key=data.get("is_partition_key", False),
            is_clustering_key=data.get("is_clustering_key", False),
            is_dynamic=data.get("is_dynamic", False),
            nullable=data.get("nullable", False),
            type_params={kv["key"]: kv["value"] for kv in data.get("type_params", [])},
        )


@dataclass
class Collection:
    """Milvus collection metadata."""
    id: int
    name: str
    db_id: int
    state: CollectionState
    schema_version: int
    fields: list[FieldSchema]
    consistency_level: str
    virtual_channels: list[str]
    physical_channels: list[str]
    properties: dict
    create_time: Optional[datetime] = None
    enable_dynamic_field: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "Collection":
        schema = data.get("schema", {})
        fields_data = schema.get("fields", [])
        return cls(
            id=data.get("ID", 0),
            name=schema.get("name", ""),
            db_id=data.get("db_id", 0),
            state=CollectionState.from_string(data.get("state", "")),
            schema_version=schema.get("version", 0),
            fields=[FieldSchema.from_dict(f) for f in fields_data],
            consistency_level=data.get("consistency_level", ""),
            virtual_channels=data.get("virtual_channel_names", []),
            physical_channels=data.get("physical_channel_names", []),
            properties={p["key"]: p["value"] for p in data.get("properties", [])},
            enable_dynamic_field=schema.get("enable_dynamic_field", False),
        )

    @property
    def num_shards(self) -> int:
        """Number of shards (channels)."""
        return len(self.virtual_channels)

    def get_field(self, name: str) -> Optional[FieldSchema]:
        """Get field by name."""
        for f in self.fields:
            if f.name == name:
                return f
        return None

    @property
    def pk_field(self) -> Optional[FieldSchema]:
        """Get primary key field."""
        for f in self.fields:
            if f.is_primary_key:
                return f
        return None

    @property
    def vector_fields(self) -> list[FieldSchema]:
        """Get all vector fields."""
        vector_types = {
            DataType.BINARY_VECTOR,
            DataType.FLOAT_VECTOR,
            DataType.FLOAT16_VECTOR,
            DataType.BFLOAT16_VECTOR,
            DataType.SPARSE_FLOAT_VECTOR,
        }
        return [f for f in self.fields if f.data_type in vector_types]


@dataclass
class Segment:
    """Milvus segment metadata."""
    id: int
    collection_id: int
    partition_id: int
    state: SegmentState
    level: SegmentLevel
    num_rows: int
    max_rows: int
    insert_channel: str
    storage_version: int
    is_sorted: bool
    compaction_from: list[int]
    binlog_count: int = 0
    statslog_count: int = 0
    deltalog_count: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> "Segment":
        return cls(
            id=data.get("ID", 0),
            collection_id=data.get("CollectionID", 0),
            partition_id=data.get("PartitionID", 0),
            state=SegmentState.from_string(data.get("State", "")),
            level=SegmentLevel.from_string(data.get("Level", "")),
            num_rows=data.get("NumOfRows", 0),
            max_rows=data.get("MaxRowNum", 0),
            insert_channel=data.get("InsertChannel", ""),
            storage_version=data.get("StorageVersion", 0),
            is_sorted=data.get("IsSorted", False),
            compaction_from=data.get("CompactionFrom", []),
        )

    @property
    def fill_ratio(self) -> float:
        """Segment fill ratio (num_rows / max_rows)."""
        if self.max_rows == 0:
            return 0.0
        return self.num_rows / self.max_rows

    @property
    def is_small(self) -> bool:
        """Check if segment is considered small (<20% fill)."""
        return self.fill_ratio < 0.2


@dataclass
class Partition:
    """Milvus partition metadata."""
    id: int
    name: str
    collection_id: int
    state: str

    @classmethod
    def from_dict(cls, data: dict) -> "Partition":
        return cls(
            id=data.get("partition_id", 0),
            name=data.get("partition_name", ""),
            collection_id=data.get("collection_id", 0),
            state=data.get("state", ""),
        )


@dataclass
class Index:
    """Milvus index metadata."""
    index_id: int
    index_name: str
    collection_id: int
    field_id: int
    index_params: dict
    is_deleted: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "Index":
        return cls(
            index_id=data.get("index_id", 0),
            index_name=data.get("index_name", ""),
            collection_id=data.get("collection_id", 0),
            field_id=data.get("field_id", 0),
            index_params={p["key"]: p["value"] for p in data.get("index_params", [])},
            is_deleted=data.get("is_deleted", False),
        )


@dataclass
class Replica:
    """Milvus replica metadata."""
    replica_id: int
    collection_id: int
    resource_group: str
    nodes: list[int]

    @classmethod
    def from_dict(cls, data: dict) -> "Replica":
        return cls(
            replica_id=data.get("replicaID", 0),
            collection_id=data.get("collectionID", 0),
            resource_group=data.get("resource_group", ""),
            nodes=data.get("nodes", []),
        )


@dataclass
class Checkpoint:
    """Channel checkpoint."""
    channel: str
    msg_id: str
    timestamp: int
    position_time: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Checkpoint":
        return cls(
            channel=data.get("channel", ""),
            msg_id=data.get("msg_id", ""),
            timestamp=data.get("timestamp", 0),
        )


@dataclass
class Database:
    """Milvus database metadata."""
    id: int
    name: str
    state: str
    properties: dict

    @classmethod
    def from_dict(cls, data: dict) -> "Database":
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            state=data.get("state", ""),
            properties={p["key"]: p["value"] for p in data.get("properties", [])},
        )
