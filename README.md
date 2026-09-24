# Sandboxed Coding Agent

A lightweight coding agent that uses a locally cached Hugging Face model to read, modify, and execute code inside an isolated Docker container.

## Architecture

```text
User
  │
  ▼
FastAPI
  │
  ▼
Kafka
  │
  ├── agent.tasks
  ├── agent.events
  └── agent.dlq
  │
  ▼
Agent Worker
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
* Kafka-based task processing
* Kafka-based agent lifecycle events
* Consumer groups for horizontal worker scaling
* At-least-once task processing

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
│   ├── events.py
│   ├── worker.py
│   ├── event_worker.py
│   ├── main.py
│   └── kafka/
│       ├── __init__.py
│       ├── schemas.py
│       ├── topics.py
│       ├── producer.py
│       └── consumer.py
├── kafka/
│   ├── docker-compose.yml
│   ├── topics.sh
│   └── README.md
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
* Docker / Colima
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

### 5. Start Kafka

```bash
cd kafka
docker compose up -d
```

### 6. Create Kafka topics

```bash
./topics.sh
```

### 7. Start the API

```bash
uvicorn app.main:app
```

### 8. Start an agent worker

```bash
python -m app.worker
```

## Kafka Architecture

The current local setup uses a three-broker Kafka cluster running in KRaft mode.

```text
                    ┌───────────────────┐
                    │   Kafka Cluster   │
                    │                   │
                    │ kafka-1           │
                    │ kafka-2           │
                    │ kafka-3           │
                    └─────────┬─────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
       agent.tasks      agent.events       agent.dlq
             │
             ▼
       agent-workers
       consumer group
             │
       ┌─────┼─────┐
       ▼     ▼     ▼
    Worker  Worker  Worker
```

### Topics

| Topic          | Purpose                                  |
| -------------- | ---------------------------------------- |
| `agent.tasks`  | Coding tasks submitted to workers        |
| `agent.events` | Agent and task lifecycle events          |
| `agent.dlq`    | Tasks that eventually fail after retries |

Tasks and events use `task_id` as the Kafka message key, providing ordering for messages belonging to the same task within a topic partition.

## Agent Events

The agent emits domain events such as:

```text
task.started
agent.step
tool.started
tool.completed
task.completed
task.failed
```

The coding agent is kept independent of Kafka through an `EventPublisher` abstraction. Kafka is one implementation of that publisher.

This keeps the agent logic independent from the messaging infrastructure and allows the event transport to evolve separately.

## Task Processing

Workers consume tasks using the same Kafka consumer group:

```text
agent.tasks
     │
     ▼
agent-workers
     │
     ├── Worker 1
     ├── Worker 2
     └── Worker N
```

Each partition is assigned to at most one consumer within the group. This allows multiple workers to process different tasks concurrently.

The worker disables automatic offset commits and commits only after successful task processing.

This currently provides **at-least-once processing**. If a worker fails after processing a task but before committing its Kafka offset, the task can be processed again.

Retry and idempotency handling will be added incrementally.

## Example

Send a coding task:

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Fix calculator.py and verify the implementation."
  }'
```

The task is published to Kafka and later consumed by an agent worker.

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

## Changelog

### 2026-09-24

#### Kafka Task Processing

* Added a local three-broker Kafka cluster using KRaft.
* Added separate internal and external Kafka listeners so brokers can communicate through Docker networking while host applications connect through `localhost`.
* Added Kafka topics:

  * `agent.tasks`
  * `agent.events`
  * `agent.dlq`
* Added version-controlled topic creation through `kafka/topics.sh`.
* Added replicated topics with replication factor `3`.
* Configured `min.insync.replicas=2`.
* Configured producers with `acks=all`.
* Added Kafka task producer and consumer abstractions.
* Added `TaskMessage` and `AgentEvent` schemas.
* Added a Kafka consumer group for horizontally scalable agent workers.
* Disabled automatic consumer offset commits and moved commits to after successful task execution.
* Established at-least-once task-processing semantics.

#### Agent Event System

* Added an `EventPublisher` abstraction to decouple the coding agent from Kafka.
* Added task lifecycle events:

  * `task.started`
  * `agent.step`
  * `tool.started`
  * `tool.completed`
  * `task.completed`
  * `task.failed`
* Added `task_id` as the Kafka message key to preserve per-task ordering within a topic partition.
* Added unique event IDs for emitted agent events.

#### Architecture

* Changed task execution from direct synchronous API execution toward an asynchronous API → Kafka → worker architecture.
* Established the foundation for multiple independent agent workers.
* Established `agent.events` as the event stream that can later feed task-status storage, monitoring, and UI components.

#### Known Next Steps

* Retry handling and exponential backoff.
* Dead-letter queue processing.
* Task idempotency and duplicate-execution protection.
* Handling long-running agent tasks with Kafka consumer `max.poll.interval.ms`.
* Task-state persistence.
* Event consumer for building task status.
* Stronger production-grade sandbox isolation.
* Containerizing workers and gradually introducing production infrastructure.
