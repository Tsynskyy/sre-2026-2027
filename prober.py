import json
import os
import time
import urllib.request
import uuid

from prometheus_client import Counter, start_http_server

TARGET = os.environ.get("PROBE_TARGET", "http://app")
PROBES = Counter("probe_total", "Шаги сценария пробера", ["check", "result"])


def call(method, path, body=None):
    req = urllib.request.Request(TARGET + path, json.dumps(body).encode() if body else None, method=method)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=2) as resp:
        return json.loads(resp.read() or "null")


def scenario():
    title = f"probe-{uuid.uuid4()}"
    check = "create"
    try:
        task = call("POST", "/api/tasks", {"title": title})
        PROBES.labels(check, "success").inc()
        check = "complete"
        call("PUT", f"/api/tasks/{task['id']}", {"title": title, "status": "done"})
        PROBES.labels(check, "success").inc()
        check = "delete"
        call("DELETE", f"/api/tasks/{task['id']}")
        PROBES.labels(check, "success").inc()
    except Exception as exc:
        PROBES.labels(check, "fail").inc()
        print(json.dumps({"level": "warning", "message": "probe failed", "check": check, "error": str(exc)}), flush=True)


if __name__ == "__main__":
    for check in ("create", "complete", "delete"):
        PROBES.labels(check, "fail")
        PROBES.labels(check, "success")
    start_http_server(9100)
    while True:
        scenario()
        time.sleep(10)
