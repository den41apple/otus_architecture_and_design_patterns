from dataclasses import dataclass

import math


@dataclass
class Point:
    x: int
    y: int

    def __add__(self, other: "Vector") -> "Point":
        if not isinstance(other, Vector):
            return NotImplemented
        # Ensure integer addition and result
        return Point(int(self.x + other.x), int(self.y + other.y))


@dataclass
class Vector:
    x: int
    y: int

    def __add__(self, other: "Vector") -> "Vector":
        if not isinstance(other, Vector):
            return NotImplemented
        # Ensure integer addition and result
        return Vector(int(self.x + other.x), int(self.y + other.y))


@dataclass(frozen=True)
class Angle:
    degrees: int

    def radians(self) -> float:
        """Возвращает угол в радианах."""
        return math.radians(self.degrees)

    def normalized(self) -> "Angle":
        """Возвращает угол, приведённый к диапазону [0, 360)."""
        return Angle(self.degrees % 360)

    def __add__(self, other: "Angle | int") -> "Angle":
        if isinstance(other, Angle):
            return Angle(self.degrees + other.degrees)
        if isinstance(other, int):
            return Angle(self.degrees + other)
        return NotImplemented

    def __sub__(self, other: "Angle | int") -> "Angle":
        if isinstance(other, Angle):
            return Angle(self.degrees - other.degrees)
        if isinstance(other, int):
            return Angle(self.degrees - other)
        return NotImplemented

    def __eq__(self, other: "Angle | int") -> bool:
        if isinstance(other, Angle):
            return self.degrees == other.degrees
        if isinstance(other, int):
            return self.degrees == other
        return False
