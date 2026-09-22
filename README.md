# Sandboxed Coding Agent

A lightweight coding agent that uses a locally cached Hugging Face model to read, modify, and execute code inside an isolated Docker container.

## Architecture

```text
User
  │
  ▼
Coding Agent
  │
  ▼
Local Hugging Face Model
  │
  ├── read_file
  ├── write_file
  └── execute_shell
          │
          ▼
    Sandbox Manager
          │
          ▼
    Docker Container
          │
          ├── Non-root user
          ├── Network disabled
          ├── Read-only root filesystem
          ├── CPU / memory limits
          ├── PID limit
          └── /workspace
```

The LLM runs on the host machine. Only agent-generated code is executed inside the sandbox.

## Features

* Local Hugging Face model inference
* File read/write tools
* Shell execution inside Docker
* Non-root container execution
* Network isolation
* CPU, memory, and PID limits
* Read-only container filesystem
* Ephemeral container lifecycle

## Project Structure

```text
sandboxed_agent/
├── app/
│   ├── agent.py
│   ├── model.py
│   ├── prompts.py
│   ├── schemas.py
│   ├── sandbox_manager.py
│   ├── tools.py
│   └── main.py
├── sandbox/
│   ├── Dockerfile
│   └── requirements.txt
├── workspace/
│   └── calculator.py
├── scripts/
│   └── download_model.py
├── requirements.txt
└── README.md
```

## Requirements

* Python 3.12+
* Docker Desktop
* Git

## Setup

### 1. Create Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Build the sandbox image

```bash
docker build -t agent-code-sandbox:latest ./sandbox
```

### 4. Download the model

```bash
python scripts/download_model.py
```

The model is cached locally by Hugging Face, typically under:

```text
~/.cache/huggingface/hub/
```

### 5. Start the API

```bash
uvicorn app.main:app
```

## Example

Send a coding task:

```bash
curl -X POST http://127.0.0.1:8000/agent \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Fix calculator.py and verify the implementation."
  }'
```

The agent follows a loop such as:

```text
Read code
   ↓
Modify code
   ↓
Run tests / script
   ↓
Inspect result
   ↓
Fix if necessary
   ↓
Complete
```

## Sandbox

Generated code runs inside a restricted Docker container with:

```text
User:        sandboxuser (UID 10001)
Network:     Disabled
Root FS:     Read-only
Memory:      512 MB
CPU:         1 core
PIDs:        64
```

The current demo mounts `workspace/` into the container as `/workspace`.

## Security Note

This is an educational project and is **not a production-grade sandbox**. Stronger isolation can be achieved using technologies such as gVisor, Kata Containers, or Firecracker.

For production use, an ephemeral task workspace and stronger isolation boundary should be used instead of directly mounting the host repository.
