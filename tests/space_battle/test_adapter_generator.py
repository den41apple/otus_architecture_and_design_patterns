"""
Тесты для генератора адаптеров.
"""

import inspect
from abc import ABC, abstractmethod
from typing import Any

import pytest

from homeworks.space_battle.adapter_generator import (
    AdapterGenerator,
    register_adapter_resolver,
)
from homeworks.space_battle.interfaces import CommandInterface
from homeworks.space_battle.ioc import IoC
from homeworks.space_battle.models import Point, Vector
from homeworks.space_battle.uobject import UObject


class TestInterface(ABC):
    """Тестовый интерфейс для проверки генерации адаптеров."""

    @abstractmethod
    def get_position(self) -> Point:
        pass

    @abstractmethod
    def set_position(self, new_value: Point) -> None:
        pass

    @abstractmethod
    def get_velocity(self) -> Vector:
        pass

    @abstractmethod
    def move(self, direction: Vector) -> None:
        pass

    @abstractmethod
    def finish(self) -> None:
        pass


class TestInterfaceWithReturn(ABC):
    """Тестовый интерфейс с методами, возвращающими значения."""

    @abstractmethod
    def get_position(self) -> Point:
        pass

    @abstractmethod
    def set_position(self, new_value: Point) -> Point:
        pass


class MockCommand(CommandInterface):
    """Тестовая команда для проверки выполнения."""

    def __init__(self, obj: UObject, value: Any = None):
        self.obj = obj
        self.value = value
        self.executed = False

    def execute(self) -> None:
        self.executed = True
        if self.value is not None:
            self.obj.set_property("last_command_value", self.value)


class MockCommandWithReturn(CommandInterface):
    """Тестовая команда с возвращаемым значением."""

    def __init__(self, obj: UObject, return_value: Any):
        self.obj = obj
        self.return_value = return_value

    def execute(self) -> Any:
        return self.return_value


@pytest.fixture(autouse=True)
def setup():
    IoC._strategies.clear()
    IoC._scopes.clear()
    IoC._current_scope = type("local", (), {})()

    # Регистрируем тестовые стратегии
    def get_position_strategy(obj: UObject) -> Point:
        return obj.get_property("position") or Point(0, 0)

    def set_position_strategy(obj: UObject, new_value: Point) -> MockCommand:
        return MockCommand(obj, new_value)

    def get_velocity_strategy(obj: UObject) -> Vector:
        return obj.get_property("velocity") or Vector(0, 0)

    def move_strategy(obj: UObject, direction: Vector) -> MockCommand:
        return MockCommand(obj, direction)

    def finish_strategy(obj: UObject) -> MockCommand:
        return MockCommand(obj, "finished")

    def set_position_return_strategy(obj: UObject, new_value: Point) -> MockCommandWithReturn:
        return MockCommandWithReturn(obj, new_value)

    # Регистрируем стратегии в IoC
    IoC.resolve("IoC.RegisterGlobal", "TestInterface:position.get", get_position_strategy).execute()
    IoC.resolve("IoC.RegisterGlobal", "TestInterface:position.set", set_position_strategy).execute()
    IoC.resolve("IoC.RegisterGlobal", "TestInterface:velocity.get", get_velocity_strategy).execute()
    IoC.resolve("IoC.RegisterGlobal", "TestInterface:move", move_strategy).execute()
    IoC.resolve("IoC.RegisterGlobal", "TestInterface:finish", finish_strategy).execute()
    IoC.resolve(
        "IoC.RegisterGlobal", "TestInterfaceWithReturn:position.get", get_position_strategy
    ).execute()
    IoC.resolve(
        "IoC.RegisterGlobal", "TestInterfaceWithReturn:position.set", set_position_return_strategy
    ).execute()

    # Регистрируем резолвер адаптеров
    register_adapter_resolver()


def test_generate_adapter_class():
    """Генерация класса адаптера для интерфейса."""
    adapter_class = AdapterGenerator.generate_adapter_class(TestInterface)

    # Проверяем, что класс создан
    assert adapter_class is not None
    assert adapter_class.__name__ == "TestInterfaceAdapter"
    assert issubclass(adapter_class, TestInterface)

    # Проверяем наличие методов
    assert hasattr(adapter_class, "__init__")
    assert hasattr(adapter_class, "get_position")
    assert hasattr(adapter_class, "set_position")
    assert hasattr(adapter_class, "get_velocity")
    assert hasattr(adapter_class, "move")
    assert hasattr(adapter_class, "finish")


def test_adapter_initialization():
    """Инициализация адаптера с UObject."""
    adapter_class = AdapterGenerator.generate_adapter_class(TestInterface)
    obj = UObject()
    adapter = adapter_class(obj)

    assert adapter.obj is obj


def test_adapter_getter_methods():
    """Тестирование геттер методов адаптера."""
    adapter_class = AdapterGenerator.generate_adapter_class(TestInterface)
    obj = UObject()
    obj.set_property("position", Point(10, 20))
    obj.set_property("velocity", Vector(5, 3))

    adapter = adapter_class(obj)

    # Тестируем геттеры
    position = adapter.get_position()
    assert position == Point(10, 20)

    velocity = adapter.get_velocity()
    assert velocity == Vector(5, 3)


def test_adapter_setter_methods():
    """Тестирование сеттер методов адаптера."""
    adapter_class = AdapterGenerator.generate_adapter_class(TestInterface)
    obj = UObject()
    adapter = adapter_class(obj)

    # Тестируем сеттер
    new_position = Point(30, 40)
    adapter.set_position(new_position)

    # Проверяем, что команда была выполнена
    assert obj.get_property("last_command_value") == new_position


def test_adapter_command_methods():
    """Тестирование командных методов адаптера."""
    adapter_class = AdapterGenerator.generate_adapter_class(TestInterface)
    obj = UObject()
    adapter = adapter_class(obj)

    # Тестируем команду move
    direction = Vector(2, 3)
    adapter.move(direction)

    # Проверяем, что команда была выполнена
    assert obj.get_property("last_command_value") == direction

    # Тестируем команду finish
    adapter.finish()

    # Проверяем, что команда была выполнена
    assert obj.get_property("last_command_value") == "finished"


def test_adapter_with_return_values():
    """Тестирование адаптера с методами, возвращающими значения."""
    adapter_class = AdapterGenerator.generate_adapter_class(TestInterfaceWithReturn)
    obj = UObject()
    adapter = adapter_class(obj)

    # Тестируем геттер
    obj.set_property("position", Point(15, 25))
    position = adapter.get_position()
    assert position == Point(15, 25)

    # Тестируем сеттер с возвращаемым значением
    new_position = Point(50, 60)
    result = adapter.set_position(new_position)
    assert result == new_position


def test_adapter_resolver():
    """Тестирование резолвера адаптеров."""
    obj = UObject()
    obj.set_property("position", Point(100, 200))

    # Используем резолвер через IoC
    adapter = IoC.resolve("Adapter", TestInterface, obj)

    assert adapter is not None
    assert isinstance(adapter, TestInterface)
    assert adapter.obj is obj

    # Проверяем, что методы работают
    position = adapter.get_position()
    assert position == Point(100, 200)


def test_adapter_with_multiple_objects():
    """Тестирование адаптеров для разных объектов."""
    obj1 = UObject()
    obj1.set_property("position", Point(1, 2))

    obj2 = UObject()
    obj2.set_property("position", Point(3, 4))

    adapter1 = IoC.resolve("Adapter", TestInterface, obj1)
    adapter2 = IoC.resolve("Adapter", TestInterface, obj2)

    # Проверяем изоляцию объектов
    assert adapter1.get_position() == Point(1, 2)
    assert adapter2.get_position() == Point(3, 4)

    # Проверяем, что это разные экземпляры
    assert adapter1 is not adapter2
    assert adapter1.obj is not adapter2.obj


def test_adapter_error_handling():
    """Тестирование обработки ошибок в адаптерах."""
    adapter_class = AdapterGenerator.generate_adapter_class(TestInterface)
    obj = UObject()
    adapter = adapter_class(obj)

    # Тестируем вызов метода без зарегистрированной стратегии
    with pytest.raises(ValueError, match="Зависимость 'TestInterface:unknown_method' не найдена"):
        # Создаем метод с неизвестным ключом
        def unknown_method(self):
            return IoC.resolve("TestInterface:unknown_method", self.obj)

        adapter.unknown_method = unknown_method.__get__(adapter, adapter_class)
        adapter.unknown_method()


def test_adapter_with_non_abstract_class():
    """Тестирование ошибки при попытке создать адаптер для неабстрактного класса."""

    class NonAbstractClass:
        def some_method(self):
            pass

    with pytest.raises(ValueError, match="Класс NonAbstractClass не является абстрактным"):
        AdapterGenerator.generate_adapter_class(NonAbstractClass)


def test_adapter_method_signature_preservation():
    """Тестирование сохранения сигнатур методов в адаптере."""
    adapter_class = AdapterGenerator.generate_adapter_class(TestInterface)

    # Проверяем, что методы имеют правильные сигнатуры

    # Проверяем сигнатуру get_position
    get_pos_sig = inspect.signature(adapter_class.get_position)
    assert len(get_pos_sig.parameters) == 1  # только self

    # Проверяем сигнатуру set_position
    set_pos_sig = inspect.signature(adapter_class.set_position)
    assert len(set_pos_sig.parameters) == 2  # self и new_value

    # Проверяем сигнатуру move (команды используют *args, **kwargs)
    move_sig = inspect.signature(adapter_class.move)
    assert "args" in move_sig.parameters  # должен иметь *args
    assert "kwargs" in move_sig.parameters  # должен иметь **kwargs
