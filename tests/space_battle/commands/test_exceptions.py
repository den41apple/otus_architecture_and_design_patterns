from queue import Queue
from unittest.mock import Mock

from pytest import MonkeyPatch

from homeworks.space_battle.commands import Command, LogCommand, RetryIfExceptionCommand
from homeworks.space_battle.handlers import RetryOnceThenLogExceptionHandler
from homeworks.space_battle.interfaces import CommandInterface


def test_execute_delegates_to_handler() -> None:
    """BaseCommand.execute(): ловит исключение и делегирует обработчику"""
    # исходная команда, которая падает при execute()
    inner: CommandInterface = Mock(spec=CommandInterface)
    inner.execute.side_effect = ValueError("fail")

    # обёртка Command с подставленным обработчиком
    cmd = Command(command=inner)
    handler = Mock()
    handler.handle = Mock()
    # подменяем хэндлер
    cmd._exception_handler = handler  # type: ignore[attr-defined]

    # выполнение не должно выбрасывать — исключение уходит в handler
    cmd.execute()

    assert handler.handle.call_count == 1


def test_execute_retry_once_flow(monkeypatch: MonkeyPatch) -> None:
    """Интеграция (п.8): первая ошибка — retry, вторая — log"""
    # исходная команда падает
    inner: CommandInterface = Mock(spec=CommandInterface)
    inner.execute.side_effect = RuntimeError("boom")

    # очередь, куда handler будет класть команды
    queue: Queue = Queue()
    handler = RetryOnceThenLogExceptionHandler(queue=queue)

    # Команда-обёртка
    cmd = Command(command=inner)
    cmd._exception_handler = handler  # type: ignore[attr-defined]

    # Шаг 1: при выполнении cmd произойдёт исключение → handler положит RetryIfExceptionCommand
    cmd.execute()
    first = queue.get_nowait()
    assert isinstance(first, RetryIfExceptionCommand)
    assert first.command is inner

    # Шаг 2: симулируем, что повтор тоже упал — вызываем handler с этой обёрткой
    handler.handle(exc=RuntimeError("boom-2"), command=first)
    second = queue.get_nowait()
    assert isinstance(second, LogCommand)
