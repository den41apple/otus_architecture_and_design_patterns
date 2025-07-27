import pytest

from homeworks.homework_2.actions import Move
from homeworks.homework_2.adapters import MovingObjectAdapter
from homeworks.homework_2.models import Point, Angle
from homeworks.homework_2.uobject import UObject


def test_move_success():
    """
    Проверяет, что для объекта, находящегося в точке (12, 5) и движущегося со скоростью 7 вдоль оси X, движение меняет положение на (19, 5)
    """
    ship = UObject()
    ship.set_property("location", Point(12, 5))
    ship.set_property("angle", Angle(0))
    ship.set_property("velocity", 7)
    adapter = MovingObjectAdapter(ship)
    move = Move(adapter)
    move.execute()
    assert ship.get_property("location") == Point(19, 5)


def test_move_no_location():
    """
    Проверяет, что попытка сдвинуть объект, у которого невозможно прочитать положение в пространстве, приводит к ошибке
    """
    ship = UObject()
    ship.set_property("angle", Angle(0))
    ship.set_property("velocity", 3)
    adapter = MovingObjectAdapter(ship)
    move = Move(adapter)
    with pytest.raises(ValueError):
        move.execute()


def test_move_no_velocity():
    """
    Проверяет, что попытка сдвинуть объект, у которого невозможно прочитать значение мгновенной скорости, приводит к ошибке
    """
    ship = UObject()
    ship.set_property("location", Point(1, 1))
    ship.set_property("angle", Angle(0))
    adapter = MovingObjectAdapter(ship)
    move = Move(adapter)
    with pytest.raises(ValueError):
        move.execute()


def test_move_set_location_error(monkeypatch):
    """
    Проверяет, что попытка сдвинуть объект, у которого невозможно изменить положение в пространстве, приводит к ошибке
    """
    ship = UObject()
    ship.set_property("location", Point(1, 1))
    ship.set_property("angle", Angle(0))
    ship.set_property("velocity", 1)
    adapter = MovingObjectAdapter(ship)
    move = Move(adapter)

    def broken_set_location(new_value):
        raise Exception("fail")

    adapter.set_location = broken_set_location
    with pytest.raises(Exception):
        move.execute()
