import math

from homeworks.space_battle.interfaces import MovingObjectInterface, RotatableObjectInterface
from homeworks.space_battle.models import Angle, Point, Vector
from homeworks.space_battle.uobject import UObject


class MovingObjectAdapter(MovingObjectInterface):
    def __init__(self, u_obj: UObject):
        self.uobj = u_obj

    def get_location(self) -> Point | None:
        pt = self.uobj.get_property("location")
        if pt is not None:
            return Point(x=int(pt.x), y=int(pt.y))
        return pt

    def get_velocity(self) -> Vector | None:
        angle: Angle = self.uobj.get_property("angle")
        velocity: float = self.uobj.get_property("velocity")
        if angle is not None and velocity is not None:
            radian = angle.radians()
            vx = int(velocity * math.cos(radian))
            vy = int(velocity * math.sin(radian))
            return Vector(x=vx, y=vy)
        return None

    def set_location(self, new_point: Point):
        self.uobj.set_property(
            property_="location",
            value=Point(x=int(new_point.x), y=int(new_point.y)),
        )


class RotatableObjectAdapter(RotatableObjectInterface):
    def __init__(self, uobj: UObject):
        self.uobj = uobj

    def get_angle(self) -> Angle:
        return self.uobj.get_property("angle")

    def set_angle(self, new_angle: Angle) -> None:
        self.uobj.set_property(property_="angle", value=new_angle)
