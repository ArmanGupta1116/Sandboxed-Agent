import time
import uuid
from pathlib import Path

import docker


class SandboxManager:

    IMAGE = "agent-code-sandbox:latest"

    def __init__(self):
        self.client = docker.from_env()

        self.host_workspace = (
            Path(__file__).resolve().parent.parent
            / "workspace"
        )

    def execute(
        self,
        command: list[str],
        timeout: int = 30,
    ) -> dict:

        container = None

        container_name = (
            f"agent-sandbox-{uuid.uuid4().hex[:12]}"
        )

        start_time = time.monotonic()

        try:

            container = self.client.containers.create(

                image=self.IMAGE,

                name=container_name,

                command=command,

                # Only mount the workspace.
                volumes={
                    str(self.host_workspace): {
                        "bind": "/workspace",
                        "mode": "rw",
                    }
                },

                working_dir="/workspace",

                # -------------------------------
                # Security
                # -------------------------------

                user="10001",

                privileged=False,

                security_opt=[
                    "no-new-privileges:true",
                ],

                # No Internet.
                network_disabled=True,

                # Container filesystem is read-only.
                read_only=True,

                # Only /tmp is writable.
                tmpfs={
                    "/tmp": (
                        "rw,noexec,nosuid,"
                        "size=64m"
                    )
                },

                # -------------------------------
                # Resource limits
                # -------------------------------

                mem_limit="512m",

                nano_cpus=1_000_000_000,

                pids_limit=64,

                # -------------------------------
                # Don't automatically restart
                # -------------------------------

                auto_remove=False,
            )

            container.start()

            # Wait for completion.
            result = container.wait(
                timeout=timeout
            )

            exit_code = result["StatusCode"]

            stdout = container.logs(
                stdout=True,
                stderr=False,
            ).decode(
                "utf-8",
                errors="replace",
            )

            stderr = container.logs(
                stdout=False,
                stderr=True,
            ).decode(
                "utf-8",
                errors="replace",
            )

            elapsed = (
                time.monotonic() - start_time
            )

            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout[:100_000],
                "stderr": stderr[:100_000],
                "duration_seconds": elapsed,
            }

        except Exception as exc:

            if container is not None:

                try:
                    container.kill()
                except Exception:
                    pass

            return {
                "success": False,
                "exit_code": None,
                "stdout": "",
                "stderr": str(exc),
            }

        finally:

            if container is not None:

                try:
                    container.remove(
                        force=True
                    )
                except Exception:
                    pass

    def execute_command(
        self,
        command: str,
        timeout: int = 30,
    ):

        return self.execute(
            [
                "/bin/sh",
                "-c",
                command,
            ],
            timeout=timeout,
        )