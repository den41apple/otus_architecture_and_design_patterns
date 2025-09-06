"""
Генератор адаптеров по интерфейсам.

Модуль для автоматической генерации адаптеров, которые реализуют интерфейсы
и делегируют вызовы методов к UObject через IoC контейнер.
"""

import inspect
import re
from abc import ABC
from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

from homeworks.space_battle.ioc import IoC
from homeworks.space_battle.uobject import UObject

T = TypeVar("T")


class AdapterGenerator:
    """Генератор адаптеров по интерфейсам."""

    @staticmethod
    def generate_adapter_class(interface_class: type[ABC]) -> type:
        """
        Генерирует класс адаптера для указанного интерфейса.
        """
        if not inspect.isabstract(interface_class):
            raise ValueError(f"Класс {interface_class.__name__} не является абстрактным")

        # Получаем все абстрактные методы интерфейса
        abstract_methods = AdapterGenerator._get_abstract_methods(interface_class)

        # Создаем словарь методов для класса
        methods = {}
        methods["__init__"] = AdapterGenerator._create_init_method()

        # Генерируем методы для каждого абстрактного метода
        for method_name, method_info in abstract_methods.items():
            methods[method_name] = AdapterGenerator._create_method_implementation(
                method_name, method_info
            )

        # Создаем класс адаптера
        adapter_class_name = f"{interface_class.__name__}Adapter"
        return type(adapter_class_name, (interface_class,), methods)

    @staticmethod
    def _get_abstract_methods(interface_class: type[ABC]) -> dict[str, dict[str, Any]]:
        """
        Извлекает информацию об абстрактных методах интерфейса.
        """
        methods = {}

        for name, method in inspect.getmembers(interface_class, predicate=inspect.isfunction):
            if getattr(method, "__isabstractmethod__", False):
                signature = inspect.signature(method)
                type_hints = get_type_hints(method)

                methods[name] = {
                    "signature": signature,
                    "type_hints": type_hints,
                    "return_type": type_hints.get("return", None),
                    "parameters": list(signature.parameters.keys()),
                }

        return methods

    @staticmethod
    def _create_init_method() -> Callable:
        """Создает метод __init__ для адаптера."""

        def init_method(self, obj: UObject):
            self.obj = obj

        return init_method

    @staticmethod
    def _create_method_implementation(method_name: str, method_info: dict[str, Any]) -> Callable:
        """
        Создает реализацию метода адаптера.
        """
        return_type = method_info["return_type"]

        # Определяем тип операции (get/set)
        operation_type = AdapterGenerator._determine_operation_type(method_name)

        if operation_type == "get":
            return AdapterGenerator._create_getter_method(method_name)
        if operation_type == "set":
            return AdapterGenerator._create_setter_method(method_name)
        return AdapterGenerator._create_command_method(method_name, return_type)

    @staticmethod
    def _determine_operation_type(method_name: str) -> str:
        """
        Определяет тип операции метода (get/set/command).
        """
        if method_name.startswith(("get_", "get")):
            return "get"
        if method_name.startswith(("set_", "set")):
            return "set"
        return "command"

    @staticmethod
    def _create_getter_method(method_name: str) -> Callable:
        """
        Создает геттер метод.
        """

        def method(self):
            # Извлекаем имя свойства из имени метода
            property_name = AdapterGenerator._extract_property_name(method_name)
            key = f"{self.__class__.__bases__[0].__name__}:{property_name}.get"

            return IoC.resolve(key, self.obj)

        return method

    @staticmethod
    def _create_setter_method(method_name: str) -> Callable:
        """
        Создает сеттер метод.
        """

        def method(self, new_value):
            # Извлекаем имя свойства из имени метода
            property_name = AdapterGenerator._extract_property_name(method_name)
            key = f"{self.__class__.__bases__[0].__name__}:{property_name}.set"

            command = IoC.resolve(key, self.obj, new_value)
            return command.execute()

        return method

    @staticmethod
    def _create_command_method(method_name: str, return_type: type) -> Callable:
        """
        Создает команду метод.
        """

        def method(self, *args, **kwargs):
            key = f"{self.__class__.__bases__[0].__name__}:{method_name}"

            if return_type is None or return_type is type(None):
                # Метод без возвращаемого значения
                command = IoC.resolve(key, self.obj, *args, **kwargs)
                command.execute()
                return None
            # Метод с возвращаемым значением
            return IoC.resolve(key, self.obj, *args, **kwargs)

        return method

    @staticmethod
    def _extract_property_name(method_name: str) -> str:
        """Извлекает имя свойства из имени метода."""
        # Убираем префиксы get_/set_/get/set
        return re.sub(r"^(get_|set_|get|set)", "", method_name)


class AdapterResolver:
    """
    Резолвер адаптеров через IoC контейнер.
    """

    @staticmethod
    def resolve_adapter(interface_class: type[ABC], obj: UObject) -> Any:
        """
        Разрешает адаптер для указанного интерфейса и объекта
        """
        adapter_class = AdapterGenerator.generate_adapter_class(interface_class)

        # Создаем экземпляр адаптера
        return adapter_class(obj)


def register_adapter_resolver():
    """
    Регистрирует резолвер адаптеров в IoC контейнере.
    """

    def resolve_adapter_command(interface_class: type[ABC], obj: UObject) -> Any:
        return AdapterResolver.resolve_adapter(interface_class, obj)

    IoC.resolve("IoC.RegisterGlobal", "Adapter", resolve_adapter_command).execute()
