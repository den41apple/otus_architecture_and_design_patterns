from homeworks.space_battle.interfaces import CommandInterface, ExceptionHandlerInterface


class Command(CommandInterface):
    """
    Реализация интерфейса CommandInterface,
    что бы не писать каждый раз что нужно вызывать .execute()
    у дочерних объектов
    """

    _exception_handler: ExceptionHandlerInterface

    def __init__(self, *, command: CommandInterface):
        self.command = command

    def execute(self):
        try:
            self.command.execute()
        except Exception as exc:
            self._exception_handler.handle(exc=exc, command=self.command)


class RetryIfExceptionCommand(Command):
    """
    Повторяет Команду, выбросившую исключение
    """


class SecondRetryIfExceptionCommand(Command):
    """
    Вторая попытка повторить Команду.
    Отличается типом — нужен для стратегии «повторить два раза, потом лог».
    """


class LogCommand(Command):
    def __init__(self, *, exc: Exception, command: CommandInterface):
        super().__init__(command=command)
        self.exc = exc
        self.command = command

    def execute(self) -> None:
        print(f"[LOG] Exception in {type(self.command).__name__}: {self.exc}")
