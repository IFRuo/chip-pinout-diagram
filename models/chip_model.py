from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field

class PackageType(Enum):
    PID = "PID"
    SOJ = "SOJ"
    SO = "SO"
    SOP = "SOP"
    TSSOP = "TSSOP"
    QFP = "QFP"
    LQFP = "LQFP"
    QFN = "QFN"
    LCC = "LCC"

    @property
    def is_two_row(self) -> bool:
        return self in [PackageType.PID, PackageType.SOJ, PackageType.SO,
                        PackageType.SOP, PackageType.TSSOP]

    @property
    def is_four_row(self) -> bool:
        return self in [PackageType.QFP, PackageType.LQFP, PackageType.QFN,
                        PackageType.LCC]

    @property
    def has_center_pad(self) -> bool:
        return True

@dataclass
class PinCount:
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    @property
    def total(self) -> int:
        return self.left + self.top + self.right + self.bottom

@dataclass
class ChipModel:
    name: str = ""
    maker: str = ""
    package_type: PackageType = PackageType.PID
    pin_count: int = 16
    pin_count_detail: PinCount = field(default_factory=PinCount)
    has_center_pad: bool = False
    pin_list: List = field(default_factory=list)

    def __post_init__(self):
        if self.pin_count_detail is None:
            self.pin_count_detail = PinCount()
        # 根据封装类型设置是否有中心焊盘
        self.has_center_pad = self.package_type.has_center_pad

    @property
    def is_multi_row(self) -> bool:
        return self.package_type.is_four_row

    def get_display_name(self) -> str:
        return f"{self.name}-{self.package_type.value}-{self.pin_count}"

    def get_file_name(self) -> str:
        prefix = f"{self.maker}" if self.maker else ""
        if self.is_multi_row:
            detail = f"{self.pin_count_detail.left}{self.pin_count_detail.top}{self.pin_count_detail.right}{self.pin_count_detail.bottom}"
            return f"{prefix}{self.name}-{detail}-{self.package_type.value}"
        else:
            return f"{prefix}{self.name}-{self.package_type.value}-{self.pin_count}"
