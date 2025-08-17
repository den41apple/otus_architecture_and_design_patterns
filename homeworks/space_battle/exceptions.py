from queue import Queue

from homeworks.space_battle.commands import (
    LogCommand,
    RetryIfExceptionCommand,
    SecondRetryIfExceptionCommand,
)
from homeworks.space_battle.interfaces import (
    CommandInterface,
    ExceptionHandlerInterface,
    ExceptionsStorageInterface,
)


class ExceptionsStorage(ExceptionsStorageInterface):
    @classmethod
    def resolve(cls, command: CommandInterface, exc: Exception) -> ExceptionHandlerInterface | None:
        return cls._storage.get(command, {}).get(exc)

    @classmethod
    def register(
        cls, command: CommandInterface, exc: Exception, handler: ExceptionHandlerInterface
    ) -> CommandInterface:
        if command not in cls._storage:
            cls._storage[command] = {}
        cls._storage[command][exc] = handler
        return command


class LogExceptionHandler(ExceptionHandlerInterface):
    """
    Обработчик исключения, который ставит Команду, пишущую в лог в очередь Команд
    """

    def __init__(self, *args, queue: Queue, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._queue = queue

    def handle(self, exc: Exception | type[Exception], command: CommandInterface):
        self._queue.put(LogCommand(exc=exc, command=command))


class RetryExceptionHandler(ExceptionHandlerInterface):
    def __init__(self, *args, queue: Queue, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._queue = queue

    def handle(
        self, exc: Exception | type[Exception], command: CommandInterface
    ) -> CommandInterface:
        pass


class RetryIfExceptionHandler(RetryExceptionHandler):
    """
    Обработчик исключения, который ставит в очередь
    Команду - повторитель команды, выбросившей исключение
    """

    def handle(self, exc: Exception | type[Exception], command: CommandInterface):  # noqa: ARG002
        self._queue.put(RetryIfExceptionCommand(command=command))


class RetryOnceThenLogExceptionHandler(RetryExceptionHandler):
    """
    Стратегия:
        1) при первом исключении — повторить
        2) при втором — записать в лог
    """

    def handle(self, exc: Exception | type[Exception], command: CommandInterface):
        if isinstance(command, RetryIfExceptionCommand):
            # 2) второй  — логируем исходную команду
            self._queue.put(LogCommand(exc=exc, command=command.command))
        else:
            # 1) Первый — ставим один повтор
            self._queue.put(RetryIfExceptionCommand(command=command))


class RetryTwiceThenLogExceptionHandler(RetryExceptionHandler):
    """
    Стратегия:
        1) при первом исключении — повторить
        2) при втором — повторить второй раз
    """

    def handle(self, exc: Exception | type[Exception], command: CommandInterface):
        if isinstance(command, SecondRetryIfExceptionCommand):
            # 3) уже второй повтор не удался — логируем
            self._queue.put(LogCommand(exc=exc, command=command.command))
        elif isinstance(command, RetryIfExceptionCommand):
            # 2) первый повтор не удался — ставим второй повтор
            self._queue.put(SecondRetryIfExceptionCommand(command=command.command))
        else:
            # 1) исходная команда упала — ставим первый повтор
            self._queue.put(RetryIfExceptionCommand(command=command))
