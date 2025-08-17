from abc import ABC, abstractmethod

from homeworks.space_battle.models import Point, Vector, Angle


class MovingObjectInterface(ABC):
    @abstractmethod
    def get_location(self) -> Point:
        pass

    @abstractmethod
    def get_velocity(self) -> Vector:
        pass

    @abstractmethod
    def set_location(self, new_point: Point) -> None:
        pass


class RotatableObjectInterface(ABC):
    @abstractmethod
    def get_angle(self) -> Angle:
        pass

    @abstractmethod
    def set_angle(self, new_angle: Angle) -> None:
        pass


class CommandInterface(ABC):
    @abstractmethod
    def execute(self) -> None:
        pass


class ExceptionHandlerInterface(ABC):

    @abstractmethod
    def handle(self, exc: Exception | type[Exception], command: CommandInterface) -> CommandInterface:
        pass


class ExceptionsStorageInterface(ABC):
    _storage: dict[CommandInterface, dict[Exception, ExceptionHandlerInterface]]

    @classmethod
    @abstractmethod
    def resolve(cls, command: CommandInterface, exc: Exception) -> ExceptionHandlerInterface | None:
        pass

    @classmethod
    @abstractmethod
    def register(cls, command: CommandInterface, exc: Exception,
                 handler: ExceptionHandlerInterface) -> CommandInterface:
        pass
