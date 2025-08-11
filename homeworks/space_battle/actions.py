from homeworks.space_battle.interfaces import MovingObjectInterface, RotatableObjectInterface
from homeworks.space_battle.models import Point, Vector, Angle


class Move:
    def __init__(self, moving_object: MovingObjectInterface):
        self._moving_object = moving_object

    def execute(self) -> None:
        location: Point = self._moving_object.get_location()
        velocity: Vector = self._moving_object.get_velocity()
        if location is None:
            raise ValueError("No location")
        if velocity is None:
            raise ValueError("No velocity")
        new_loc: Point = location + velocity
        self._moving_object.set_location(new_loc)


class Rotate:
    def __init__(self, rotatable_object: RotatableObjectInterface):
        self._rotatable_object = rotatable_object

    def execute(self, delta_angle: Angle) -> None:
        angle: Angle = self._rotatable_object.get_angle()
        if angle is None:
            raise ValueError("No angle")
        self._rotatable_object.set_angle(angle + delta_angle)
