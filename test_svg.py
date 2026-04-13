#!/usr/bin/env python3
"""
测试SVG生成功能
"""

from models import ChipModel, PackageType, PinCount, PinModel, StyleManager
from utils import SvgGenerator

# 创建样式管理器
style_manager = StyleManager()

# 创建SVG生成器
svg_generator = SvgGenerator(style_manager)

# 测试双列封装
def test_two_row_package():
    print("测试双列封装...")
    chip = ChipModel(
        name="Test Chip",
        package_type=PackageType.PID,
        pin_count=16
    )
    
    # 添加引脚
    for i in range(1, 17):
        pin = PinModel(number=i)
        pin.add_function(f"P{i}", "GPIO")
        chip.pin_list.append(pin)
    
    # 生成SVG
    svg_content = svg_generator.generate(chip)
    print(f"双列封装SVG生成成功，长度: {len(svg_content)}")
    
    # 保存到文件
    with open("test_two_row.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("双列封装SVG已保存到 test_two_row.svg")

# 测试四列封装
def test_four_row_package():
    print("\n测试四列封装...")
    chip = ChipModel(
        name="Test QFN",
        package_type=PackageType.QFN,
        pin_count=32
    )
    
    # 设置四列引脚数
    chip.pin_count_detail = PinCount(
        top=8,
        right=8,
        bottom=8,
        left=8
    )
    
    # 添加引脚
    for i in range(1, 33):
        pin = PinModel(number=i)
        pin.add_function(f"P{i}", "GPIO")
        chip.pin_list.append(pin)
    
    # 生成SVG
    svg_content = svg_generator.generate(chip)
    print(f"四列封装SVG生成成功，长度: {len(svg_content)}")
    
    # 保存到文件
    with open("test_four_row.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("四列封装SVG已保存到 test_four_row.svg")

# 测试引脚隐藏和占位功能
def test_pin_visibility():
    print("\n测试引脚隐藏和占位功能...")
    chip = ChipModel(
        name="Test Visibility",
        package_type=PackageType.PID,
        pin_count=8
    )
    
    # 添加引脚
    for i in range(1, 9):
        pin = PinModel(number=i)
        pin.add_function(f"P{i}", "GPIO")
        # 隐藏偶数引脚
        if i % 2 == 0:
            pin.is_visible = False
        # 不占位奇数引脚
        if i % 2 == 1:
            pin.occupies_pin_number = False
        chip.pin_list.append(pin)
    
    # 生成SVG
    svg_content = svg_generator.generate(chip)
    print(f"引脚可见性测试SVG生成成功，长度: {len(svg_content)}")
    
    # 保存到文件
    with open("test_visibility.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("引脚可见性测试SVG已保存到 test_visibility.svg")

# 测试中心焊盘功能
def test_center_pad():
    print("\n测试中心焊盘功能...")
    chip = ChipModel(
        name="Test QFN with Center Pad",
        package_type=PackageType.QFN,
        pin_count=32
    )
    
    # 设置四列引脚数
    chip.pin_count_detail = PinCount(
        top=8,
        right=8,
        bottom=8,
        left=8
    )
    
    # 添加中心焊盘
    center_pin = PinModel(number=0)
    center_pin.add_function("GND", "GND")
    chip.pin_list.append(center_pin)
    
    # 添加其他引脚
    for i in range(1, 33):
        pin = PinModel(number=i)
        pin.add_function(f"P{i}", "GPIO")
        chip.pin_list.append(pin)
    
    # 生成SVG
    svg_content = svg_generator.generate(chip)
    print(f"中心焊盘测试SVG生成成功，长度: {len(svg_content)}")
    
    # 保存到文件
    with open("test_center_pad.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("中心焊盘测试SVG已保存到 test_center_pad.svg")

if __name__ == "__main__":
    test_two_row_package()
    test_four_row_package()
    test_pin_visibility()
    test_center_pad()
    print("\n所有测试完成！")
