import threading
from collections.abc import Callable
from typing import Any, ClassVar, TypeVar

from homeworks.space_battle.interfaces import CommandInterface

T = TypeVar("T")

__all__ = [
    "ClearScopeCommand",
    "IoC",
    "NewScopeCommand",
    "RegisterCommand",
    "RegisterGlobalCommand",
    "SetCurrentScopeCommand",
]


class IoC:
    """
    IoC контейнер для разрешения зависимостей.
    Поддерживает скоупы и регистрацию стратегий разрешения зависимостей.
    """

    _strategies: ClassVar[dict[str, Callable[..., Any]]] = {}
    _scopes: ClassVar[dict[str, dict[str, Any]]] = {}
    _current_scope: ClassVar[threading.local] = threading.local()

    @classmethod
    def resolve(cls, key: str, *args, **kwargs) -> T:
        """
        Разрешить зависимость по ключу.

        Args:
            key: Ключ зависимости
            *args: Аргументы для создания объекта
            **kwargs: Именованные аргументы для создания объекта

        Returns:
            Объект зависимости
        """
        if key == "IoC.Register":
            return RegisterCommand(*args, **kwargs)
        if key == "IoC.RegisterGlobal":
            return RegisterGlobalCommand(*args, **kwargs)
        if key == "Scopes.New":
            return NewScopeCommand(*args, **kwargs)
        if key == "Scopes.Current":
            return SetCurrentScopeCommand(*args, **kwargs)
        if key == "Scopes.Clear":
            return ClearScopeCommand(*args, **kwargs)

        return cls._resolve_dependency(key, *args, **kwargs)

    @classmethod
    def _resolve_dependency(cls, key: str, *args, **kwargs) -> T:
        """Разрешить зависимость из скоупов или глобальных стратегий."""
        current_scope_id = cls._get_current_scope_id()
        scope_data = cls._get_scope_data(current_scope_id)

        if key in scope_data:
            strategy = scope_data[key]
            if callable(strategy):
                return strategy(*args, **kwargs)
            return strategy

        if key in cls._strategies:
            strategy = cls._strategies[key]
            if callable(strategy):
                return strategy(*args, **kwargs)
            return strategy

        raise ValueError(f"Зависимость '{key}' не найдена")

    @classmethod
    def _get_current_scope_id(cls) -> str:
        """Получить ID текущего скоупа."""
        if not hasattr(cls._current_scope, "scope_id"):
            cls._current_scope.scope_id = "root"
        return cls._current_scope.scope_id

    @classmethod
    def _get_scope_data(cls, scope_id: str) -> dict[str, Any]:
        """Получить данные скоупа по ID."""
        if scope_id not in cls._scopes:
            cls._scopes[scope_id] = {}
        return cls._scopes[scope_id]


class RegisterCommand(CommandInterface):
    """Команда для регистрации зависимости в IoC контейнере."""

    def __init__(self, key: str, strategy: Callable[..., Any]):
        self.key = key
        self.strategy = strategy

    def execute(self) -> None:
        current_scope_id = IoC._get_current_scope_id()
        scope_data = IoC._get_scope_data(current_scope_id)
        scope_data[self.key] = self.strategy


class RegisterGlobalCommand(CommandInterface):
    """Команда для глобальной регистрации зависимости в IoC контейнере."""

    def __init__(self, key: str, strategy: Callable[..., Any]):
        self.key = key
        self.strategy = strategy

    def execute(self) -> None:
        IoC._strategies[self.key] = self.strategy


class NewScopeCommand(CommandInterface):
    """Команда для создания нового скоупа."""

    def __init__(self, scope_id: str):
        self.scope_id = scope_id

    def execute(self) -> None:
        IoC._scopes[self.scope_id] = {}


class SetCurrentScopeCommand(CommandInterface):
    """Команда для установки текущего скоупа."""

    def __init__(self, scope_id: str):
        self.scope_id = scope_id

    def execute(self) -> None:
        IoC._current_scope.scope_id = self.scope_id


class ClearScopeCommand(CommandInterface):
    """Команда для очистки скоупа."""

    def __init__(self, scope_id: str):
        self.scope_id = scope_id

    def execute(self) -> None:
        if self.scope_id in IoC._scopes:
            del IoC._scopes[self.scope_id]
        if hasattr(IoC._current_scope, "scope_id") and IoC._current_scope.scope_id == self.scope_id:
            IoC._current_scope.scope_id = "root"
