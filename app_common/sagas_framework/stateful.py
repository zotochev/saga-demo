import abc
import logging

from celery import Celery

from .base import BaseSaga, AsyncStep, BaseStep


class AbstractSagaStateRepository(abc.ABC):
    @abc.abstractmethod
    def get_saga_state_by_id(self, saga_id: int) -> object:
        raise NotImplementedError

    @abc.abstractmethod
    def update_status(self, saga_id: int, status: str) -> object:
        raise NotImplementedError

    @abc.abstractmethod
    def update(self, saga_id: int, **fields_to_update: str) -> object:
        raise NotImplementedError


class StatefulSaga(BaseSaga, abc.ABC):
    """
    Note this class assumes sqlalchemy-mixins library is used.
    Use it rather as an example
    """
    saga_state_repository: AbstractSagaStateRepository = None
    _saga_state = None  # cached SQLAlchemy instance

    def __init__(self, celery_app: Celery, saga_id: int):
        if not self.saga_state_repository:
            raise AttributeError('to run stateful saga, you must set '
                                 '"saga_state_repository" class property')

        super().__init__(celery_app, saga_id)

    @property
    def saga_state(self):
        if not self._saga_state:
            self._saga_state = self.saga_state_repository.get_saga_state_by_id(self.saga_id)

        return self._saga_state

    def run_step(self, step: BaseStep):
        self.saga_state_repository.update_status(self.saga_id, status=f'{step.name}.running')
        super().run_step(step)

    def compensate_step(self, step: BaseStep, initial_failure_payload: dict):
        self.saga_state_repository.update_status(self.saga_id, status=f'{step.name}.compensating')
        super().compensate_step(step, initial_failure_payload)
        self.saga_state_repository.update_status(self.saga_id, status=f'{step.name}.compensated')

    def on_step_success(self, step: AsyncStep, *args, **kwargs):
        self.saga_state_repository.update_status(self.saga_id, status=f'{step.name}.succeeded')
        super().on_step_success(step, *args, **kwargs)

    def on_step_failure(self, step: AsyncStep, *args, **kwargs):
        self.saga_state_repository.update_status(self.saga_id, status=f'{step.name}.failed')
        super().on_step_failure(step, *args, **kwargs)

    def on_saga_success(self):
        self.saga_state_repository.update_status(self.saga_id, 'succeeded')
        super().on_saga_success()

    def on_saga_failure(self, initial_failure_payload: dict, *args, **kwargs):
        self.saga_state_repository.update_status(self.saga_id, 'failed')
        super().on_saga_failure(initial_failure_payload, *args, **kwargs)
