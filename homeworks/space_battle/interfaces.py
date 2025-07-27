from abc import ABC, abstractmethod

from homeworks.space_battle.models import Point, Vector, Angle


class MovingObject(ABC):
    @abstractmethod
    def get_location(self) -> Point:
        pass

    @abstractmethod
    def get_velocity(self) -> Vector:
        pass

    @abstractmethod
    def set_location(self, new_point: Point) -> None:
        pass


class RotatableObject(ABC):
    @abstractmethod
    def get_angle(self) -> Angle:
        pass

    @abstractmethod
    def set_angle(self, new_angle: Angle) -> None:
        pass
