import json
from uuid import uuid4

from kafka import KafkaProducer

from app.kafka.schemas import AgentEvent, TaskMessage
from app.kafka.topics import EVENTS_TOPIC, TASKS_TOPIC


class KafkaProducerClient:

    def __init__(
        self,
        bootstrap_servers: list[str],
    ):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            key_serializer=lambda key: key.encode("utf-8"),
            value_serializer=lambda value: json.dumps(
                value
            ).encode("utf-8"),
            acks="all",
        )

    def publish_task(
        self,
        task: TaskMessage,
    ):
        future = self.producer.send(
            TASKS_TOPIC,
            key=task.task_id,
            value=task.model_dump(mode="json"),
        )

        metadata = future.get(timeout=10)

        return {
            "topic": metadata.topic,
            "partition": metadata.partition,
            "offset": metadata.offset,
        }

    def publish_event(
        self,
        event: AgentEvent,
    ):
        future = self.producer.send(
            EVENTS_TOPIC,
            key=event.task_id,
            value=event.model_dump(mode="json"),
        )

        metadata = future.get(timeout=10)

        return {
            "topic": metadata.topic,
            "partition": metadata.partition,
            "offset": metadata.offset,
        }

    def flush(self):
        self.producer.flush()

    def close(self):
        self.producer.close()

class KafkaEventPublisher:

    def __init__(
        self,
        producer: KafkaProducerClient,
    ):
        self.producer = producer

    def publish(
        self,
        task_id: str,
        event_type: str,
        payload: dict,
    ):
        event = AgentEvent(
            event_id=f"evt_{uuid4().hex}",
            task_id=task_id,
            event_type=event_type,
            payload=payload,
        )

        return self.producer.publish_event(event)