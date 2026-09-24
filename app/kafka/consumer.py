import json

from kafka import KafkaConsumer


class KafkaTaskConsumer:

    def __init__(
        self,
        bootstrap_servers: list[str],
        group_id: str,
        topic: str,
    ):
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            key_deserializer=lambda key: (
                key.decode("utf-8")
                if key
                else None
            ),
            value_deserializer=lambda value: json.loads(
                value.decode("utf-8")
            ),
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )

    def consume(self):
        return self.consumer

    def commit(self):
        self.consumer.commit()

    def close(self):
        self.consumer.close()