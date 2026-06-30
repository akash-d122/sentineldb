"""Domain enums for SentinelDB."""

from enum import StrEnum


class AlertType(StrEnum):
    cpu_high = "cpu_high"
    connection_saturation = "connection_saturation"
    slow_query = "slow_query"
    replication_lag = "replication_lag"
    db_unreachable = "db_unreachable"


class Severity(StrEnum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class EvidenceStatus(StrEnum):
    OK = "OK"
    WARN = "WARN"
    CRITICAL = "CRITICAL"
    UNAVAILABLE = "UNAVAILABLE"


class IncidentStatus(StrEnum):
    queued = "queued"
    collecting = "collecting"
    analyzing = "analyzing"
    report_ready = "report_ready"
    failed = "failed"


class RCAStrength(StrEnum):
    High = "High"
    Medium = "Medium"
    Low = "Low"
