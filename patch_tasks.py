with open("src/sentineldb/worker/tasks.py", "r") as f:
    code = f.read()

code = code.replace("_dispatcher.dispatch(report)", "await _dispatcher.dispatch(report)")

with open("src/sentineldb/worker/tasks.py", "w") as f:
    f.write(code)
