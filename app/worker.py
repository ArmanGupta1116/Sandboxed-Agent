import time

from app.agent import CodingAgent
from app.kafka.consumer import KafkaTaskConsumer
from app.kafka.topics import TASKS_TOPIC
from app.model import LocalModel
from app.sandbox_manager import SandboxManager
from app.tools import CodeTools


KAFKA_SERVERS = [
    "localhost:9092",
    "localhost:9094",
    "localhost:9096",
]

GROUP_ID = "agent-workers"


def create_agent():

    model = LocalModel()

    sandbox = SandboxManager()

    tools = CodeTools(
        sandbox=sandbox
    )

    return CodingAgent(
        model=model,
        tools=tools,
    )


def main():

    print("Starting agent worker...")

    agent = create_agent()

    consumer = KafkaTaskConsumer(
        bootstrap_servers=KAFKA_SERVERS,
        group_id=GROUP_ID,
        topic=TASKS_TOPIC,
    )

    print("Worker listening for tasks...")

    try:

        for message in consumer.consume():

            task_data = message.value

            task_id = task_data["task_id"]
            task = task_data["task"]

            print(
                f"Received task {task_id}"
            )

            try:

                result = agent.run(
                    task_id=task_id,
                    task=task,
                )

                print(
                    f"Task {task_id} completed"
                )

                print(result)

                consumer.commit()

            except Exception as exc:

                print(
                    f"Task {task_id} failed: {exc}"
                )

                # Don't commit yet.
                #
                # Retry / DLQ handling will be added next.

    except KeyboardInterrupt:

        print("Worker shutting down...")

    finally:

        consumer.close()


if __name__ == "__main__":
    main()