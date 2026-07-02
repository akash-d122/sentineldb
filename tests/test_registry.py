"""Tests for the instance registry loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from sentineldb.registry.loader import InstanceNotRegistered, InstanceRegistry
from sentineldb.registry.models import InstanceConfig


@pytest.fixture
def registry(tmp_path: Path) -> InstanceRegistry:
    """Registry loaded from the real instances.yaml."""
    return InstanceRegistry(Path(__file__).parent.parent / "instances.yaml")


@pytest.fixture
def two_entry_registry(tmp_path: Path) -> InstanceRegistry:
    data = {
        "db-alpha": {
            "engine": "postgresql",
            "host": "alpha-host",
            "port": 5432,
            "database": "db_alpha",
            "username": "user_a",
            "credential_ref": "pg_alpha",
        },
        "db-beta": {
            "engine": "mysql",
            "host": "beta-host",
            "port": 3306,
            "database": "db_beta",
            "username": "user_b",
            "credential_ref": "my_beta",
        },
    }
    yaml_file = tmp_path / "instances.yaml"
    yaml_file.write_text(yaml.dump(data), encoding="utf-8")
    return InstanceRegistry(yaml_file)


def test_resolve_demo_instance(registry: InstanceRegistry) -> None:
    cfg = registry.resolve("db-demo-01")
    assert isinstance(cfg, InstanceConfig)
    assert cfg.instance_id == "db-demo-01"
    assert cfg.engine == "postgresql"
    assert cfg.port == 5432


def test_resolve_nonexistent_raises(registry: InstanceRegistry) -> None:
    with pytest.raises(InstanceNotRegistered) as exc_info:
        registry.resolve("does-not-exist")
    assert "does-not-exist" in str(exc_info.value)


def test_two_entry_registry_resolves_both(two_entry_registry: InstanceRegistry) -> None:
    alpha = two_entry_registry.resolve("db-alpha")
    beta = two_entry_registry.resolve("db-beta")
    assert alpha.engine == "postgresql"
    assert beta.engine == "mysql"


def test_malformed_yaml_raises_at_load_time(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "instances.yaml"
    bad_yaml.write_text("- this is a list not a mapping\n", encoding="utf-8")
    with pytest.raises(ValueError, match="mapping"):
        InstanceRegistry(bad_yaml).resolve("any")


def test_instance_config_cloud_none_valid(tmp_path: Path) -> None:
    data = {
        "local-01": {
            "engine": "postgresql",
            "host": "localhost",
            "port": 5432,
            "database": "mydb",
            "username": "user",
            "credential_ref": "pg_local",
            "cloud": None,
            "monitoring": None,
        }
    }
    yaml_file = tmp_path / "instances.yaml"
    yaml_file.write_text(yaml.dump(data), encoding="utf-8")
    reg = InstanceRegistry(yaml_file)
    cfg = reg.resolve("local-01")
    assert cfg.cloud is None
    assert cfg.monitoring is None
