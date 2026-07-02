import os
import glob

# Models
with open("src/sentineldb/notifications/models.py", "r") as f:
    code = f.read()
code = code.replace("def notify(self", "async def notify(self")
with open("src/sentineldb/notifications/models.py", "w") as f:
    f.write(code)

# Dispatcher
with open("src/sentineldb/notifications/dispatcher.py", "r") as f:
    code = f.read()
code = code.replace("def dispatch(", "async def dispatch(")
code = code.replace(
"""        for handler in self.handlers:
            try:
                handler.notify(report)
            except Exception as e:
                logger.error("Notification handler %s failed: %s", handler.__class__.__name__, e)""",
"""        import asyncio
        async def _safe_notify(h):
            try:
                await h.notify(report)
            except Exception as e:
                logger.error("Notification handler %s failed: %s", h.__class__.__name__, e)
        await asyncio.gather(*(_safe_notify(h) for h in self.handlers))"""
)
with open("src/sentineldb/notifications/dispatcher.py", "w") as f:
    f.write(code)

# Slack, Jira, Freshdesk
for handler_file in ["slack.py", "jira.py", "freshdesk.py"]:
    filepath = f"src/sentineldb/notifications/{handler_file}"
    if not os.path.exists(filepath): continue
    with open(filepath, "r") as f:
        code = f.read()
    code = code.replace("def notify(", "async def notify(")
    code = code.replace("response = httpx.post(", "async with httpx.AsyncClient() as client:\n                response = await client.post(")
    with open(filepath, "w") as f:
        f.write(code)
