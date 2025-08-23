from unittest.mock import Mock

import pytest

from homeworks.space_battle.adapters import MovingObjectAdapter, RotatableObjectAdapter
from homeworks.space_battle.commands import (
    BurnFuelCommand,
    CheckFuelCommand,
    MacroCommand,
    ModifyVelocityOnRotateCommand,
    MoveCommand,
    MoveWithFuelMacroCommand,
    RotateCommand,
    RotateWithVelocityMacroCommand,
)
from homeworks.space_battle.exceptions import CommandException
from homeworks.space_battle.models import Angle, Point, Vector
from homeworks.space_battle.uobject import UObject


def make_uobject_with_fuel(fuel: int, fuel_burn_rate: int) -> UObject:
    uobject = UObject()
    uobject.set_property("fuel", fuel)
    uobject.set_property("fuel_burn_rate", fuel_burn_rate)
    return uobject


def test_checkfuel_success():
    """Проверка, что CheckFuelCommand не выбрасывает исключение, если топлива хватает."""
    uobject = make_uobject_with_fuel(fuel=10, fuel_burn_rate=2)
    command = CheckFuelCommand(uobj=uobject)

    command.execute()


def test_checkfuel_raises_if_not_enough():
    """Проверка, что CheckFuelCommand выбрасывает CommandException при нехватке топлива."""
    uobject = make_uobject_with_fuel(fuel=1, fuel_burn_rate=5)
    command = CheckFuelCommand(uobj=uobject)

    with pytest.raises(CommandException):
        command.execute()


def test_burnfuel_reduces_fuel():
    """Проверка, что BurnFuelCommand уменьшает количество топлива на величину расхода."""
    uobject = make_uobject_with_fuel(fuel=10, fuel_burn_rate=3)

    BurnFuelCommand(uobj=uobject).execute()

    assert uobject.get_property("fuel") == 7


def test_burnfuel_not_negative():
    """Проверка, что BurnFuelCommand не уводит топливо в отрицательное значение."""
    uobject = make_uobject_with_fuel(fuel=2, fuel_burn_rate=5)

    BurnFuelCommand(uobj=uobject).execute()

    assert uobject.get_property("fuel") == 0


def test_macrocommand_stops_on_exception(monkeypatch):
    """Проверка, что MacroCommand прерывается при исключении и выбрасывает CommandException."""
    first_command = Mock()
    failing_command = Mock()
    failing_command.execute = Mock(side_effect=ValueError("boom"))
    macro_command = MacroCommand(commands=[first_command, failing_command])

    with pytest.raises(CommandException):
        macro_command.execute()

    first_command.execute.assert_called()
    failing_command.execute.assert_called()


def test_movecommand_updates_location():
    """Проверка, что MoveCommand вызывает корректное смещение объекта."""
    uobject = UObject()
    uobject.set_property("location", Point(0, 0))
    uobject.set_property("velocity", 5)
    uobject.set_property("angle", Angle(0))
    moving_object = MovingObjectAdapter(u_obj=uobject)

    MoveCommand(moving=moving_object).execute()

    assert uobject.get_property("location") == Point(5, 0)


def test_rotatecommand_changes_angle():
    """Проверка, что RotateCommand изменяет угол на заданный delta_angle."""
    uobject = UObject()
    uobject.set_property("angle", Angle(0))
    rotatable_object = RotatableObjectAdapter(uobj=uobject)

    RotateCommand(rotatable=rotatable_object, delta_angle=Angle(90)).execute()

    assert uobject.get_property("angle") == Angle(90)


def test_modify_velocity_sets_vector():
    """Проверка, что ModifyVelocityOnRotateCommand пересчитывает вектор скорости."""
    uobject = UObject()
    uobject.set_property("velocity", 10)
    uobject.set_property("angle", Angle(90))

    ModifyVelocityOnRotateCommand(uobj=uobject).execute()

    velocity_vector = uobject.get_property("velocity_vector")
    assert velocity_vector.x == pytest.approx(0, abs=1)
    assert velocity_vector.y == pytest.approx(10, abs=1)


def test_movewithfuelmacrocommand_full_cycle():
    """Проверка макрокоманды движения с расходом топлива: проверка → движение → списание топлива."""
    uobject = UObject()
    uobject.set_property("fuel", 10)
    uobject.set_property("fuel_burn_rate", 2)
    uobject.set_property("location", Point(0, 0))
    uobject.set_property("velocity", 5)
    uobject.set_property("angle", Angle(0))
    moving_object = MovingObjectAdapter(u_obj=uobject)

    MoveWithFuelMacroCommand(uobj=uobject, moving=moving_object).execute()

    assert uobject.get_property("location") == Point(5, 0)
    assert uobject.get_property("fuel") == 8


def test_rotatewithvelocitymacrocommand_full_cycle():
    """Проверка макрокоманды поворота с модификацией вектора скорости."""
    uobject = UObject()
    uobject.set_property("velocity", 10)
    uobject.set_property("angle", Angle(0))
    rotatable_object = RotatableObjectAdapter(uobj=uobject)

    RotateWithVelocityMacroCommand(
        uobj=uobject, rotatable=rotatable_object, delta_angle=Angle(90)
    ).execute()

    assert uobject.get_property("angle") == Angle(90)
    velocity_vector: Vector = uobject.get_property("velocity_vector")
    assert velocity_vector.x == pytest.approx(0, abs=1)
    assert velocity_vector.y == pytest.approx(10, abs=1)
