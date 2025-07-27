from typing import Any


class UObject:
    def __init__(self):
        self._properties = {}

    def get_property(self, property_) -> Any:
        return self._properties.get(property_)

    def set_property(self, property_: str, value: Any) -> None:
        self._properties[property_] = value
