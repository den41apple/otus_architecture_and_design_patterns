from queue import Queue
from typing import Any

from homeworks.space_battle.commands import (
    LogCommand,
    RetryIfExceptionCommand,
    SecondRetryIfExceptionCommand,
)
from homeworks.space_battle.handlers import (
    LogExceptionHandler,
    RetryIfExceptionHandler,
    RetryOnceThenLogExceptionHandler,
    RetryTwiceThenLogExceptionHandler,
)
from homeworks.space_battle.interfaces import CommandInterface


def dequeue_one(queue: Queue) -> Any:
    item = queue.get_nowait()
    assert queue.empty()
    return item


def test_log_enqueues(command: CommandInterface) -> None:
    """LogExceptionHandler: ставит LogCommand в очередь"""
    queue: Queue = Queue()
    h = LogExceptionHandler(queue=queue)

    exc: Exception = RuntimeError("x")
    h.handle(exc=exc, command=command)

    enq = dequeue_one(queue=queue)
    assert isinstance(enq, LogCommand)
    # Выполнение LogCommand печатает строку в stdout — проверим, что не падает
    enq.execute()


def test_retry_enqueues_wrapper(command: CommandInterface) -> None:
    """RetryIfExceptionHandler: ставит RetryIfExceptionCommand в очередь"""
    queue: Queue = Queue()
    h = RetryIfExceptionHandler(queue=queue)

    exc: Exception = RuntimeError("x")
    h.handle(exc=exc, command=command)

    enq = dequeue_one(queue=queue)
    assert isinstance(enq, RetryIfExceptionCommand)
    assert enq.command is command


def test_retry_once_then_log(command: CommandInterface) -> None:
    """Стратегия п.8: при первом исключении — повтор, при втором — лог"""
    queue: Queue = Queue()
    h = RetryOnceThenLogExceptionHandler(queue=queue)

    exc1: Exception = RuntimeError("e1")
    # 1-я ошибка: должна появиться RetryIfExceptionCommand
    h.handle(exc=exc1, command=command)
    first = dequeue_one(queue=queue)
    assert isinstance(first, RetryIfExceptionCommand)
    assert first.command is command

    exc2: Exception = RuntimeError("e2")
    # 2-я ошибка: если падает обёртка — логируем оригинал
    h.handle(exc=exc2, command=first)
    second = dequeue_one(queue=queue)
    assert isinstance(second, LogCommand)
    # убеждаемся, что внутри хранится оригинальная команда
    second.execute()


def test_retry_twice_then_log(command: CommandInterface) -> None:
    """Стратегия п.9: два повтора, затем лог"""
    queue: Queue = Queue()
    h = RetryTwiceThenLogExceptionHandler(queue=queue)

    exc1: Exception = RuntimeError("e1")
    # 1-я ошибка: кладём RetryIfExceptionCommand
    h.handle(exc=exc1, command=command)
    first = dequeue_one(queue=queue)
    assert isinstance(first, RetryIfExceptionCommand)
    assert first.command is command

    exc2: Exception = RuntimeError("e2")
    # 2-я ошибка (упал 1-й повтор): кладём SecondRetryIfExceptionCommand
    h.handle(exc=exc2, command=first)
    second = dequeue_one(queue=queue)
    assert isinstance(second, SecondRetryIfExceptionCommand)
    assert second.command is command

    exc3: Exception = RuntimeError("e3")
    # 3-я ошибка (упал 2-й повтор): логируем оригинал
    h.handle(exc=exc3, command=second)
    third = dequeue_one(queue=queue)
    assert isinstance(third, LogCommand)
    third.execute()
