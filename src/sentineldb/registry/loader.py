"""Instance registry loader — resolves instance_id to InstanceConfig from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from sentineldb.registry.models import InstanceConfig


class InstanceNotRegistered(Exception):
    def __init__(self, instance_id: str) -> None:
        super().__init__(f"Instance not registered: {instance_id!r}")
        self.instance_id = instance_id


class InstanceRegistry:
    """Loads instances.yaml and resolves instance_id → InstanceConfig."""

    def __init__(self, path: str | Path = "instances.yaml") -> None:
        self._path = Path(path)
        self._registry: dict[str, InstanceConfig] = {}
        self._loaded = False

    def _load(self) -> dict[str, InstanceConfig]:
        if not self._path.exists():
            return {}
        with self._path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            raise ValueError(f"instances.yaml must be a mapping, got {type(data).__name__}")
        return {
            instance_id: InstanceConfig(instance_id=instance_id, **cfg)
            for instance_id, cfg in data.items()
        }

    def resolve(self, instance_id: str) -> InstanceConfig:
        if not self._loaded:
            self._registry = self._load()
            self._loaded = True
        try:
            return self._registry[instance_id]
        except KeyError:
            raise InstanceNotRegistered(instance_id)

    def register(self, instance_id: str, config: dict) -> None:
        if not self._loaded:
            self._registry = self._load()
            self._loaded = True

        if self._path.exists():
            with self._path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        else:
            data = {}

        data[instance_id] = config

        with self._path.open("w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh)

        self._registry[instance_id] = InstanceConfig(instance_id=instance_id, **config)
