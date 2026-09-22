import json
from pathlib import Path

from app.sandbox_manager import SandboxManager


class CodeTools:

    def __init__(
        self,
        sandbox: SandboxManager,
    ):
        self.sandbox = sandbox

    def read_file(
        self,
        path: str,
    ) -> dict:

        result = self.sandbox.execute(
            [
                "python",
                "-c",
                (
                    "from pathlib import Path; "
                    f"p=Path({path!r}); "
                    "print(p.read_text())"
                ),
            ]
        )

        return result

    def write_file(
        self,
        path: str,
        content: str,
    ) -> dict:

        payload = json.dumps(content)

        code = f"""
from pathlib import Path

path = Path({path!r})

if path.is_absolute():
    raise ValueError("Absolute paths are not allowed")

resolved = (Path("/workspace") / path).resolve()

if not str(resolved).startswith("/workspace/"):
    raise ValueError("Path escapes workspace")

resolved.parent.mkdir(
    parents=True,
    exist_ok=True,
)

resolved.write_text(
    {payload}
)

print(f"Wrote {{resolved}}")
"""

        return self.sandbox.execute(
            [
                "python",
                "-c",
                code,
            ]
        )

    def execute_shell(self, command: str):
        if not isinstance(command, str):
            return {
                "success": False,
                "error": "command must be a string",
            }

        if not command.strip():
            return {
                "success": False,
                "error": "command cannot be empty",
            }

        return self.sandbox.execute_command(command)