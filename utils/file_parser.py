import re
from typing import List, Optional, Tuple
from models.chip_model import ChipModel, PackageType, PinCount
from models.pin_model import PinModel, PinFunction
from models.style_model import StyleManager

class FileParser:
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager

    def parse_chip_file(self, file_path: str, current_chip: Optional['ChipModel'] = None, include_styles: bool = True) -> Optional[ChipModel]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_chip_content(content, current_chip, include_styles)
        except FileNotFoundError:
            print(f"文件不存在: {file_path}")
            return None
        except UnicodeDecodeError:
            print(f"文件编码错误: {file_path}")
            return None
        except Exception as e:
            print(f"解析文件时出错: {str(e)}")
            return None

    def parse_chip_content(self, content: str, current_chip: Optional['ChipModel'] = None, include_styles: bool = True) -> Optional[ChipModel]:
        lines = content.strip().split('\n')
        if not lines:
            return None

        # 检查是否为新格式的标准芯片引脚文件
        if lines[0].strip() == '[Chip pin function]':
            return self._parse_new_standard_file(lines, current_chip, include_styles)
        else:
            # 尝试解析旧格式
            header = lines[0].strip()
            chip_model = self._parse_header(header)
            if not chip_model:
                chip_model = self._parse_simple_header(header, current_chip)
            if not chip_model:
                return None

            style_lines = []
            pin_lines = []

            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('*'):
                    line = line.lstrip('*').strip()
                if not line:
                    continue
                if '\t:' in line:
                    style_lines.append(line)
                elif ':' in line:
                    pin_lines.append(line)

            # 解析并应用功能组样式信息
            if include_styles:
                for style_line in style_lines:
                    style = self._parse_style_line(style_line)
                    if style:
                        # 如果样式已存在，更新它；否则添加它
                        self.style_manager.update_style(style)

            pin_index = 1
            for pin_line in pin_lines:
                # 对于旧格式文件，直接使用简易引脚行解析方法，因为它会正确处理"/"分隔符
                pin = self._parse_simple_pin_line(pin_line, pin_index)
                if pin:
                    chip_model.pin_list.append(pin)
                    pin_index += 1

            # 确保引脚列表中默认有pin0
        has_pin0 = any(pin.number == 0 for pin in chip_model.pin_list)
        if not has_pin0:
            # 如果文件中没有中心焊盘pin0，添加一个隐藏的pin0
            pin0 = PinModel(number=0, is_visible=False, occupies_pin_number=True)
            # 添加一个标记，确保__post_init__方法不会覆盖我们设置的is_visible属性
            pin0._is_visible_set = True
            # 添加默认的nc功能
            pin0.add_function("nc")
            chip_model.pin_list.insert(0, pin0)

            # 根据引脚数量设置pin_count_detail
            if chip_model.package_type.is_four_row:
                total_pins = len(chip_model.pin_list)
                # 计算每边的引脚数
                pins_per_side = total_pins // 4
                # 处理余数
                remainder = total_pins % 4
                
                chip_model.pin_count_detail = PinCount(
                    left=pins_per_side + (1 if remainder > 0 else 0),
                    bottom=pins_per_side + (1 if remainder > 1 else 0),
                    right=pins_per_side + (1 if remainder > 2 else 0),
                    top=pins_per_side
                )
            else:
                chip_model.pin_count = len(chip_model.pin_list)

            return chip_model
    
    def _parse_new_standard_file(self, lines: List[str], current_chip: Optional['ChipModel'] = None, include_styles: bool = True) -> Optional[ChipModel]:
        """解析新格式的标准芯片引脚文件"""
        if len(lines) < 4:
            return None

        # 解析厂商名
        maker_line = lines[1].strip()
        if not maker_line.startswith('[') or not maker_line.endswith(']'):
            return None
        maker = maker_line[1:-1].strip()

        # 解析芯片型号
        chip_name_line = lines[2].strip()
        if not chip_name_line.startswith('[') or not chip_name_line.endswith(']'):
            return None
        chip_name = chip_name_line[1:-1].strip()

        # 解析封装形式和引脚数
        package_line = lines[3].strip()
        if not package_line.startswith('[') or not package_line.endswith(']'):
            return None
        package_info = package_line[1:-1].strip()
        
        # 解析封装类型和引脚数
        package_type, pin_count, pin_count_detail = self._parse_package_info(package_info)
        if not package_type:
            return None

        # 创建芯片模型
        chip_model = ChipModel(
            name=chip_name,
            maker=maker,
            package_type=package_type,
            pin_count=pin_count
        )
        if package_type.is_four_row and pin_count_detail:
            chip_model.pin_count_detail = pin_count_detail

        # 解析功能组样式和引脚信息
        style_lines = []
        pin_lines = []
        in_pin_section = False

        for line in lines[4:]:
            line = line.strip()
            if not line:
                continue
            if line.startswith('*'):
                line = line.lstrip('*').strip()
            if not line:
                continue
            
            # 检查是否开始引脚描述部分
            if not in_pin_section and ':' in line and not '\t:' in line:
                # 检查是否是引脚行
                parts = line.split(':', 1)
                try:
                    # 尝试解析引脚号
                    pin_num = int(parts[0].strip())
                    in_pin_section = True
                    pin_lines.append(line)
                except:
                    # 不是引脚行，继续解析样式
                    style_lines.append(line)
            elif '\t:' in line:
                style_lines.append(line)
            else:
                pin_lines.append(line)

        # 解析并应用功能组样式信息
        if include_styles:
            # 先清空styles字典，确保按照文件中的顺序加载样式
            self.style_manager.styles.clear()
            for style_line in style_lines:
                style = self._parse_style_line(style_line)
                if style:
                    # 直接添加样式，确保按照文件中的顺序
                    self.style_manager.styles[style.name] = style

        # 解析引脚信息
        for pin_line in pin_lines:
            pin = self._parse_pin_line(pin_line, 1)
            if pin:
                chip_model.pin_list.append(pin)

        # 确保引脚列表中默认有pin0
        has_pin0 = any(pin.number == 0 for pin in chip_model.pin_list)
        if not has_pin0:
            # 如果文件中没有中心焊盘pin0，添加一个隐藏的pin0
            pin0 = PinModel(number=0, is_visible=False, occupies_pin_number=True)
            # 添加一个标记，确保__post_init__方法不会覆盖我们设置的is_visible属性
            pin0._is_visible_set = True
            # 添加默认的nc功能
            pin0.add_function("nc")
            chip_model.pin_list.insert(0, pin0)

        return chip_model
    
    def _parse_package_info(self, package_info: str) -> Tuple[Optional[PackageType], int, Optional[PinCount]]:
        """解析封装信息"""
        import re
        match = re.match(r'([A-Z]+)\((\d+)(?:,(\d+),(\d+),(\d+),(\d+))?\)', package_info)
        if not match:
            return None, 0, None

        package_name = match.group(1).upper()
        total_pins = int(match.group(2))

        # 确定封装类型
        try:
            package_type = PackageType[package_name] if package_name in [e.name for e in PackageType] else PackageType.PID
        except:
            package_type = PackageType.PID

        # 解析四排封装的引脚分布
        pin_count_detail = None
        if package_type.is_four_row and match.group(3) and match.group(4) and match.group(5) and match.group(6):
            left = int(match.group(3))
            bottom = int(match.group(4))
            right = int(match.group(5))
            top = int(match.group(6))
            pin_count_detail = PinCount(left=left, bottom=bottom, right=right, top=top)

        return package_type, total_pins, pin_count_detail

    def _parse_header(self, header: str) -> Optional[ChipModel]:
        match = re.match(r'/\*(.+)-(\w+)-(\d+)\*/', header)
        if match:
            name = match.group(1).strip()
            package = match.group(2).strip().upper()
            pin_count = int(match.group(3))

            try:
                package_type = PackageType[package] if package in [e.name for e in PackageType] else PackageType.PID
            except:
                package_type = PackageType.PID

            model = ChipModel(
                name=name,
                package_type=package_type,
                pin_count=pin_count
            )
            return model
        return None

    def _parse_style_line(self, line: str) -> Optional:
        from models.style_model import GroupStyle
        return GroupStyle.from_gn_string(line)

    def _parse_pin_line(self, line: str, default_index: int) -> Optional[PinModel]:
        line = line.strip()
        if line.startswith('[') and ']' in line:
            parts = line.split(']', 1)
            pin_num_str = parts[0][1:].strip()
            try:
                pin_num = int(pin_num_str)
            except:
                pin_num = default_index
            content = parts[1].strip() if len(parts) > 1 else ""
        elif ':' in line:
            parts = line.split(':', 1)
            try:
                pin_num = int(parts[0].strip())
            except:
                pin_num = default_index
            content = parts[1].strip()
        else:
            return None

        pin = PinModel(number=pin_num)

        content = content.strip()
        if not content:
            return pin

        func_strs = self._split_functions(content)
        for i, func_str in enumerate(func_strs):
            # 检查是否是最后一个元素，并且是复选框状态
            if i == len(func_strs) - 1 and func_str.startswith('(') and func_str.endswith(')'):
                state_str = func_str[1:-1].strip()
                state_parts = state_str.split(',')
                if len(state_parts) == 2:
                    try:
                        # 解析可见性和是否占用引脚号
                        pin.is_visible = bool(int(state_parts[0].strip()))
                        pin.occupies_pin_number = bool(int(state_parts[1].strip()))
                    except:
                        pass
            else:
                # 解析功能
                func = self._parse_function(func_str)
                if func:
                    pin.functions.append(func)

        return pin

    def _split_functions(self, content: str) -> List[str]:
        result = []
        current = []
        in_brackets = False
        in_parentheses = False
        i = 0
        while i < len(content):
            char = content[i]
            if char == '[':
                in_brackets = True
                current.append(char)
            elif char == ']':
                in_brackets = False
                current.append(char)
            elif char == '(':
                in_parentheses = True
                current.append(char)
            elif char == ')':
                in_parentheses = False
                current.append(char)
            elif char == ',' and not in_brackets and not in_parentheses:
                if current:
                    result.append(''.join(current).strip())
                    current = []
            else:
                current.append(char)
            i += 1
        if current:
            result.append(''.join(current).strip())
        return result

    def _parse_function(self, func_str: str) -> Optional[PinFunction]:
        func_str = func_str.strip()
        if not func_str or func_str == '[]':
            return None

        if func_str.startswith('[') and func_str.endswith(']'):
            func_str = func_str[1:-1]

        if ',' in func_str:
            parts = func_str.rsplit(',', 1)
            name = parts[0].strip()
            group = parts[1].strip()
        else:
            name = func_str
            group = ""

        if not name:
            return None

        if not group:
            matched_style = self.style_manager.find_style_by_function(name)
            if matched_style:
                group = matched_style.name

        return PinFunction(name=name, group_name=group)

    def parse_simple_file(self, file_path: str, current_chip: Optional['ChipModel'] = None) -> Optional[ChipModel]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.parse_simple_content(content, current_chip)
        except Exception:
            return None

    def parse_simple_content(self, content: str, current_chip: Optional['ChipModel'] = None) -> Optional[ChipModel]:
        lines = content.strip().split('\n')
        if not lines:
            return None

        header = lines[0].strip()
        chip_model = self._parse_simple_header(header, current_chip)
        if not chip_model:
            return None

        pin_index = 1
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            pin = self._parse_simple_pin_line(line, pin_index)
            if pin:
                chip_model.pin_list.append(pin)
                pin_index += 1

        chip_model.pin_count = len(chip_model.pin_list)
        return chip_model

    def _parse_simple_header(self, header: str, current_chip: Optional['ChipModel'] = None) -> Optional[ChipModel]:
        header = header.strip()
        header = header.strip('/*').strip('*/').strip()

        name = header
        package = None
        pin_count = 0

        parts = header.split('-')
        if len(parts) >= 1:
            name = parts[0].strip()
        if len(parts) >= 2:
            package = parts[1].strip()
        if len(parts) >= 3:
            try:
                pin_count = int(parts[2].strip())
            except:
                pin_count = 0

        # 确定封装形式
        if package:
            # 文件中有封装形式，使用文件中的
            try:
                package_upper = package.upper()
                if package_upper in [e.name for e in PackageType]:
                    package_type = PackageType[package_upper]
                elif package_upper in [e.value for e in PackageType]:
                    package_type = PackageType(package_upper)
                else:
                    # 如果文件中的封装形式无效，使用当前的
                    package_type = current_chip.package_type if current_chip else PackageType.PID
            except:
                # 如果解析失败，使用当前的
                package_type = current_chip.package_type if current_chip else PackageType.PID
        else:
            # 文件中没有封装形式，使用当前的
            package_type = current_chip.package_type if current_chip else PackageType.PID

        # 分离芯片名称中的厂商部分和型号部分
        # 厂商部分是开头的连续字母（包括小写字母和大写字母）
        maker = ""
        chip_name = name
        
        # 找到第一个非字母字符的位置
        import re
        match = re.match(r'^([a-zA-Z]+)(.*)$', name)
        if match:
            maker = match.group(1)
            chip_name = match.group(2).lstrip()
        
        model = ChipModel(
            name=chip_name,
            maker=maker,
            package_type=package_type,
            pin_count=pin_count
        )
        return model

    def _parse_simple_pin_line(self, line: str, default_index: int) -> Optional[PinModel]:
        line = line.strip()
        if not line:
            return None

        if ':' in line:
            parts = line.split(':', 1)
            try:
                pin_num = int(parts[0].strip())
            except:
                pin_num = default_index
            content = parts[1].strip()
        else:
            pin_num = default_index
            content = line

        pin = PinModel(number=pin_num)

        # 检查是否包含复选框状态
        if '(' in content and ')' in content:
            # 分离功能和状态
            last_bracket_index = content.rfind('(')
            func_part = content[:last_bracket_index].strip()
            state_part = content[last_bracket_index:].strip()
            
            # 解析功能
            if func_part:
                func_names = func_part.split('/')
                for name in func_names:
                    name = name.strip()
                    if name:
                        group = ""
                        matched_style = self.style_manager.find_style_by_function(name)
                        if matched_style:
                            group = matched_style.name
                        pin.add_function(name, group)
            
            # 解析复选框状态
            if state_part.startswith('(') and state_part.endswith(')'):
                state_str = state_part[1:-1].strip()
                state_parts = state_str.split(',')
                if len(state_parts) == 2:
                    try:
                        pin.is_visible = bool(int(state_parts[0].strip()))
                        pin.occupies_pin_number = bool(int(state_parts[1].strip()))
                    except:
                        pass
        else:
            # 没有复选框状态，只解析功能
            func_names = content.split('/')
            for name in func_names:
                name = name.strip()
                if name:
                    group = ""
                    matched_style = self.style_manager.find_style_by_function(name)
                    if matched_style:
                        group = matched_style.name
                    pin.add_function(name, group)

        return pin

    def generate_chip_file_content(self, chip: ChipModel, include_styles: bool = True) -> str:
        lines = []
        # 第一行：标准芯片引脚文件标识
        lines.append('[Chip pin function]')
        # 第二行：厂商名
        lines.append(f'[{chip.maker}]')
        # 第三行：芯片型号
        lines.append(f'[{chip.name}]')
        # 第四行：封装形式和引脚数
        if chip.package_type.is_four_row and chip.pin_count_detail:
            package_line = f"[{chip.package_type.name}({chip.pin_count},{chip.pin_count_detail.left},{chip.pin_count_detail.bottom},{chip.pin_count_detail.right},{chip.pin_count_detail.top})]"
        else:
            package_line = f"[{chip.package_type.name}({chip.pin_count})]"
        lines.append(package_line)
        lines.append("")

        # 功能组样式信息
        if include_styles:
            for style in self.style_manager.get_all_styles():
                lines.append(style.to_gn_string())
            lines.append("")

        # 引脚描述
        for pin in chip.pin_list:
            pin_line = self._generate_pin_line(pin)
            lines.append(pin_line)

        return '\n'.join(lines)

    def _generate_pin_line(self, pin: PinModel) -> str:
        pin_str = f"{pin.number:02d}:"
        funcs = []
        for func in pin.functions:
            if func.group_name:
                funcs.append(f"[{func.name},{func.group_name}]")
            else:
                funcs.append(f"[{func.name}]")
        pin_str += ','.join(funcs)
        # 添加复选框状态：可见性和是否占用引脚号
        pin_str += f",({int(pin.is_visible)},{int(pin.occupies_pin_number)})"
        return pin_str
