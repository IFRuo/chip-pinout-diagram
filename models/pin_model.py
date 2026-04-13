from typing import Optional, List
from dataclasses import dataclass, field

@dataclass
class PinFunction:
    name: str = ""
    group_name: str = ""

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"PinFunction({self.name}, {self.group_name})"

@dataclass
class PinModel:
    number: int = 0
    functions: List[PinFunction] = field(default_factory=list)
    is_visible: bool = True
    occupies_pin_number: bool = True

    def __post_init__(self):
        if self.number == 0 and not hasattr(self, '_is_visible_set'):
            self.is_visible = True
            self.occupies_pin_number = True

    @property
    def is_center_pad(self) -> bool:
        return self.number == 0

    def add_function(self, name: str, group_name: str = "") -> PinFunction:
        func = PinFunction(name=name, group_name=group_name)
        self.functions.append(func)
        return func

    def remove_function(self, index: int) -> bool:
        if 0 <= index < len(self.functions):
            self.functions.pop(index)
            return True
        return False

    def get_first_function_name(self) -> str:
        if self.functions:
            return self.functions[0].name
        return ""

    def __repr__(self):
        return f"PinModel({self.number}, {len(self.functions)} functions)"
