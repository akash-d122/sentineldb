"""Domain enums for SentinelDB."""

from enum import Enum


class AlertType(str, Enum):
    cpu_high = "cpu_high"
    connection_saturation = "connection_saturation"
    slow_query = "slow_query"
    replication_lag = "replication_lag"
    db_unreachable = "db_unreachable"


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class EvidenceStatus(str, Enum):
    OK = "OK"
    WARN = "WARN"
    CRITICAL = "CRITICAL"
    UNAVAILABLE = "UNAVAILABLE"


class IncidentStatus(str, Enum):
    queued = "queued"
    collecting = "collecting"
    analyzing = "analyzing"
    report_ready = "report_ready"
    failed = "failed"


class RCAStrength(str, Enum):
    High = "High"
    Medium = "Medium"
    Low = "Low"
