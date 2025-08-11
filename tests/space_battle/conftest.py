from unittest.mock import Mock

import pytest

from homeworks.space_battle.interfaces import CommandInterface


@pytest.fixture
def command() -> CommandInterface:
    return Mock(spec=CommandInterface)
