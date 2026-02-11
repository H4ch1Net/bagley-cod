"""Docker container orchestration for CTF labs"""

import subprocess
import logging
from datetime import datetime
from typing import Optional, Dict, List
from config.settings import AVAILABLE_LABS, DOCKER_NETWORK, MAX_LABS_PER_USER, AUTO_CLEANUP_HOURS
from config.security import DOCKER_SECURITY_OPTS, RESOURCE_LIMITS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LabEnvironment:
    """Represents a single CTF lab instance"""

    def __init__(self, owner: str, lab_type: str):
        if lab_type not in AVAILABLE_LABS:
            raise ValueError(f"Unknown lab type: {lab_type}")

        self.owner = owner
        self.lab_type = lab_type
        self.lab_config = AVAILABLE_LABS[lab_type]
        self.image = self.lab_config["image"]

        # Generate unique name
        self.name = f"{lab_type}-{owner}-{datetime.now().strftime('%s')[-4:]}"

        self.ip_address = None
        self.status = "created"
        self.started_at = None

    def start(self) -> bool:
        """Start the Docker container"""
        try:
            # Build docker run command
            cmd = [
                "docker", "run", "-d",
                "--name", self.name,
                "--network", DOCKER_NETWORK,
                f"--memory={RESOURCE_LIMITS['memory']}",
                f"--cpus={RESOURCE_LIMITS['cpus']}",
                f"--pids-limit={RESOURCE_LIMITS['pids_limit']}",
                f"--label=owner={self.owner}",
                f"--label=lab-type={self.lab_type}",
            ]

            # Add security options
            cmd.extend(DOCKER_SECURITY_OPTS)

            # Add image
            cmd.append(self.image)

            # Run container
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )

            # Get container IP
            ip_result = subprocess.run([
                "docker", "inspect",
                "-f", "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                self.name
            ], capture_output=True, text=True, check=True, timeout=10)

            self.ip_address = ip_result.stdout.strip()
            self.status = "running"
            self.started_at = datetime.now()

            logger.info(f"Started lab: {self.name} at {self.ip_address}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start {self.name}: {e.stderr}")
            self.status = "failed"
            return False
        except Exception as e:
            logger.error(f"Error starting {self.name}: {e}")
            self.status = "failed"
            return False

    def stop(self) -> bool:
        """Stop the container"""
        try:
            subprocess.run(
                ["docker", "stop", self.name],
                capture_output=True,
                check=True,
                timeout=30
            )
            self.status = "stopped"
            logger.info(f"Stopped lab: {self.name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop {self.name}: {e.stderr}")
            return False

    def delete(self) -> bool:
        """Remove the container"""
        try:
            subprocess.run(
                ["docker", "rm", "-f", self.name],
                capture_output=True,
                check=True,
                timeout=30
            )
            self.status = "deleted"
            logger.info(f"Deleted lab: {self.name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete {self.name}: {e.stderr}")
            return False

    def get_uptime_hours(self) -> float:
        """Get lab uptime in hours"""
        if not self.started_at:
            return 0
        delta = datetime.now() - self.started_at
        return delta.total_seconds() / 3600


class LabManager:
    """Manages multiple lab instances"""

    def __init__(self):
        self.active_labs: Dict[str, LabEnvironment] = {}

    def create_lab(self, owner: str, lab_type: str) -> str:
        """Create and start a new lab"""

        # Validate lab type
        if lab_type not in AVAILABLE_LABS:
            available = ", ".join(AVAILABLE_LABS.keys())
            return f"❌ Unknown lab type. Available: {available}"

        # Check user's active labs
        user_labs = [
            lab for lab in self.active_labs.values()
            if lab.owner == owner and lab.status == "running"
        ]

        # Enforce per-user limit
        if len(user_labs) >= MAX_LABS_PER_USER:
            return (
                f"❌ You already have {MAX_LABS_PER_USER} labs running.\n"
                f"Stop one first: `!stop {user_labs[0].lab_type}`"
            )

        # Auto-cleanup old labs
        for lab in user_labs:
            if lab.get_uptime_hours() > AUTO_CLEANUP_HOURS:
                logger.info(f"Auto-cleaning up {lab.name} (exceeded {AUTO_CLEANUP_HOURS}h)")
                lab.stop()
                lab.delete()
                del self.active_labs[lab.name]
                return (
                    f"✅ Cleaned up your old {lab.lab_type} lab (ran for {AUTO_CLEANUP_HOURS}+ hours).\n"
                    f"Starting new {lab_type} lab now..."
                )

        # Create new lab
        try:
            lab = LabEnvironment(owner, lab_type)

            if lab.start():
                self.active_labs[lab.name] = lab
                port = AVAILABLE_LABS[lab_type].get("port", 80)
                return (
                    f"✅ **{lab.name}** started successfully!\n"
                    f"📍 IP: `{lab.ip_address}`\n"
                    f"🔗 Access: `http://{lab.ip_address}:{port}`\n"
                    f"⏰ Auto-cleanup in {AUTO_CLEANUP_HOURS} hours"
                )
            else:
                return f"❌ Failed to start {lab_type} lab. Check logs."

        except ValueError as e:
            return f"❌ {e}"
        except Exception as e:
            logger.error(f"Error creating lab: {e}")
            return f"❌ Error creating lab. Contact admin."

    def stop_lab(self, owner: str, lab_type: str) -> str:
        """Stop a running lab"""

        # Find user's lab of this type
        user_lab = None
        for lab in self.active_labs.values():
            if lab.owner == owner and lab.lab_type == lab_type and lab.status == "running":
                user_lab = lab
                break

        if not user_lab:
            return f"❌ You don't have a running {lab_type} lab."

        if user_lab.stop():
            return f"🛑 Stopped **{user_lab.name}**"
        else:
            return f"❌ Failed to stop lab. Try again or contact admin."

    def delete_lab(self, owner: str, lab_type: str) -> str:
        """Delete a lab (stop + remove)"""

        # Find user's lab
        user_lab = None
        for lab in self.active_labs.values():
            if lab.owner == owner and lab.lab_type == lab_type:
                user_lab = lab
                break

        if not user_lab:
            return f"❌ You don't have a {lab_type} lab."

        # Stop if running
        if user_lab.status == "running":
            user_lab.stop()

        # Delete
        if user_lab.delete():
            del self.active_labs[user_lab.name]
            return f"🗑️ Deleted **{user_lab.name}**"
        else:
            return f"❌ Failed to delete lab. Try again or contact admin."

    def get_status(self, owner: str) -> str:
        """Get status of user's labs"""

        user_labs = [
            lab for lab in self.active_labs.values()
            if lab.owner == owner
        ]

        if not user_labs:
            return "📋 You have no active labs."

        msg = "📋 **Your Active Labs:**\n"
        for lab in user_labs:
            uptime_hours = lab.get_uptime_hours()
            uptime_str = f"{int(uptime_hours)}h {int((uptime_hours % 1) * 60)}m"

            status_emoji = "🟢" if lab.status == "running" else "🔴"
            port = AVAILABLE_LABS[lab.lab_type].get("port", 80)

            msg += (
                f"{status_emoji} **{lab.lab_type}** | "
                f"`{lab.ip_address}:{port}` | "
                f"Uptime: {uptime_str}\n"
            )

        return msg

    def list_available(self) -> str:
        """List available lab types"""

        msg = "🔬 **Available Lab Types:**\n\n"

        for lab_type, config in AVAILABLE_LABS.items():
            msg += (
                f"**{lab_type.upper()}** - {config['name']}\n"
                f"  • Category: {config['category']}\n"
                f"  • Difficulty: {config['difficulty']}\n"
                f"  • {config['description']}\n\n"
            )

        msg += f"Start a lab: `!start <lab_type>`"
        return msg

    def cleanup_old_labs(self):
        """Clean up labs exceeding max uptime (for cron job)"""
        for lab in list(self.active_labs.values()):
            if lab.get_uptime_hours() > AUTO_CLEANUP_HOURS:
                logger.info(f"Auto-cleanup: {lab.name} exceeded {AUTO_CLEANUP_HOURS}h")
                lab.stop()
                lab.delete()
                del self.active_labs[lab.name]
