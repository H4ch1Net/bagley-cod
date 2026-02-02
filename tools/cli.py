import os
import sys

from skills.ai_integration import AIOrchestrator
from skills.lab_orchestrator import LabManager


class LabCLI:
    def __init__(self) -> None:
        self.manager = LabManager()
        self.ai = AIOrchestrator()
        self.username = os.getenv("USER") or os.getenv("USERNAME") or "user"
        self.ai_enabled = bool(self.ai.api_key)

    def print_banner(self) -> None:
        print("🧪 Bagley Lab Orchestrator")
        print("──────────────────────────")
        print(f"User: {self.username}")
        print(f"AI Mode: {'✅ Enabled' if self.ai_enabled else '❌ Disabled'}")
        print()

    def print_help(self) -> None:
        print("Available commands:")
        print("  start <lab_type>")
        print("  stop <lab_name|lab_type>")
        print("  delete <lab_name|lab_type>")
        print("  status")
        print("  list")
        print("  help")
        print("  quit / exit")
        print()
        print("Examples:")
        print("  start dvwa")
        print("  stop dvwa")
        print("  delete dvwa")
        print("  status")
        print("  list")
        print()
        print("AI Mode lets you use natural language if enabled.")

    def _execute_action(self, action: str, lab_type: str | None) -> None:
        action = action.lower().strip()
        if action == "start":
            if not lab_type:
                print("❌ Please specify a lab type")
                return
            print(self.manager.create_lab(self.username, lab_type))
        elif action == "stop":
            if not lab_type:
                print("❌ Please specify a lab name or type")
                return
            print(self.manager.stop_lab(self.username, lab_type))
        elif action == "delete":
            if not lab_type:
                print("❌ Please specify a lab name or type")
                return
            print(self.manager.delete_lab(self.username, lab_type))
        elif action == "status":
            print(self.manager.get_status(self.username))
        elif action == "list":
            print(self.manager.list_available())
        elif action == "help":
            self.print_help()
        else:
            print("❌ Unknown action")

    def handle_command(self, user_input: str) -> bool:
        cleaned = user_input.strip()
        if not cleaned:
            return True

        parts = cleaned.split()
        command = parts[0].lower()
        arg = parts[1].lower() if len(parts) > 1 else None

        if command in {"quit", "exit"}:
            print("👋 Goodbye!")
            return False

        if command == "help":
            self.print_help()
            return True

        if command == "list":
            print(self.manager.list_available())
            return True

        if command == "status":
            print(self.manager.get_status(self.username))
            return True

        if command in {"start", "stop", "delete"}:
            self._execute_action(command, arg)
            return True

        if self.ai_enabled:
            result = self.ai.parse_command(cleaned, self.username)
            if not result.get("success"):
                print(f"❌ {result.get('error')}")
                return True

            command = result["command"]
            action = command.get("action")
            lab_type = command.get("lab_type")
            self._execute_action(action, lab_type)
            return True

        print("❌ Unknown command. Type 'help' for options.")
        return True

    def run(self) -> None:
        self.print_banner()
        self.print_help()
        while True:
            try:
                user_input = input(f"{self.username}@orchestrator> ")
                if not self.handle_command(user_input):
                    break
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as exc:  # pylint: disable=broad-except
                print(f"❌ Error: {exc}")


def main() -> None:
    cli = LabCLI()
    cli.run()


if __name__ == "__main__":
    sys.exit(main())
