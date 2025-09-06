"""
Домашнее задание №5 - Реализация IoC контейнера.

Этот модуль содержит реализацию IoC (Inversion of Control) контейнера
с поддержкой generics, скоупов и регистрации зависимостей.
"""

from .ioc_container import (
    Command,
    CurrentScopeCommand,
    IoC,
    IoCContainer,
    NewScopeCommand,
    RegisterCommand,
)

__all__ = [
    "Command",
    "CurrentScopeCommand",
    "IoC",
    "IoCContainer",
    "NewScopeCommand",
    "RegisterCommand",
]
