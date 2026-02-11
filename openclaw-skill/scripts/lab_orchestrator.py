#!/usr/bin/env python3
"""Docker container orchestration for CTF labs.

All public functions are accessible via CLI and return JSON to stdout.
"""

import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import (
    AVAILABLE_LABS,
    AUTO_CLEANUP_HOURS,
    CONTAINER_CPUS,
    CONTAINER_MEMORY,
    CONTAINER_PID_LIMIT,
    DATA_DIR,
    DOCKER_NETWORK,
    DOCKER_SECURITY_OPTS,
    DOCKER_SUBNET,
    LAB_TMPFS,
    LOGS_DIR,
    MAX_LABS_PER_USER,
    MAX_TOTAL_LABS,
    SCHOOL_NETWORK_BLOCK,
)

# ── Logging ─────────────────────────────────────────────────────

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
_ah = logging.FileHandler(LOGS_DIR / "audit.log")
_ah.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
audit_logger.addHandler(_ah)

error_logger = logging.getLogger("errors")
error_logger.setLevel(logging.ERROR)
_eh = logging.FileHandler(LOGS_DIR / "errors.log")
_eh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
error_logger.addHandler(_eh)

# ── Active Labs Persistence ─────────────────────────────────────

ACTIVE_LABS_FILE = DATA_DIR / "active_labs.json"


def _load_active_labs() -> Dict[str, Dict]:
    if ACTIVE_LABS_FILE.exists():
        try:
            return json.loads(ACTIVE_LABS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_active_labs(data: Dict[str, Dict]) -> None:
    ACTIVE_LABS_FILE.write_text(json.dumps(data, indent=2))


# ── Docker Helpers ──────────────────────────────────────────────


def _run(cmd: List[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Execute a command, capturing output."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _ensure_network() -> bool:
    """Create the isolated Docker network if it doesn't exist."""
    check = _run(["docker", "network", "inspect", DOCKER_NETWORK])
    if check.returncode == 0:
        return True

    result = _run([
        "docker", "network", "create",
        "--driver", "bridge",
        "--subnet", DOCKER_SUBNET,
        DOCKER_NETWORK,
    ])
    if result.returncode != 0:
        error_logger.error(f"Failed to create network: {result.stderr}")
        return False

    # Block traffic to school network
    _run([
        "sudo", "iptables", "-I", "DOCKER-USER",
        "-s", DOCKER_SUBNET, "-d", SCHOOL_NETWORK_BLOCK,
        "-j", "DROP",
    ])
    audit_logger.info(f"Created Docker network {DOCKER_NETWORK} ({DOCKER_SUBNET})")
    return True


def _container_ip(name: str) -> Optional[str]:
    """Retrieve a container's IP on the CTF network."""
    result = _run([
        "docker", "inspect",
        "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
        name,
    ], timeout=10)
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    return None


def _container_running(name: str) -> bool:
    """Check if a container is actively running."""
    result = _run([
        "docker", "inspect", "-f", "{{.State.Running}}", name,
    ], timeout=10)
    return result.returncode == 0 and result.stdout.strip() == "true"


# ── Public Commands ─────────────────────────────────────────────


def start_lab(username: str, lab_type: str) -> Dict[str, Any]:
    """Start a new CTF lab container."""

    if lab_type not in AVAILABLE_LABS:
        avail = ", ".join(AVAILABLE_LABS.keys())
        return {"success": False, "error": f"Unknown lab type: {lab_type}", "available": avail}

    labs = _load_active_labs()

    # Enforce per-user limit
    user_labs = [l for l in labs.values() if l["owner"] == username and l["status"] == "running"]
    if len(user_labs) >= MAX_LABS_PER_USER:
        running = [l["lab_type"] for l in user_labs]
        return {
            "success": False,
            "error": f"You already have {MAX_LABS_PER_USER} labs running.",
            "running_labs": running,
        }

    # Enforce system-wide limit
    total_running = sum(1 for l in labs.values() if l["status"] == "running")
    if total_running >= MAX_TOTAL_LABS:
        return {"success": False, "error": "Server lab capacity reached. Try again later."}

    # Ensure network
    if not _ensure_network():
        return {"success": False, "error": "Failed to create Docker network. Contact admin."}

    lab_cfg = AVAILABLE_LABS[lab_type]
    timestamp = datetime.now().strftime("%s")[-4:]
    container_name = f"{lab_type}-{username}-{timestamp}"

    # Build docker run command
    cmd = [
        "docker", "run", "-d",
        "--name", container_name,
        "--network", DOCKER_NETWORK,
        f"--memory={CONTAINER_MEMORY}",
        f"--cpus={CONTAINER_CPUS}",
        f"--pids-limit={CONTAINER_PID_LIMIT}",
        f"--label=ctf-owner={username}",
        f"--label=ctf-lab-type={lab_type}",
        f"--label=ctf-managed=true",
    ]
    cmd.extend(DOCKER_SECURITY_OPTS)
    # Add lab-specific tmpfs mounts for writable directories
    cmd.extend(LAB_TMPFS.get(lab_type, ["--tmpfs", "/tmp:rw,noexec,nosuid"]))
    cmd.append(lab_cfg["image"])

    result = _run(cmd, timeout=30)

    if result.returncode != 0:
        error_logger.error(f"Docker start failed for {container_name}: {result.stderr}")
        return {"success": False, "error": f"Failed to start {lab_type}. Check Docker logs."}

    # Get IP
    ip = _container_ip(container_name)
    if not ip:
        # Cleanup on failure
        _run(["docker", "rm", "-f", container_name])
        return {"success": False, "error": "Container started but no IP assigned."}

    port = lab_cfg["port"]

    # Persist
    labs[container_name] = {
        "owner": username,
        "lab_type": lab_type,
        "container_name": container_name,
        "ip_address": ip,
        "port": port,
        "started_at": datetime.now().isoformat(),
        "status": "running",
    }
    _save_active_labs(labs)

    audit_logger.info(f"LAB_STARTED - User: {username} - Lab: {container_name} - IP: {ip}:{port}")

    return {
        "success": True,
        "lab_name": container_name,
        "ip_address": ip,
        "port": port,
        "url": f"http://{ip}:{port}",
        "auto_cleanup_hours": AUTO_CLEANUP_HOURS,
    }


def stop_lab(username: str, lab_type: str) -> Dict[str, Any]:
    """Stop and remove a user's lab of the given type."""

    labs = _load_active_labs()

    # Find matching lab
    target = None
    for name, info in labs.items():
        if info["owner"] == username and info["lab_type"] == lab_type and info["status"] == "running":
            target = name
            break

    if not target:
        return {"success": False, "error": f"You don't have a running {lab_type} lab."}

    # Stop & remove
    _run(["docker", "stop", target], timeout=30)
    _run(["docker", "rm", "-f", target], timeout=15)

    labs[target]["status"] = "stopped"
    del labs[target]
    _save_active_labs(labs)

    audit_logger.info(f"LAB_STOPPED - User: {username} - Lab: {target}")
    return {"success": True, "message": f"Stopped {target}"}


def status_labs(username: str) -> Dict[str, Any]:
    """Return user's active labs with live status checks."""

    labs = _load_active_labs()
    user_labs = []

    for name, info in labs.items():
        if info["owner"] != username:
            continue

        # Verify container is actually running
        running = _container_running(name)
        if not running and info["status"] == "running":
            info["status"] = "stopped"

        if info["status"] != "running":
            continue

        started = datetime.fromisoformat(info["started_at"])
        uptime_h = (datetime.now() - started).total_seconds() / 3600
        remaining_h = max(0, AUTO_CLEANUP_HOURS - uptime_h)

        user_labs.append({
            "name": name,
            "type": info["lab_type"],
            "ip": info["ip_address"],
            "port": info["port"],
            "uptime_hours": round(uptime_h, 1),
            "remaining_hours": round(remaining_h, 1),
        })

    _save_active_labs(labs)
    return {"success": True, "active_labs": user_labs}


def list_labs() -> Dict[str, Any]:
    """List all available lab types."""
    labs_list = []
    for key, cfg in AVAILABLE_LABS.items():
        labs_list.append({
            "id": key,
            "name": cfg["name"],
            "category": cfg["category"],
            "difficulty": cfg["difficulty"],
            "port": cfg["port"],
            "description": cfg["description"],
        })
    return {"success": True, "labs": labs_list}


def force_cleanup(username: str) -> Dict[str, Any]:
    """Immediately stop and remove all of a user's labs (officer command)."""

    labs = _load_active_labs()
    removed = []

    for name in list(labs.keys()):
        if labs[name]["owner"] == username:
            _run(["docker", "stop", name], timeout=15)
            _run(["docker", "rm", "-f", name], timeout=15)
            removed.append(name)
            del labs[name]

    _save_active_labs(labs)
    audit_logger.info(f"FORCE_CLEANUP - Target: {username} - Removed: {removed}")
    return {"success": True, "removed": removed, "count": len(removed)}


def auto_cleanup() -> Dict[str, Any]:
    """Remove labs that have exceeded AUTO_CLEANUP_HOURS."""

    labs = _load_active_labs()
    cleaned = []

    for name in list(labs.keys()):
        info = labs[name]
        if info["status"] != "running":
            continue

        started = datetime.fromisoformat(info["started_at"])
        uptime_h = (datetime.now() - started).total_seconds() / 3600

        if uptime_h > AUTO_CLEANUP_HOURS:
            _run(["docker", "stop", name], timeout=15)
            _run(["docker", "rm", "-f", name], timeout=15)
            cleaned.append({"name": name, "owner": info["owner"], "uptime_hours": round(uptime_h, 1)})
            del labs[name]
            audit_logger.info(
                f"AUTO_CLEANUP - Lab: {name} - Owner: {info['owner']} - Uptime: {uptime_h:.1f}h"
            )

    # Also remove any entries for containers no longer running
    for name in list(labs.keys()):
        if not _container_running(name):
            del labs[name]

    _save_active_labs(labs)
    return {"success": True, "cleaned": cleaned, "count": len(cleaned)}


def server_stats() -> Dict[str, Any]:
    """Return server resource usage summary (officer command)."""

    labs = _load_active_labs()
    running = sum(1 for l in labs.values() if l["status"] == "running")

    # Docker system info
    disk = _run(["docker", "system", "df", "--format", "{{.Size}}"], timeout=10)
    disk_usage = disk.stdout.strip() if disk.returncode == 0 else "unknown"

    # Basic system stats
    mem = _run(["free", "-h", "--si"], timeout=5)
    cpu = _run(["nproc"], timeout=5)

    # GPU (optional)
    gpu = _run(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits"], timeout=5)
    gpu_info = gpu.stdout.strip() if gpu.returncode == 0 else "N/A"

    return {
        "success": True,
        "active_containers": running,
        "max_containers": MAX_TOTAL_LABS,
        "docker_disk": disk_usage,
        "cpu_cores": cpu.stdout.strip() if cpu.returncode == 0 else "unknown",
        "memory": mem.stdout.strip() if mem.returncode == 0 else "unknown",
        "gpu": gpu_info,
    }


# ── CLI Dispatch ────────────────────────────────────────────────


def _output(data: Dict[str, Any]) -> None:
    print(json.dumps(data))


def main() -> None:
    if len(sys.argv) < 2:
        _output({"success": False, "error": "Usage: lab_orchestrator.py <action> [args...]"})
        sys.exit(1)

    action = sys.argv[1]

    try:
        if action == "start":
            if len(sys.argv) < 4:
                _output({"success": False, "error": "Usage: start <username> <lab_type>"})
                sys.exit(1)
            _output(start_lab(sys.argv[2], sys.argv[3]))

        elif action == "stop":
            if len(sys.argv) < 4:
                _output({"success": False, "error": "Usage: stop <username> <lab_type>"})
                sys.exit(1)
            _output(stop_lab(sys.argv[2], sys.argv[3]))

        elif action == "status":
            if len(sys.argv) < 3:
                _output({"success": False, "error": "Usage: status <username>"})
                sys.exit(1)
            _output(status_labs(sys.argv[2]))

        elif action == "list":
            _output(list_labs())

        elif action == "force_cleanup":
            if len(sys.argv) < 3:
                _output({"success": False, "error": "Usage: force_cleanup <username>"})
                sys.exit(1)
            _output(force_cleanup(sys.argv[2]))

        elif action == "auto_cleanup":
            _output(auto_cleanup())

        elif action == "server_stats":
            _output(server_stats())

        else:
            _output({"success": False, "error": f"Unknown action: {action}"})
            sys.exit(1)

    except subprocess.TimeoutExpired:
        error_logger.error(f"lab_orchestrator.py {action} timed out")
        _output({"success": False, "error": "Operation timed out (30s). Try again."})
        sys.exit(1)
    except Exception as exc:
        error_logger.error(f"lab_orchestrator.py {action} failed: {exc}", exc_info=True)
        _output({"success": False, "error": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
