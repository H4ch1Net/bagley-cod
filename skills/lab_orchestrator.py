import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class LabEnvironment:
    name: str
    lab_type: str
    owner: str
    status: str = "stopped"
    ip: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None

    def start(self) -> str:
        if self.status == "running":
            return f"🟢 {self.name} is already running"
        self.status = "running"
        self.started_at = time.time()
        self.ip = f"192.168.100.{hash(self.name) % 200 + 50}"
        return (
            f"✅ {self.name} started successfully\n"
            f"📍 IP: {self.ip}\n"
            f"🔗 Access: http://{self.ip}"
        )

    def stop(self) -> str:
        if self.status != "running":
            return f"🔴 {self.name} is already stopped"
        self.status = "stopped"
        return f"🛑 {self.name} stopped"

    def get_info(self) -> str:
        uptime = "N/A"
        if self.status == "running" and self.started_at:
            uptime_seconds = int(time.time() - self.started_at)
            uptime = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
        ip_display = self.ip or "N/A"
        status_icon = "🟢" if self.status == "running" else "🔴"
        return f"{status_icon} {self.name} | {ip_display} | Uptime: {uptime}"


class LabManager:
    def __init__(self) -> None:
        self.available_labs: Dict[str, str] = {
            "dvwa": "Damn Vulnerable Web App (beginner)",
            "webgoat": "WebGoat (beginner)",
            "metasploitable": "Metasploitable 2 (intermediate)",
            "juice-shop": "OWASP Juice Shop (beginner)",
        }
        self.active_labs: Dict[str, LabEnvironment] = {}

    def list_available(self) -> str:
        lines = ["🔬 Available Lab Types:"]
        for lab_type, desc in self.available_labs.items():
            lines.append(f"• {lab_type.upper()} - {desc}")
        return "\n".join(lines)

    def _find_user_lab(self, owner: str, lab_type: str) -> Optional[LabEnvironment]:
        for lab in self.active_labs.values():
            if lab.owner == owner and lab.lab_type == lab_type:
                return lab
        return None

    def create_lab(self, owner: str, lab_type: str) -> str:
        lab_type = lab_type.lower().strip()
        if lab_type not in self.available_labs:
            return f"❌ Unknown lab type: {lab_type}"

        existing = self._find_user_lab(owner, lab_type)
        if existing:
            return f"⚠️ You already have a {lab_type} instance running"

        index = 1
        name_base = f"{lab_type}-{owner}"
        name = f"{name_base}-{index}"
        while name in self.active_labs:
            index += 1
            name = f"{name_base}-{index}"

        lab = LabEnvironment(name=name, lab_type=lab_type, owner=owner)
        self.active_labs[name] = lab
        return lab.start()

    def stop_lab(self, owner: str, lab_identifier: str) -> str:
        lab_identifier = lab_identifier.lower().strip()
        lab = self.active_labs.get(lab_identifier)
        if not lab:
            lab = self._find_user_lab(owner, lab_identifier)

        if not lab or lab.owner != owner:
            return "❌ Lab not found"
        return lab.stop()

    def delete_lab(self, owner: str, lab_identifier: str) -> str:
        lab_identifier = lab_identifier.lower().strip()
        lab = self.active_labs.get(lab_identifier)
        if not lab:
            lab = self._find_user_lab(owner, lab_identifier)

        if not lab or lab.owner != owner:
            return "❌ Lab not found"

        lab.stop()
        del self.active_labs[lab.name]
        return f"🧹 {lab.name} deleted"

    def get_status(self, owner: Optional[str] = None) -> str:
        labs = list(self.active_labs.values())
        if owner:
            labs = [lab for lab in labs if lab.owner == owner]

        if not labs:
            return "📋 No active labs found"

        lines = ["📋 Active Labs:"]
        for lab in labs:
            lines.append(lab.get_info())
        return "\n".join(lines)
