with open("src/sentineldb/registry/loader.py", "r") as f:
    code = f.read()

new_code = code.replace(
"""    def __init__(self, path: str | Path = "instances.yaml") -> None:
        self._path = Path(path)
        self._registry: dict[str, InstanceConfig] = self._load()""",
"""    def __init__(self, path: str | Path = "instances.yaml") -> None:
        self._path = Path(path)
        self._registry: dict[str, InstanceConfig] = {}
        self._loaded = False
"""
)

new_code = new_code.replace(
"""    def _load(self) -> dict[str, InstanceConfig]:
        with self._path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)""",
"""    def _load(self) -> dict[str, InstanceConfig]:
        if not self._path.exists():
            return {}
        with self._path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)"""
)

new_code = new_code.replace(
"""    def resolve(self, instance_id: str) -> InstanceConfig:
        try:
            return self._registry[instance_id]""",
"""    def resolve(self, instance_id: str) -> InstanceConfig:
        if not self._loaded:
            self._registry = self._load()
            self._loaded = True
        try:
            return self._registry[instance_id]"""
)

with open("src/sentineldb/registry/loader.py", "w") as f:
    f.write(new_code)
