"""Instance registry Pydantic models.

CloudResourceConfig and MonitoringConfig are included for V1B.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class MonitoringConfig(BaseModel):
    """Configuration for external monitoring systems like Prometheus or PMM."""

    model_config = ConfigDict(frozen=True)

    provider: Literal["prometheus", "cloudwatch"]
    url: str | None = None
    job_name: str | None = None
    pmm_service_name: str | None = None


class CloudResourceConfig(BaseModel):
    """Configuration for cloud resources like AWS RDS."""

    model_config = ConfigDict(frozen=True)

    provider: Literal["aws"]
    type: Literal["rds", "ec2"]
    instance_id: str
    region: str


class InstanceConfig(BaseModel):
    """Full connection configuration for a monitored database instance."""

    model_config = ConfigDict(frozen=True)

    instance_id: str
    engine: str  # "postgresql" | "mysql"
    host: str
    port: int
    database: str
    username: str
    credential_ref: str
    cloud: CloudResourceConfig | None = None
    monitoring: MonitoringConfig | None = None
