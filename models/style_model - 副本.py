import re
from typing import List, Optional, Dict
from dataclasses import dataclass, field

@dataclass
class GroupStyle:
    name: str = ""
    font_family: str = "Cursive"
    font_bold: bool = False
    font_italic: bool = False
    font_size: int = 16
    font_color: str = "#000000"
    border_radius: int = 3
    border_width: int = 1
    border_color: str = "#000000"
    background_color: str = "#ffffff"
    related_names: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.name:
            self.name = "Default"

    def matches_function(self, func_name: str) -> bool:
        if not func_name:
            return False
        # 精确匹配
        if func_name == self.name:
            return True
        func_name_lower = func_name.lower()
        for pattern in self.related_names:
            pattern_lower = pattern.lower()
            try:
                # 尝试作为正则表达式匹配
                if re.fullmatch(pattern_lower, func_name_lower):
                    return True
            except:
                # 如果不是有效的正则表达式，尝试精确匹配
                if pattern_lower == func_name_lower:
                    return True
        return False

    def to_gn_string(self) -> str:
        related = ",".join(self.related_names) if self.related_names else ""
        return (f"{self.name}\t:{self.font_family},{int(self.font_bold)},"
                f"{int(self.font_italic)},{self.font_size},{self.font_color},"
                f"{self.border_radius},{self.border_width},{self.border_color},"
                f"{self.background_color},{{{related}}}")

    @staticmethod
    def from_gn_string(line: str) -> Optional['GroupStyle']:
        try:
            parts = line.strip().split("\t:")
            if len(parts) != 2:
                return None
            name = parts[0].strip()
            params = parts[1].strip()

            param_parts = params.split(",")
            if len(param_parts) < 9:
                return None

            font_family = param_parts[0]
            font_bold = bool(int(param_parts[1]))
            font_italic = bool(int(param_parts[2]))
            font_size = int(param_parts[3])
            font_color = param_parts[4]
            border_radius = int(param_parts[5])
            border_width = int(param_parts[6])
            border_color = param_parts[7]
            background_color = param_parts[8]

            related_names = []
            if "{" in params and "}" in params:
                related_str = params.split("{")[1].split("}")[0]
                if related_str:
                    related_names = [n.strip() for n in related_str.split(",")]

            return GroupStyle(
                name=name,
                font_family=font_family,
                font_bold=font_bold,
                font_italic=font_italic,
                font_size=font_size,
                font_color=font_color,
                border_radius=border_radius,
                border_width=border_width,
                border_color=border_color,
                background_color=background_color,
                related_names=related_names
            )
        except Exception:
            return None

    def __repr__(self):
        return f"GroupStyle({self.name})"


class StyleManager:
    def __init__(self):
        self.styles: Dict[str, GroupStyle] = {}
        self._load_default_styles()

    def _load_default_styles(self):
        default_styles = [
            GroupStyle(
                name="GND",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#FFFFFF",
                border_radius=3,
                border_width=1,
                border_color="#000000",
                background_color="#000000",
                related_names=["GND", "AGND", "DGND", "VSS", "PGND", "V-"]
            ),
            GroupStyle(
                name="VCC",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#000000",
                border_radius=3,
                border_width=1,
                border_color="#000000",
                background_color="#FF0000",
                related_names=["VCC", "AVCC", "VDD", "V+", "5V", "3.3V", "12V", "24V", "V5", "V3", "VBAT", "VREF"]
            ),
            GroupStyle(
                name="RESET",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#000000",
                border_radius=3,
                border_width=1,
                border_color="#000000",
                background_color="#f7f700",
                related_names=["RESET"]
            ),
            GroupStyle(
                name="GPIO",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#000000",
                border_radius=3,
                border_width=1,
                border_color="#000000",
                background_color="#ffff56",
                related_names=["gpio", "P"]
            ),
            GroupStyle(
                name="PWM",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#3f3f3f",
                border_radius=3,
                border_width=1,
                border_color="#424242",
                background_color="#ead0d0",
                related_names=["PWM"]
            ),
            GroupStyle(
                name="USART",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#FFFFFF",
                border_radius=3,
                border_width=1,
                border_color="#000000",
                background_color="#4291e5",
                related_names=["TX", "RX", "UART", "CTS", "RTS"]
            ),
            GroupStyle(
                name="I2C",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#E0E0E0",
                border_radius=3,
                border_width=1,
                border_color="#424242",
                background_color="#007fff",
                related_names=["SCL", "SDA", "I2C"]
            ),
            GroupStyle(
                name="SPI",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#3f3f3f",
                border_radius=3,
                border_width=1,
                border_color="#424242",
                background_color="#007f00",
                related_names=["SCLK", "MOSI", "MISO", "SS", "CS", "SPI"]
            ),
            GroupStyle(
                name="ADC",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#000000",
                border_radius=3,
                border_width=1,
                border_color="#424242",
                background_color="#00ffff",
                related_names=["ADC"]
            ),
            GroupStyle(
                name="DAC",
                font_family="Cursive",
                font_bold=False,
                font_italic=False,
                font_size=16,
                font_color="#3f3f3f",
                border_radius=3,
                border_width=1,
                border_color="#565656",
                background_color="#ffaaaa",
                related_names=["DAC"]
            ),
        ]
        for style in default_styles:
            self.styles[style.name] = style

    def add_style(self, style: GroupStyle) -> bool:
        if style.name in self.styles:
            return False
        self.styles[style.name] = style
        return True

    def remove_style(self, name: str) -> bool:
        if name in self.styles:
            del self.styles[name]
            return True
        return False

    def get_style(self, name: str) -> Optional[GroupStyle]:
        return self.styles.get(name)

    def find_style_by_function(self, func_name: str) -> Optional[GroupStyle]:
        for style in self.styles.values():
            if style.matches_function(func_name):
                return style
        return None

    def update_style(self, style: GroupStyle) -> bool:
        if style.name not in self.styles:
            return False
        self.styles[style.name] = style
        return True

    def get_all_styles(self) -> List[GroupStyle]:
        return list(self.styles.values())

    def load_from_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue
                    style = GroupStyle.from_gn_string(line)
                    if style:
                        self.styles[style.name] = style
            return True
        except Exception:
            return False

    def save_to_file(self, file_path: str) -> bool:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("//组名:字体,加粗,斜体,字号,字体颜色,圆角半径,边框线宽,边框颜色,背景颜色,{关联引脚名1,关联引脚名2,关联引脚名3,,,}\n")
                for style in self.styles.values():
                    f.write(style.to_gn_string() + "\n")
            return True
        except Exception:
            return False
