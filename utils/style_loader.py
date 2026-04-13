from models.style_model import GroupStyle, StyleManager
import os

class StyleLoader:
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager

    def load_from_file(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False
        return self.style_manager.load_from_file(file_path)

    def save_to_file(self, file_path: str) -> bool:
        return self.style_manager.save_to_file(file_path)

    def get_default_preset_path(self) -> str:
        return os.path.join("preset", "Groupingstyle.gn")

    def load_default_preset(self) -> bool:
        default_path = self.get_default_preset_path()
        if os.path.exists(default_path):
            return self.load_from_file(default_path)
        return False

    def save_default_preset(self) -> bool:
        default_path = self.get_default_preset_path()
        return self.save_to_file(default_path)
