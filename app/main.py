from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, status

from app.kafka.producer import KafkaProducerClient
from app.kafka.schemas import TaskMessage
from app.schemas import AgentRequest


KAFKA_SERVERS = [
    "localhost:9092",
    "localhost:9094",
    "localhost:9096",
]

producer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global producer

    producer = KafkaProducerClient(
        bootstrap_servers=KAFKA_SERVERS
    )

    print("Kafka producer ready.")

    yield

    producer.close()
    print("Kafka producer stopped.")


app = FastAPI(
    title="Sandboxed Coding Agent",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "kafka": producer is not None,
    }


@app.post(
    "/tasks",
    status_code=status.HTTP_202_ACCEPTED,
)
def create_task(request: AgentRequest):

    task_id = f"task_{uuid4().hex}"

    task = TaskMessage(
        task_id=task_id,
        task=request.task,
    )

    metadata = producer.publish_task(task)

    return {
        "task_id": task_id,
        "status": "queued",
        "kafka": metadata,
    }