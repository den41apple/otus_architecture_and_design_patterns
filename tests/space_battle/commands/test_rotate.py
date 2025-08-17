import pytest

from homeworks.space_battle.actions import Rotate
from homeworks.space_battle.adapters import RotatableObjectAdapter
from homeworks.space_battle.models import Angle
from homeworks.space_battle.uobject import UObject


def test_rotate_success():
    """
    Проверяет, что поворот объекта вокруг оси работает корректно:
    к текущему углу прибавляется дельта
    """
    ship = UObject()
    ship.set_property("angle", Angle(45))
    adapter = RotatableObjectAdapter(ship)
    rotate = Rotate(adapter)
    rotate.execute(Angle(15))
    assert ship.get_property("angle") == 60


def test_rotate_no_angle():
    """
    Проверяет, что попытка повернуть объект без определённого угла приводит к ошибке
    """
    ship = UObject()
    adapter = RotatableObjectAdapter(ship)
    rotate = Rotate(adapter)
    with pytest.raises(ValueError):
        rotate.execute(10)
