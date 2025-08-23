import math

from homeworks.space_battle.actions import Move as MoveAction
from homeworks.space_battle.actions import Rotate as RotateAction
from homeworks.space_battle.adapters import MovingObjectAdapter, RotatableObjectAdapter
from homeworks.space_battle.exceptions import CommandException
from homeworks.space_battle.interfaces import CommandInterface, ExceptionHandlerInterface
from homeworks.space_battle.models import Angle, Vector
from homeworks.space_battle.uobject import UObject


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


class MacroCommand(CommandInterface):
    """
    Простейшая макрокоманда: выполняет список команд последовательно.
    При исключении прерывает цепочку и выбрасывает CommandException.
    """

    def __init__(self, *, commands: list[CommandInterface]):
        self._commands = commands

    def execute(self) -> None:
        for cmd in self._commands:
            try:
                cmd.execute()
            except Exception as exc:
                raise CommandException(
                    f"MacroCommand failed on {type(cmd).__name__}: {exc}"
                ) from exc


class CheckFuelCommand(CommandInterface):
    """Проверяет, что топлива достаточно: fuel >= fuel_burn_rate, иначе CommandException."""

    def __init__(self, *, uobj: UObject):
        self._uobj = uobj

    def execute(self) -> None:
        fuel = self._uobj.get_property("fuel")
        burn_rate = self._uobj.get_property("fuel_burn_rate")
        if fuel is None or burn_rate is None:
            raise CommandException("Не заданы параметры топлива: fuel или fuel_burn_rate")
        if fuel < burn_rate:
            raise CommandException("Недостаточно топлива для движения")


class BurnFuelCommand(CommandInterface):
    """Списывает топливо: fuel = max(0, fuel - fuel_burn_rate)."""

    def __init__(self, *, uobj: UObject):
        self._uobj = uobj

    def execute(self) -> None:
        fuel = self._uobj.get_property("fuel")
        burn_rate = self._uobj.get_property("fuel_burn_rate")
        if fuel is None or burn_rate is None:
            raise CommandException("Не заданы параметры топлива: fuel или fuel_burn_rate")
        new_value = max(0, int(fuel) - int(burn_rate))
        self._uobj.set_property("fuel", new_value)


class MoveCommand(CommandInterface):
    """Команда движения по прямой (оборачивает действие Move)."""

    def __init__(self, *, moving: MovingObjectAdapter):
        self._action = MoveAction(moving)

    def execute(self) -> None:
        self._action.execute()


class RotateCommand(CommandInterface):
    """Команда поворота на delta_angle (оборачивает действие Rotate)."""

    def __init__(self, *, rotatable: RotatableObjectAdapter, delta_angle: Angle):
        self._action = RotateAction(rotatable)
        self._delta = delta_angle

    def execute(self) -> None:
        self._action.execute(self._delta)


class ModifyVelocityOnRotateCommand(CommandInterface):
    """
    При повороте движущегося объекта меняется вектор мгновенной скорости.
    Команда пересчитывает и сохраняет вектор, если объект действительно движется (speed>0).
    Скорость берётся из свойства uobj "velocity" (скаляр), угол — из свойства "angle".
    Результат кладётся в свойство "velocity_vector" типа Vector.
    """

    def __init__(self, *, uobj: UObject):
        self._uobj = uobj

    def execute(self) -> None:
        speed = self._uobj.get_property("velocity")
        angle = self._uobj.get_property("angle")
        if speed is None or angle is None:
            return  # нечего модифицировать
        if int(speed) == 0:
            return
        rad = angle.radians()
        vx = int(int(speed) * math.cos(rad))
        vy = int(int(speed) * math.sin(rad))
        self._uobj.set_property("velocity_vector", Vector(x=vx, y=vy))


class MoveWithFuelMacroCommand(MacroCommand):
    """Движение по прямой с расходом топлива: CheckFuel -> Move -> BurnFuel."""

    def __init__(self, *, uobj: UObject, moving: MovingObjectAdapter):
        super().__init__(
            commands=[
                CheckFuelCommand(uobj=uobj),
                MoveCommand(moving=moving),
                BurnFuelCommand(uobj=uobj),
            ]
        )


class RotateWithVelocityMacroCommand(MacroCommand):
    """Поворот с модификацией вектора скорости: Rotate -> ModifyVelocityOnRotate."""

    def __init__(self, *, uobj: UObject, rotatable: RotatableObjectAdapter, delta_angle: Angle):
        super().__init__(
            commands=[
                RotateCommand(rotatable=rotatable, delta_angle=delta_angle),
                ModifyVelocityOnRotateCommand(uobj=uobj),
            ]
        )
