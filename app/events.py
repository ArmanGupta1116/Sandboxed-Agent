from abc import ABC, abstractmethod


class EventPublisher(ABC):

    @abstractmethod
    def publish(
        self,
        task_id: str,
        event_type: str,
        payload: dict,
    ):
        pass