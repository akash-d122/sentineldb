with open("src/sentineldb/api/routes_tenant.py", "r") as f:
    code = f.read()

code = code.replace("from typing import Any", "from typing import Any, Literal")
code = code.replace("plan_tier: str = \"free\"", "plan_tier: Literal[\"free\", \"pro\", \"enterprise\"] = \"free\"")

with open("src/sentineldb/api/routes_tenant.py", "w") as f:
    f.write(code)
