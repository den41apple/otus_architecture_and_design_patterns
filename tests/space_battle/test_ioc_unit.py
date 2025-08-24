"""
Юнит-тесты для IOC контейнера.
Тестируют базовый функционал без многопоточности.
"""

from unittest.mock import Mock

import pytest

from homeworks.space_battle.ioc import (
    ClearScopeCommand,
    IoC,
    NewScopeCommand,
    RegisterCommand,
    SetCurrentScopeCommand,
)


@pytest.fixture(autouse=True)
def setup():
    """Очистка состояния перед каждым тестом."""
    IoC._strategies.clear()
    IoC._scopes.clear()
    IoC._current_scope = type("MockThreadLocal", (), {})()
    IoC._current_scope.scope_id = "root"


def test_register_and_resolve_dependency():
    """Регистрация зависимости в IoC и её последующее разрешение."""
    # Регистрируем зависимость
    mock_strategy = Mock(return_value="test_value")
    register_cmd = IoC.resolve("IoC.Register", "test_key", mock_strategy)
    register_cmd.execute()

    # Разрешаем зависимость
    result = IoC.resolve("test_key")
    assert result == "test_value"
    mock_strategy.assert_called_once()


def test_resolve_nonexistent_dependency():
    """Попытка разрешить несуществующую зависимость должна вызывать ValueError."""
    with pytest.raises(ValueError, match="Зависимость 'nonexistent' не найдена"):
        IoC.resolve("nonexistent")


def test_resolve_with_arguments():
    """Разрешение зависимости с передачей позиционных и именованных аргументов."""

    def strategy_with_args(arg1, arg2, kwarg1=None):
        return f"{arg1}_{arg2}_{kwarg1}"

    register_cmd = IoC.resolve("IoC.Register", "test_key", strategy_with_args)
    register_cmd.execute()

    result = IoC.resolve("test_key", "value1", "value2", kwarg1="kwvalue")
    assert result == "value1_value2_kwvalue"


def test_create_new_scope():
    """Создание нового скоупа для изоляции зависимостей."""
    new_scope_cmd = IoC.resolve("Scopes.New", "test_scope")
    new_scope_cmd.execute()

    assert "test_scope" in IoC._scopes
    assert IoC._scopes["test_scope"] == {}


def test_set_current_scope():
    """Установка конкретного скоупа как текущего активного."""
    # Создаем скоуп
    new_scope_cmd = IoC.resolve("Scopes.New", "test_scope")
    new_scope_cmd.execute()

    # Устанавливаем как текущий
    set_scope_cmd = IoC.resolve("Scopes.Current", "test_scope")
    set_scope_cmd.execute()

    assert IoC._current_scope.scope_id == "test_scope"


def test_register_in_scope():
    """Регистрация зависимости в конкретном скоупе с проверкой изоляции от других скоупов."""
    # Создаем скоуп и устанавливаем как текущий
    IoC.resolve("Scopes.New", "test_scope").execute()
    IoC.resolve("Scopes.Current", "test_scope").execute()

    # Регистрируем зависимость
    mock_strategy = Mock(return_value="scope_value")
    register_cmd = IoC.resolve("IoC.Register", "scope_test_key", mock_strategy)
    register_cmd.execute()

    # Проверяем, что зависимость доступна в скоупе
    result = IoC.resolve("scope_test_key")
    assert result == "scope_value"

    # Проверяем, что в корневом скоупе её нет
    IoC.resolve("Scopes.Current", "root").execute()
    with pytest.raises(ValueError):
        IoC.resolve("scope_test_key")


def test_clear_scope():
    """Удаление скоупа и сброс текущего скоупа в root при очистке."""
    # Создаем скоуп и регистрируем зависимость
    IoC.resolve("Scopes.New", "test_scope").execute()
    IoC.resolve("Scopes.Current", "test_scope").execute()

    mock_strategy = Mock(return_value="test_value")
    IoC.resolve("IoC.Register", "clear_test_key", mock_strategy).execute()

    # Очищаем скоуп
    clear_cmd = IoC.resolve("Scopes.Clear", "test_scope")
    clear_cmd.execute()

    # Проверяем, что скоуп удален
    assert "test_scope" not in IoC._scopes

    # Проверяем, что текущий скоуп сброшен в root
    assert IoC._current_scope.scope_id == "root"


def test_global_registration():
    """Глобальная регистрация зависимостей доступна из любого скоупа."""
    mock_strategy = Mock(return_value="global_value")
    IoC.resolve("IoC.RegisterGlobal", "global_key", mock_strategy).execute()

    # Проверяем, что доступна из любого скоупа
    result = IoC.resolve("global_key")
    assert result == "global_value"

    # Создаем новый скоуп и проверяем доступность
    IoC.resolve("Scopes.New", "test_scope").execute()
    IoC.resolve("Scopes.Current", "test_scope").execute()

    result = IoC.resolve("global_key")
    assert result == "global_value"


def test_scope_isolation():
    """Проверка изоляции скоупов - каждый скоуп имеет свои версии зависимостей."""
    # Регистрируем в корневом скоупе
    root_strategy = Mock(return_value="root_value")
    IoC.resolve("IoC.Register", "isolation_shared_key", root_strategy).execute()

    # Создаем новый скоуп и регистрируем ту же зависимость
    IoC.resolve("Scopes.New", "test_scope").execute()
    IoC.resolve("Scopes.Current", "test_scope").execute()

    scope_strategy = Mock(return_value="scope_value")
    IoC.resolve("IoC.Register", "isolation_shared_key", scope_strategy).execute()

    # В скоупе должна быть своя версия
    result = IoC.resolve("isolation_shared_key")
    assert result == "scope_value"

    # В корневом скоупе должна быть своя версия
    IoC.resolve("Scopes.Current", "root").execute()
    result = IoC.resolve("isolation_shared_key")
    assert result == "root_value"


def test_command_execution():
    """Проверка корректности выполнения всех типов команд IoC."""
    # Тест RegisterCommand
    mock_strategy = Mock(return_value="test_value")
    register_cmd = RegisterCommand("exec_test_key", mock_strategy)
    register_cmd.execute()

    assert "exec_test_key" in IoC._scopes["root"]

    # Тест NewScopeCommand
    new_scope_cmd = NewScopeCommand("test_scope")
    new_scope_cmd.execute()

    assert "test_scope" in IoC._scopes

    # Тест SetCurrentScopeCommand
    set_scope_cmd = SetCurrentScopeCommand("test_scope")
    set_scope_cmd.execute()

    assert IoC._current_scope.scope_id == "test_scope"

    # Тест ClearScopeCommand
    clear_cmd = ClearScopeCommand("test_scope")
    clear_cmd.execute()

    assert "test_scope" not in IoC._scopes
    assert IoC._current_scope.scope_id == "root"


def test_resolve_with_kwargs():
    """Разрешение зависимости с передачей именованных аргументов в стратегию."""

    def strategy_with_kwargs(name, age=25, city="Moscow"):
        return f"{name}_{age}_{city}"

    register_cmd = IoC.resolve("IoC.Register", "person_strategy", strategy_with_kwargs)
    register_cmd.execute()

    result = IoC.resolve("person_strategy", "John", city="NYC")
    assert result == "John_25_NYC"


def test_resolve_object_strategy():
    """Разрешение зависимости, где стратегия является объектом, а не функцией."""
    test_object = {"key": "value", "number": 42}
    IoC.resolve("IoC.Register", "test_object", test_object).execute()

    result = IoC.resolve("test_object")
    assert result == test_object
    assert result["key"] == "value"
    assert result["number"] == 42


def test_multiple_scopes():
    """Работа с несколькими скоупами и проверка их полной изоляции друг от друга."""
    # Создаем несколько скоупов
    IoC.resolve("Scopes.New", "scope1").execute()
    IoC.resolve("Scopes.New", "scope2").execute()
    IoC.resolve("Scopes.New", "scope3").execute()

    # Регистрируем зависимости в разных скоупах
    IoC.resolve("Scopes.Current", "scope1").execute()
    IoC.resolve("IoC.Register", "key1", lambda: "value1").execute()

    IoC.resolve("Scopes.Current", "scope2").execute()
    IoC.resolve("IoC.Register", "key2", lambda: "value2").execute()

    IoC.resolve("Scopes.Current", "scope3").execute()
    IoC.resolve("IoC.Register", "key3", lambda: "value3").execute()

    # Проверяем изоляцию
    IoC.resolve("Scopes.Current", "scope1").execute()
    assert IoC.resolve("key1") == "value1"
    with pytest.raises(ValueError):
        IoC.resolve("key2")
    with pytest.raises(ValueError):
        IoC.resolve("key3")

    IoC.resolve("Scopes.Current", "scope2").execute()
    assert IoC.resolve("key2") == "value2"
    with pytest.raises(ValueError):
        IoC.resolve("key1")
    with pytest.raises(ValueError):
        IoC.resolve("key3")


def test_scope_nesting():
    """Проверка полной изоляции скоупов - внутренние скоупы не видят внешние и наоборот."""
    # Создаем скоупы
    IoC.resolve("Scopes.New", "outer").execute()
    IoC.resolve("Scopes.Current", "outer").execute()
    IoC.resolve("IoC.Register", "outer_key", lambda: "outer_value").execute()

    IoC.resolve("Scopes.New", "inner").execute()
    IoC.resolve("Scopes.Current", "inner").execute()
    IoC.resolve("IoC.Register", "inner_key", lambda: "inner_value").execute()

    # Каждый скоуп видит только свои зависимости
    assert IoC.resolve("inner_key") == "inner_value"
    with pytest.raises(ValueError):
        IoC.resolve("outer_key")  # Внутренний скоуп не видит внешний

    # Внешний скоуп видит только свои зависимости
    IoC.resolve("Scopes.Current", "outer").execute()
    assert IoC.resolve("outer_key") == "outer_value"
    with pytest.raises(ValueError):
        IoC.resolve("inner_key")  # Внешний скоуп не видит внутренний
