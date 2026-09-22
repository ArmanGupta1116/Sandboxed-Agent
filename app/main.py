from fastapi import FastAPI

from app.agent import CodingAgent
from app.model import LocalModel
from app.sandbox_manager import SandboxManager
from app.tools import CodeTools
from app.schemas import AgentRequest


app = FastAPI(
    title="Agent Sandbox Demo"
)


model = LocalModel()

sandbox = SandboxManager()

tools = CodeTools(
    sandbox
)

agent = CodingAgent(
    model=model,
    tools=tools,
)


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.post("/agent")
def run_agent(
    request: AgentRequest,
):

    return agent.run(
        request.task
    )