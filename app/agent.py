import json
import re

from app.model import LocalModel
from app.prompts import SYSTEM_PROMPT
from app.tools import CodeTools


class CodingAgent:

    def __init__(
        self,
        model: LocalModel,
        tools: CodeTools,
    ):
        self.model = model
        self.tools = tools

    def run(
        self,
        task: str,
        max_steps: int = 8,
    ):

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": task,
            },
        ]

        history = []
        used_tool = False
        finish_requested = False

        for step in range(max_steps):

            response = self.model.generate(
                messages
            )

            history.append({
                "step": step,
                "model": response,
            })

            print(
                f"\n--- Agent step {step} ---"
            )
            print(response)

            if response.strip() == "DONE":
                if not used_tool:
                    messages.append({
                        "role": "assistant",
                        "content": response,
                    })
                    messages.append({
                        "role": "user",
                        "content": (
                            "Do not finish yet. Use an available tool "
                            "before completing the task."
                        ),
                    })
                    continue

                finish_requested = True
                messages.append({
                    "role": "assistant",
                    "content": response,
                })
                messages.append({
                    "role": "user",
                    "content": (
                        "Now provide the final answer to the user based on "
                        "the tool results. Explain what you found and what "
                        "you changed. Do not output DONE."
                    ),
                })
                continue

            tool_calls = self._parse_tools(
                response
            )

            if not tool_calls:

                if finish_requested:
                    history.append({
                        "step": step,
                        "final": response,
                    })
                    return {
                        "status": "completed",
                        "history": history,
                    }

                messages.append({
                    "role": "assistant",
                    "content": response,
                })

                messages.append({
                    "role": "user",
                    "content": (
                        "You must use one of the "
                        "available tools or output DONE."
                    ),
                })

                continue

            results = []
            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                args = tool_call["arguments"]

                result = self._execute_tool(
                    tool_name,
                    args,
                )
                used_tool = True
                results.append({
                    "tool": tool_name,
                    "result": result,
                })

            messages.append({
                "role": "assistant",
                "content": response,
            })

            messages.append({
                "role": "user",
                "content": (
                    "TOOL RESULT:\n"
                    + json.dumps(results)
                ),
            })

        return {
            "status": "max_steps_reached",
            "history": history,
        }

    def _parse_tools(
        self,
        response: str,
    ) -> list[dict]:

        calls = []
        marker = re.compile(
            r"TOOL:\s*(\w+)\s*ARGS:\s*"
        )

        for match in marker.finditer(response):
            try:
                arguments, _ = json.JSONDecoder().raw_decode(
                    response[match.end():].lstrip()
                )
            except json.JSONDecodeError:
                continue

            if isinstance(arguments, dict):
                calls.append({
                    "name": match.group(1),
                    "arguments": arguments,
                })

        return calls

    def _execute_tool(
        self,
        name: str,
        args: dict,
    ):

        if name == "read_file":

            path = args.get("path")
            if not isinstance(path, str):
                return {
                    "success": False,
                    "error": "read_file requires a string path",
                }

            return self.tools.read_file(path)

        if name == "write_file":

            path = args.get("path")
            content = args.get("content")
            if not isinstance(path, str) or not isinstance(content, str):
                return {
                    "success": False,
                    "error": (
                        "write_file requires string path and content"
                    ),
                }

            return self.tools.write_file(path, content)

        if name == "execute_shell":

            command = args.get("command")
            if not isinstance(command, str):
                return {
                    "success": False,
                    "error": "execute_shell requires a string command",
                }

            return self.tools.execute_shell(command)

        return {
            "success": False,
            "error": (
                f"Unknown tool: {name}"
            ),
        }