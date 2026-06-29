"""Instance registry Pydantic models.

Only InstanceConfig is defined for V1A.
CloudResourceConfig and MonitoringConfig are deferred to V1B.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


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
    cloud: str | None = None
    monitoring: str | None = None
