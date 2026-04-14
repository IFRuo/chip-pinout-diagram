from typing import List, Dict, Optional, Tuple
from models.chip_model import ChipModel, PackageType, PinCount
from models.pin_model import PinModel
from models.style_model import StyleManager, GroupStyle
from .config_manager import ConfigManager
from PIL import ImageFont

class SvgGenerator:
    def __init__(self, style_manager: StyleManager):
        self.style_manager = style_manager
        self.config_manager = ConfigManager()
        
        # SVG画布设置
        #画布颜色
        self._svg_bg_color = self.config_manager.get('画板.画板背景色', "#555555")
        self._svg_width = self.config_manager.get('画板.画板宽度', 640) * 1#画布宽度1.2
        self._svg_height = self.config_manager.get('画板.画板高度', 480) * 1#画布高度 1.2
        
        # 引脚参数
        self._pin_rect_width = 20  # 引脚宽度
        self._pin_rect_height = 10  # 引脚高度
        self._pin_spacing = None  # 引脚间距（根据引脚数量动态计算）

        self.QFN_pin2labelspacing = self.config_manager.get('焊盘.QFN焊盘.QFN引脚与标签间距', 10)  # 引脚与标签的间距
        self.QFN_label2labelspacing = self.config_manager.get('焊盘.QFN焊盘.QFN标签间距', 5)  # 标签与标签的间距
        
        # 芯片主体参数
        self._chip_corner_radius = self.config_manager.get('芯片主体参数.芯片主体圆角半径', 10)  # 芯片主体圆角半径
        self._chip_stroke_width = self.config_manager.get('芯片主体参数.芯片主体边框宽度', 5)  # 芯片主体边框宽度
        
        # 标签参数
        self._label_height = self.config_manager.get('标签参数.标签高度', 15)  # 标签高度
        #self._label_spacing = self.config_manager.get('标签参数.标签间距', 5)  # 标签间距
        
        # 文本参数
        self._pin_number_font_size = 8  # 引脚编号字体大小
        self._pin_number_font_family = "Cursive"  # 引脚编号字体
        self._function_font_size = 16  # 功能标签字体大小
        self._function_font_family = "Cursive"  # 功能标签字体
        self._chip_title_font_size = self.config_manager.get('芯片主体参数.芯片标题字体大小', 22)  # 芯片标题字体大小
        self._chip_title_font_family = self.config_manager.get('芯片主体参数.芯片标题字体', "Fantasy")  # 芯片标题字体
        self._chip_name_font_size = self.config_manager.get('芯片主体参数.芯片名称字体大小', 22)  # 芯片名称字体大小
        self._chip_name_font_family = self.config_manager.get('芯片主体参数.芯片名称字体', "Fantasy")  # 芯片名称字体
        self._chip_info_font_size = self.config_manager.get('芯片主体参数.芯片信息字体大小', 12)  # 芯片信息字体大小
        self._chip_info_font_family = self.config_manager.get('芯片主体参数.芯片信息字体', "Cursive")  # 芯片信息字体
        
        
        # 图例参数
        self._legend_x = self.config_manager.get('图例参数.图例起始X坐标', 20)  # 图例起始X坐标
        self._legend_y = self.config_manager.get('图例参数.图例起始Y坐标', 20)  # 图例起始Y坐标
        self._legend_item_height = self.config_manager.get('图例参数.图例项高度', 20)  # 图例项高度
        self._legend_item_width = self.config_manager.get('图例参数.图例项宽度', 100)  # 图例项宽度
        self._legend_font_size = self.config_manager.get('图例参数.图例字体大小', 14)  # 图例字体大小
        #self._legend_font_family = "Cursive"  # 图例字体
        self._legend_items_per_column = self.config_manager.get('图例参数.每列图例项数量', 10)  # 每列显示的图例项数量
        self._legend_column_spacing = self.config_manager.get('图例参数.图例列间距', 4)  # 图例列间距
        
        # 文本宽度缓存
        self._text_width_cache = {}
    
    def _get_package_config_prefix(self, package_type: str) -> str:
        """根据封装类型获取配置前缀"""
        # 封装类型映射
        package_map = {
            # PID系列
            "PID": "PID",
            "SO": "PID",
            "SOJ": "PID",
            "SOP": "PID",
            "TSSOP": "PID",
            # QFP系列
            "QFP": "QFP",
            "LQFP": "QFP",
            # QFN系列
            "QFN": "QFN",
            "LCC": "QFN"
        }
        return package_map.get(package_type, "PID")
    
    def _calculate_body_size_two_row(self, half_pins: int, pin_rect_height: int) -> tuple:
        """计算双列封装的芯片主体大小
        
        Args:
            half_pins: 每边的引脚数量
            pin_rect_height: 引脚高度
            
        Returns:
            tuple: (body_width, body_height, body_left, body_right, body_top, body_bottom, pin_spacing)
        """
        # 有引脚的边的长度
        pin_side_length = ((half_pins + 2) * 2 - 1) * pin_rect_height
        # 无引脚的边的长度 = 有引脚边边长/2 + 30
        no_pin_side_length = pin_side_length // 2 + 30
        
        center_x = self._svg_width // 2
        center_y = self._svg_height // 2
        body_left = center_x - no_pin_side_length // 2
        body_right = center_x + no_pin_side_length // 2
        body_top = center_y - pin_side_length // 2
        body_bottom = center_y + pin_side_length // 2
        
        pin_spacing = (body_bottom - body_top) / (half_pins + 1)
        
        return (no_pin_side_length, pin_side_length, body_left, body_right, body_top, body_bottom, pin_spacing)
    
    def _calculate_body_size_four_row(self, detail: PinCount, pin_rect_height: int) -> tuple:
        """计算四列封装的芯片主体大小
        
        Args:
            detail: 四边的引脚数量
            pin_rect_height: 引脚高度
            
        Returns:
            tuple: (body_width, body_height, body_left, body_top, body_right, body_bottom, top_spacing, right_spacing, bottom_spacing, left_spacing)
        """
        # 分别计算芯片宽度和高度
        # 芯片宽度：比较上下两条边的焊盘数，取多的一边
        max_width_pins = max(detail.top, detail.bottom)
        # 芯片高度：比较左右两条边的焊盘数，取多的一边
        max_height_pins = max(detail.left, detail.right)
        
        # 计算宽度和高度
        # 宽度长度 = ((上下边最大引脚数量 + 2) * 2 - 1) * 引脚高度
        body_width = ((max_width_pins + 2) * 2 ) * pin_rect_height
        # 高度长度 = ((左右边最大引脚数量 + 2) * 2 - 1) * 引脚高度
        body_height = ((max_height_pins + 2) * 2) * pin_rect_height
        
        center_x = self._svg_width // 2
        center_y = self._svg_height // 2
        body_left = center_x - body_width // 2
        body_top = center_y - body_height // 2
        body_right = center_x + body_width // 2
        body_bottom = center_y + body_height // 2

        # 计算各边引脚间距
        top_spacing = body_width / (detail.top + 1) if detail.top > 0 else 0
        right_spacing = body_height / (detail.right + 1) if detail.right > 0 else 0
        bottom_spacing = body_width / (detail.bottom + 1) if detail.bottom > 0 else 0
        left_spacing = body_height / (detail.left + 1) if detail.left > 0 else 0
        
        return (body_width, body_height, body_left, body_top, body_right, body_bottom, top_spacing, right_spacing, bottom_spacing, left_spacing)
    
    def set_canvas_size(self, width: int, height: int):
        """设置画布大小"""
        self._svg_width = width * 1.2  # 保持与初始化时相同的缩放比例
        self._svg_height = height * 1.2

    def _calculate_text_width(self, text: str, font_family: str, font_size: int) -> float:
        """计算文本宽度
        
        Args:
            text: 要计算宽度的文本
            font_family: 字体家族
            font_size: 字体大小
            
        Returns:
            文本的宽度
        """
        # 生成缓存键，用于缓存文本宽度计算结果
        cache_key = (text, font_family, font_size)
        
        # 检查缓存，如果已存在则直接返回
        if cache_key in self._text_width_cache:
            return self._text_width_cache[cache_key]
        
        try:
            # 尝试加载字体并计算实际宽度
            font = ImageFont.truetype(font_family, font_size)
            # 使用getlength方法获取文本宽度
            width = font.getlength(text)
        except Exception:
            # 如果加载字体失败，使用默认的估算方法
            # 0.6是一个调整因子，因为字体宽度通常小于字体大小
            width = len(text) * font_size * 0.6
        
        # 将计算结果存入缓存
        self._text_width_cache[cache_key] = width
        return width

    def calculate_chip_bounds(self, chip: ChipModel) -> Tuple[float, float]:
        """计算芯片图内容大小（不包含图例）"""
        # 初始化边界值 - 使用芯片主体的边界作为初始值
        if chip.package_type.is_four_row and chip.pin_count_detail:
            # 四排封装
            max_pins = max(chip.pin_count_detail.left, chip.pin_count_detail.top, 
                          chip.pin_count_detail.right, chip.pin_count_detail.bottom)
            side_length = ((max_pins + 2) * 2 - 1) * self._pin_rect_height
            center_x = self._svg_width // 2
            center_y = self._svg_height // 2
            body_left = center_x - side_length // 2
            body_top = center_y - side_length // 2
            body_right = center_x + side_length // 2
            body_bottom = center_y + side_length // 2
        else:
            # 两排封装
            half_pins = chip.pin_count // 2
            pin_side_length = ((half_pins + 2) * 2 - 1) * self._pin_rect_height
            no_pin_side_length = pin_side_length // 2 + 30
            center_x = self._svg_width // 2
            center_y = self._svg_height // 2
            body_left = center_x - no_pin_side_length // 2
            body_top = center_y - pin_side_length // 2
            body_right = center_x + no_pin_side_length // 2
            body_bottom = center_y + pin_side_length // 2
        
        # 初始化边界值
        min_x = body_left  # 最左侧x坐标
        max_x = body_right  # 最右侧x坐标
        min_y = body_top  # 最上方y坐标
        max_y = body_bottom  # 最下方y坐标
        
        # 计算标签边界
        if chip.package_type.is_four_row and chip.pin_count_detail:
            # 获取封装类型配置前缀
            package_prefix = self._get_package_config_prefix(chip.package_type.value)
            # 读取焊盘配置以获取标签间距
            pad_config = self.config_manager.get(f'焊盘.{package_prefix}焊盘', {})
            label_spacing = pad_config.get(f'{package_prefix}标签间距', 10)
            
            # 四排封装标签边界
            # 左侧标签 x_posx
            left_spacing = (body_bottom - body_top) / (chip.pin_count_detail.left + 1) if chip.pin_count_detail.left > 0 else 0
            for i in range(chip.pin_count_detail.left):
                y_pos = body_top + left_spacing * (i + 1)
                pin = self._get_pin_by_number(chip, i + 1)
                if pin and pin.is_visible:
                    label_x = body_left
                    for func in pin.functions:
                        style = self.style_manager.get_style(func.group_name)
                        if style:
                            # 计算标签宽度
                            font_size = style.font_size
                            width = self._calculate_text_width(func.name, style.font_family, font_size) + 10 + label_spacing
                            # 左侧标签起始位置 = 焊盘x - 标签宽度
                            label_x = label_x - width
                            # 更新最左侧x坐标
                            min_x = min(min_x, label_x)
            
            # 右侧标签
            right_spacing = (body_bottom - body_top) / (chip.pin_count_detail.right + 1) if chip.pin_count_detail.right > 0 else 0
            current_pin = chip.pin_count_detail.left + chip.pin_count_detail.bottom + 1
            for i in range(chip.pin_count_detail.right):
                y_pos = body_bottom - right_spacing * (i + 1)
                pin = self._get_pin_by_number(chip, current_pin)
                if pin and pin.is_visible:
                    label_x = body_right + self._pin_rect_width
                    for func in pin.functions:
                        style = self.style_manager.get_style(func.group_name)
                        if style:
                            # 计算标签宽度
                            font_size = style.font_size
                            width = self._calculate_text_width(func.name, style.font_family, font_size) + 10 + label_spacing
                            # 右侧标签起始位置 = 焊盘x + 焊盘宽度
                            label_x = label_x + width
                            # 更新最右侧x坐标
                            max_x = max(max_x, label_x)
                current_pin += 1
            
            # 顶部标签
            top_spacing = (body_right - body_left) / (chip.pin_count_detail.top + 1) if chip.pin_count_detail.top > 0 else 0
            current_pin = chip.pin_count_detail.left + chip.pin_count_detail.bottom + chip.pin_count_detail.right + 1
            for i in range(chip.pin_count_detail.top):
                x_pos = body_right - top_spacing * (i + 1)
                pin = self._get_pin_by_number(chip, current_pin)
                if pin and pin.is_visible:
                    label_y = body_top - self._pin_rect_width
                    for func in pin.functions:
                        style = self.style_manager.get_style(func.group_name)
                        if style:
                            # 计算标签宽度（旋转后标签的宽度是垂直方向的长度）
                            font_size = style.font_size
                            width = self._calculate_text_width(func.name, style.font_family, font_size) + 10 + label_spacing
                            # 上侧标签起始位置 = 焊盘y - 焊盘宽度 - 标签宽度
                            label_y = label_y - width
                            # 更新最上方y坐标
                            min_y = min(min_y, label_y)
                current_pin += 1
            
            # 底部标签
            bottom_spacing = (body_right - body_left) / (chip.pin_count_detail.bottom + 1) if chip.pin_count_detail.bottom > 0 else 0
            current_pin = chip.pin_count_detail.left + 1
            for i in range(chip.pin_count_detail.bottom):
                x_pos = body_left + bottom_spacing * (i + 1)
                pin = self._get_pin_by_number(chip, current_pin)
                if pin and pin.is_visible:
                    label_y = body_bottom
                    for func in pin.functions:
                        style = self.style_manager.get_style(func.group_name)
                        if style:
                            # 计算标签宽度（旋转后标签的宽度是垂直方向的长度）
                            font_size = style.font_size
                            width = self._calculate_text_width(func.name, style.font_family, font_size) + 10 + label_spacing
                            # 下侧标签起始位置 = 焊盘y + 标签宽度
                            label_y = label_y + width
                            # 更新最下方y坐标
                            max_y = max(max_y, label_y)
                current_pin += 1
        else:
            # 两排封装标签边界
            # 获取封装类型配置前缀
            package_prefix = self._get_package_config_prefix(chip.package_type.value)
            # 读取焊盘配置以获取标签间距
            pad_config = self.config_manager.get(f'焊盘.{package_prefix}焊盘', {})
            label_spacing = pad_config.get(f'{package_prefix}标签间距', 10)
            
            half_pins = chip.pin_count // 2
            pin_spacing = (body_bottom - body_top) / (half_pins + 1)
            
            # 左侧标签
            for i in range(half_pins):
                y_pos = body_top + pin_spacing * (i + 1)
                pin = self._get_pin_by_number(chip, i + 1)
                if pin and pin.is_visible:
                    label_x = body_left + self._pin_rect_width
                    for func in pin.functions:
                        style = self.style_manager.get_style(func.group_name)
                        if style:
                            # 计算标签宽度
                            font_size = style.font_size
                            width = self._calculate_text_width(func.name, style.font_family, font_size) + 0 + label_spacing
                            # 左侧标签起始位置 = 焊盘x - 标签宽度
                            label_x = label_x - width
                            # 更新最左侧x坐标
                            min_x = min(min_x, label_x)
            
            # 右侧标签
            for i in range(half_pins):
                y_pos = body_top + pin_spacing * (i + 1)
                pin = self._get_pin_by_number(chip, half_pins + i + 1)
                if pin and pin.is_visible:
                    label_x = body_right  + self._pin_rect_width
                    for func in pin.functions:
                        style = self.style_manager.get_style(func.group_name)
                        if style:
                            # 计算标签宽度
                            font_size = style.font_size
                            width = self._calculate_text_width(func.name, style.font_family, font_size) + 0 + label_spacing
                            # 右侧标签起始位置 = 焊盘x + 焊盘宽度 + 标签宽度
                            label_x = label_x + width
                            # 更新最右侧x坐标
                            max_x = max(max_x, label_x)
        
        # 计算最终宽度和高度
        width = max_x - min_x
        height = max_y - min_y
        
        # 确保宽度和高度为正数
        width = max(width, 0)
        height = max(height, 0)
        
        return width, height

    def generate(self, chip: ChipModel) -> str:
        # 计算芯片图的实际大小
        chip_width, chip_height = self.calculate_chip_bounds(chip)
        
        # 检查芯片图大小是否大于当前画布大小
        if chip_width > self._svg_width or chip_height > self._svg_height:
            # 计算画布原本的宽高比
            if self._svg_height > 0:
                canvas_aspect_ratio = self._svg_width / self._svg_height
            else:
                canvas_aspect_ratio = 1.777
            
            # 计算所需的最小画布大小（芯片图大小 * 1.2）
            min_required_width = chip_width * 1.2
            min_required_height = chip_height * 1.2
            
            # 根据画布原本的宽高比计算新的画布大小
            if canvas_aspect_ratio > 1:  # 画布是横屏
                # 以宽度为基准
                new_width = max(min_required_width, min_required_height * canvas_aspect_ratio)
                new_height = new_width / canvas_aspect_ratio
            else:  # 画布是竖屏
                # 以高度为基准
                new_height = max(min_required_height, min_required_width / canvas_aspect_ratio)
                new_width = new_height * canvas_aspect_ratio
            
            # 更新画布大小
            self._svg_width = new_width
            self._svg_height = new_height
        
        if chip.package_type == PackageType.PID or chip.package_type.is_two_row:
            return self._generate_two_row_package(chip)
        else:
            return self._generate_four_row_package(chip)

    def _generate_two_row_package(self, chip: ChipModel) -> str:
        pin_count = chip.pin_count
        half_pins = pin_count // 2

        svg_parts = []
        svg_parts.append(f'<svg width="{self._svg_width}" height="{self._svg_height}" xmlns="http://www.w3.org/2000/svg">')
        # 添加背景矩形
        svg_parts.append(f'<rect width="{self._svg_width}" height="{self._svg_height}" fill="{self._svg_bg_color}" />')

        svg_parts.append(self._generate_defs())

        svg_parts.append(self._generate_chip_body_two_row(chip, half_pins))

        svg_parts.append(self._generate_pins_two_row(chip, half_pins))

        svg_parts.append(self._generate_labels_two_row(chip, half_pins))

        svg_parts.append(self._generate_style_legend())

        svg_parts.append(self._generate_chip_title(chip))

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _generate_four_row_package(self, chip: ChipModel) -> str:
        detail = chip.pin_count_detail
        svg_parts = []
        svg_parts.append(f'<svg width="{self._svg_width}" height="{self._svg_height}" xmlns="http://www.w3.org/2000/svg">')
        # 添加背景矩形
        svg_parts.append(f'<rect width="{self._svg_width}" height="{self._svg_height}" fill="{self._svg_bg_color}" />')

        svg_parts.append(self._generate_defs())

        svg_parts.append(self._generate_chip_body_four_row(chip, detail))

        svg_parts.append(self._generate_pins_four_row(chip, detail))

        svg_parts.append(self._generate_labels_four_row(chip, detail))

        svg_parts.append(self._generate_style_legend())

        svg_parts.append(self._generate_chip_title(chip))

        svg_parts.append('</svg>')
        return '\n'.join(svg_parts)

    def _generate_defs(self) -> str:
        defs = ['<defs>']
        defs.append('  <marker id="pin_marker" markerHeight="5" markerUnits="strokeWidth" markerWidth="5" orient="auto" refX="50" refY="50" viewBox="0 0 100 100">')
        defs.append('    <circle cx="50" cy="50" fill="#000000" r="30" stroke="#000000" stroke-width="10"/>')
        defs.append('  </marker>')
        defs.append('</defs>')
        return '\n'.join(defs)

    def _generate_chip_body_two_row(self, chip: ChipModel, half_pins: int) -> str:
        # 计算芯片主体大小
        body_width, body_height, _, _, body_top, body_bottom, _ = self._calculate_body_size_two_row(half_pins, self._pin_rect_height)
        center_x = self._svg_width // 2
        center_y = self._svg_height // 2
        x = center_x - body_width // 2
        y = center_y - body_height // 2

        parts = [f'<rect fill="#000000" height="{body_height}" rx="{self._chip_corner_radius}" ry="{self._chip_corner_radius}" stroke="#000000" stroke-width="{self._chip_stroke_width}" width="{body_width}" x="{x}" y="{y}"/>']
        Ox = self.config_manager.get('芯片主体参数.PIN1脚标志位置X', 15)  #1脚标志X
        Oy = self.config_manager.get('芯片主体参数.PIN1脚标志位置Y', 15)  #1脚标志Y
        Orxy = self.config_manager.get('芯片主体参数.1脚标志直径', 5) #1脚标志直径
        Ofill = self.config_manager.get('芯片主体参数.1脚标志颜色', "#000000") #1脚标志颜色
        Ostrokewidth =  self.config_manager.get('芯片主体参数.1脚标志边框直径', 1) #1脚标志边框直径
        Ostroke = self.config_manager.get('芯片主体参数.1脚标志字体直径', "#ffffff") #1脚标志边框颜色
        parts.append(f'<ellipse cx="{x + Ox}" cy="{y + Oy}" fill="{Ofill}" rx="{Orxy}" ry="{Orxy}" stroke="{Ostroke}" stroke-width= "{Ostrokewidth}"/>')
        

        if not chip.has_center_pad:
            pass

        return '\n'.join(parts)

    def _generate_chip_body_four_row(self, chip: ChipModel, detail: PinCount) -> str:
        # 计算芯片主体大小
        body_width, body_height, body_left, body_top, body_right, body_bottom, top_spacing, right_spacing, bottom_spacing, left_spacing = self._calculate_body_size_four_row(detail, self._pin_rect_height)
        center_x = self._svg_width // 2
        center_y = self._svg_height // 2
        x = center_x - body_width // 2
        y = center_y - body_height // 2

        parts = [f'<rect fill="#000000" height="{body_height}" rx="{self._chip_corner_radius}" ry="{self._chip_corner_radius}" stroke="#000000" stroke-width="{self._chip_stroke_width}" width="{body_width}" x="{x}" y="{y}"/>']
        Ox = self.config_manager.get('芯片主体参数.QFN1脚标志位置X', 15)  #1脚标志X
        Oy = self.config_manager.get('芯片主体参数.QFN1脚标志位置Y', 15)  #1脚标志Y
        Orxy = self.config_manager.get('芯片主体参数.1脚标志直径', 5) #1脚标志直径
        Ofill = self.config_manager.get('芯片主体参数.1脚标志颜色', "#000000") #1脚标志颜色
        Ostrokewidth =  self.config_manager.get('芯片主体参数.1脚标志边框直径', 1) #1脚标志边框直径
        Ostroke = self.config_manager.get('芯片主体参数.1脚标志字体直径', "#ffffff") #1脚标志边框颜色
        parts.append(f'<ellipse cx="{x + Ox}" cy="{y + Oy}" fill="{Ofill}" rx="{Orxy}" ry="{Orxy}" stroke="{Ostroke}" stroke-width= "{Ostrokewidth}"/>')
        

        # 检查是否有可见的中心焊盘
        has_visible_center_pad = False
        for pin in chip.pin_list:
            if pin.is_center_pad and pin.is_visible:
                has_visible_center_pad = True
                break
        
        if has_visible_center_pad:
            # 获取封装类型配置前缀
            package_prefix = self._get_package_config_prefix(chip.package_type.value)
            
            # 读取中心焊盘配置
            center_pad_config = self.config_manager.get(f'焊盘.{package_prefix}中心焊盘', {})
            
            # 读取焊盘配置以获取焊盘宽度
            pad_config = self.config_manager.get(f'焊盘.{package_prefix}焊盘', {})
            pin_rect_width = pad_config.get(f'{package_prefix}焊盘宽度', 20)
            
            # 计算左侧焊盘列的宽度（第一个焊盘左边缘到最后一个焊盘右边缘）
            left_center_distance = ((detail.left - 1) * left_spacing) - pin_rect_width if detail.left > 1 else 0
            # 计算上侧焊盘列的宽度（第一个焊盘左边缘到最后一个焊盘右边缘）
            top_center_distance = ((detail.top - 1) * top_spacing) - pin_rect_width if detail.top > 1 else 0
            
            # 中心焊盘参数
            center_pad_width_str = center_pad_config.get(f'{package_prefix}_中心焊盘宽度', '100%')
            center_pad_height_str = center_pad_config.get(f'{package_prefix}_中心焊盘高度', '100%')
            center_pad_radius = center_pad_config.get(f'{package_prefix}_中心焊盘圆角', 2)
            center_pad_color = center_pad_config.get(f'{package_prefix}_中心焊焊盘颜色', '#cccccc')
            center_pad_stroke_color = center_pad_config.get(f'{package_prefix}_中心焊边线颜色', '#ffffff')
            center_pad_stroke_width = center_pad_config.get(f'{package_prefix}_中心焊边线宽度', 0)
            center_pad_x_offset = center_pad_config.get(f'{package_prefix}_中心焊盘X偏移', 0)
            center_pad_y_offset = center_pad_config.get(f'{package_prefix}_中心焊盘Y偏移', 0)
            
            # 解析百分比值
            if isinstance(center_pad_width_str, str) and '%' in center_pad_width_str:
                width_percent = float(center_pad_width_str.rstrip('%')) / 100
                center_pad_width = top_center_distance * width_percent
            else:
                center_pad_width = float(center_pad_width_str)
            
            if isinstance(center_pad_height_str, str) and '%' in center_pad_height_str:
                height_percent = float(center_pad_height_str.rstrip('%')) / 100
                center_pad_height = left_center_distance * height_percent
            else:
                center_pad_height = float(center_pad_height_str)
            
            # 确保中心焊盘大小不为负数
            center_pad_width = max(10, center_pad_width)  # 最小宽度10
            center_pad_height = max(10, center_pad_height)  # 最小高度10
            
            # 计算中心焊盘位置
            pad_x = center_x - center_pad_width // 2 + center_pad_x_offset
            pad_y = center_y - center_pad_height // 2 + center_pad_y_offset
            
            parts.append(f'<rect fill="{center_pad_color}" height="{center_pad_height}" rx="{center_pad_radius}" ry="{center_pad_radius}" stroke="{center_pad_stroke_color}" stroke-width="{center_pad_stroke_width}" width="{center_pad_width}" x="{pad_x}" y="{pad_y}"/>')

        return '\n'.join(parts)

    def _generate_pins_two_row(self, chip: ChipModel, half_pins: int) -> str:
        parts = ['<g class="pin_layer">']

        # 获取封装类型配置前缀
        package_prefix = self._get_package_config_prefix(chip.package_type.value)
        
        # 读取焊盘配置
        pad_config = self.config_manager.get(f'焊盘.{package_prefix}焊盘', {})
        
        # 焊盘参数
        pin_rect_width = pad_config.get(f'{package_prefix}焊盘宽度', 20)
        pin_rect_height = pad_config.get(f'{package_prefix}焊盘高度', 10)
        pin_radius = pad_config.get(f'{package_prefix}_焊盘圆角', 2)
        pin_color = pad_config.get(f'{package_prefix}_焊盘颜色', '#cccccc')
        pin_stroke_color = pad_config.get(f'{package_prefix}_边线颜色', '#000000')
        pin_stroke_width = pad_config.get(f'{package_prefix}_边线宽度', 1)
        pin_number_font = pad_config.get(f'{package_prefix}焊盘编号字体', 'Cursive')
        pin_number_font_size = pad_config.get(f'{package_prefix}焊盘编号字体大小', 8)
        pin_number_font_color = pad_config.get(f'{package_prefix}_焊盘编号字体颜色', '#000000')

        # 计算芯片主体大小
        body_width, body_height, body_left, body_right, body_top, body_bottom, _ = self._calculate_body_size_two_row(half_pins, pin_rect_height)
        
        # 从配置文件中读取焊盘间距
        pin_spacing = pad_config.get(f'{package_prefix}焊盘间距', 10)
        self._pin_spacing = pin_spacing

        # 计算引脚列的总高度
        total_pin_height = (half_pins - 1) * self._pin_spacing + pin_rect_height
        # 计算引脚列的起始位置，使其与芯片主体居中对齐
        start_y = body_top + (body_height - total_pin_height) / 2

        for i in range(half_pins):
            pin_num_left = i + 1
            pin_num_right = 2 * half_pins - i
            
            pin_left = self._get_pin_by_number(chip, pin_num_left)
            pin_right = self._get_pin_by_number(chip, pin_num_right)

            y_pos = start_y + self._pin_spacing * i + pin_rect_height / 2

            # Left side pin
            if pin_left and pin_left.is_visible:
                x_left = body_left - pin_rect_width
                parts.append(f'<rect fill="{pin_color}" height="{pin_rect_height}" rx="{pin_radius}" ry="{pin_radius}" stroke="{pin_stroke_color}" stroke-width="{pin_stroke_width}" width="{pin_rect_width}" x="{x_left}" y="{y_pos - pin_rect_height/2}"/>')
                if pin_left.occupies_pin_number:
                    parts.append(f'<text fill="{pin_number_font_color}" font-family="{pin_number_font}" font-size="{pin_number_font_size}" stroke="#ffffff" text-anchor="middle" x="{x_left + pin_rect_width/2}" y="{y_pos + 3}">{pin_num_left}</text>')

            # Right side pin
            if pin_right and pin_right.is_visible:
                x_right = body_right
                parts.append(f'<rect fill="{pin_color}" height="{pin_rect_height}" rx="{pin_radius}" ry="{pin_radius}" stroke="{pin_stroke_color}" stroke-width="{pin_stroke_width}" width="{pin_rect_width}" x="{x_right}" y="{y_pos - pin_rect_height/2}"/>')
                if pin_right.occupies_pin_number:
                    parts.append(f'<text fill="{pin_number_font_color}" font-family="{pin_number_font}" font-size="{pin_number_font_size}" stroke="#ffffff" text-anchor="middle" x="{x_right + pin_rect_width/2}" y="{y_pos + 3}">{pin_num_right}</text>')

        parts.append('</g>')
        return '\n'.join(parts)

    def _generate_pins_four_row(self, chip: ChipModel, detail: PinCount) -> str:
        """生成四列封装的引脚
        
        Args:
            chip: 芯片模型
            detail: 四边的引脚数量
            
        Returns:
            生成的SVG引脚层
        """
        parts = ['<g class="pin_layer">']

        # 获取封装类型配置前缀
        package_prefix = self._get_package_config_prefix(chip.package_type.value)
        
        # 读取焊盘配置
        pad_config = self.config_manager.get(f'焊盘.{package_prefix}焊盘', {})
        
        # 焊盘参数
        pin_rect_width = pad_config.get(f'{package_prefix}焊盘宽度', 20)
        pin_rect_height = pad_config.get(f'{package_prefix}焊盘高度', 10)
        pin_radius = pad_config.get(f'{package_prefix}_焊盘圆角', 2)
        pin_color = pad_config.get(f'{package_prefix}_焊盘颜色', '#cccccc')
        pin_stroke_color = pad_config.get(f'{package_prefix}_边线颜色', '#000000')
        pin_stroke_width = pad_config.get(f'{package_prefix}_边线宽度', 1)
        pin_number_font = pad_config.get(f'{package_prefix}焊盘编号字体', 'Cursive')
        pin_number_font_size = pad_config.get(f'{package_prefix}焊盘编号字体大小', 8)
        pin_number_font_color = pad_config.get(f'{package_prefix}_焊盘编号字体颜色', '#000000')
        
        # 计算芯片主体大小
        body_width, body_height, body_left, body_top, body_right, body_bottom, _, _, _, _ = self._calculate_body_size_four_row(detail, pin_rect_height)
        
        # 从配置文件中读取焊盘间距
        pin_spacing = pad_config.get(f'{package_prefix}焊盘间距', 10)
        
        # 计算各边引脚间距（固定间距）
        top_spacing = pin_spacing if detail.top > 0 else 0
        right_spacing = pin_spacing if detail.right > 0 else 0
        bottom_spacing = pin_spacing if detail.bottom > 0 else 0
        left_spacing = pin_spacing if detail.left > 0 else 0

        # 检查是否是QFN封装
        is_qfn = package_prefix == "QFN"
        
        # 从配置文件中读取QFN焊盘边缘距离
        qfn_pad_margin = pad_config.get(f'{package_prefix}焊盘边缘距离', 0)

        # 计算各边焊盘的起始位置，确保居中对齐
        # 左边框引脚起始位置
        left_start_y = body_top + (body_height - (detail.left - 1) * left_spacing) / 2
        # 下边框引脚起始位置
        bottom_start_x = body_left + (body_width - (detail.bottom - 1) * bottom_spacing) / 2
        # 右边框引脚起始位置
        right_start_y = body_top + (body_height - (detail.right - 1) * right_spacing) / 2
        # 上边框引脚起始位置
        top_start_x = body_left + (body_width - (detail.top - 1) * top_spacing) / 2

        # 左边框引脚 (1 -> left) - 水平放置，从上到下
        current_pin = 1
        for i in range(detail.left):
            if is_qfn:
                # QFN焊盘在芯片内部，距离芯片左边缘的距离为qfn_pad_margin
                x_pos = body_left + qfn_pad_margin
            else:
                # 其他封装焊盘在芯片外部
                x_pos = body_left - pin_rect_width
            y_pos = left_start_y + left_spacing * i
            
            pin = self._get_pin_by_number(chip, current_pin)
            if pin and pin.is_visible:
                parts.append(f'<rect fill="{pin_color}" height="{pin_rect_height}" rx="{pin_radius}" ry="{pin_radius}" stroke="{pin_stroke_color}" stroke-width="{pin_stroke_width}" width="{pin_rect_width}" x="{x_pos}" y="{y_pos - pin_rect_height/2}"/>')
                if pin.occupies_pin_number:
                    parts.append(f'<text fill="{pin_number_font_color}" font-family="{pin_number_font}" font-size="{pin_number_font_size}" stroke="#ffffff" text-anchor="middle" x="{x_pos + pin_rect_width/2}" y="{y_pos + 3}">{current_pin}</text>')
            current_pin += 1

        # 下边框引脚 (left+1 -> left+bottom) - 垂直放置，从左到右
        for i in range(detail.bottom):
            x_pos = bottom_start_x + bottom_spacing * i
            if is_qfn:
                # QFN焊盘在芯片内部，距离芯片下边缘的距离为qfn_pad_margin
                y_pos = body_bottom - pin_rect_width - qfn_pad_margin
            else:
                # 其他封装焊盘在芯片外部
                y_pos = body_bottom
            
            pin = self._get_pin_by_number(chip, current_pin)
            if pin and pin.is_visible:
                parts.append(f'<rect fill="{pin_color}" height="{pin_rect_width}" rx="{pin_radius}" ry="{pin_radius}" stroke="{pin_stroke_color}" stroke-width="{pin_stroke_width}" width="{pin_rect_height}" x="{x_pos - pin_rect_height/2}" y="{y_pos}"/>')
                if pin.occupies_pin_number:
                    # 顶部和底部焊盘pin号旋转90度
                    # 对于垂直放置的焊盘，文本需要特殊处理
                    # 计算焊盘的中心点
                    pad_center_x = x_pos -  (pin_rect_height / 2)/1.4
                    pad_center_y = y_pos + pin_rect_width / 2
                    # 对于旋转90度的文本，我们使用不同的锚点设置
                    # 当文本旋转90度时，text-anchor和dominant-baseline的行为会改变
                    # 我们需要调整文本位置以确保它在焊盘内居中
                    parts.append(f'<text fill="{pin_number_font_color}" font-family="{pin_number_font}" font-size="{pin_number_font_size}" stroke="#ffffff" text-anchor="middle" x="{pad_center_x}" y="{pad_center_y}" transform="rotate(90, {pad_center_x}, {pad_center_y})">{current_pin}</text>')
            current_pin += 1

        # 右边框引脚 (left+bottom+1 -> left+bottom+right) - 水平放置，从下到上
        for i in range(detail.right):
            if is_qfn:
                # QFN焊盘在芯片内部，距离芯片右边缘的距离为qfn_pad_margin
                x_pos = body_right - pin_rect_width - qfn_pad_margin
            else:
                # 其他封装焊盘在芯片外部
                x_pos = body_right
            # 从下到上排列
            y_pos = right_start_y + right_spacing * (detail.right - 1 - i)
            
            pin = self._get_pin_by_number(chip, current_pin)
            if pin and pin.is_visible:
                parts.append(f'<rect fill="{pin_color}" height="{pin_rect_height}" rx="{pin_radius}" ry="{pin_radius}" stroke="{pin_stroke_color}" stroke-width="{pin_stroke_width}" width="{pin_rect_width}" x="{x_pos}" y="{y_pos - pin_rect_height/2}"/>')
                if pin.occupies_pin_number:
                    parts.append(f'<text fill="{pin_number_font_color}" font-family="{pin_number_font}" font-size="{pin_number_font_size}" stroke="#ffffff" text-anchor="middle" x="{x_pos + pin_rect_width/2}" y="{y_pos + 3}">{current_pin}</text>')
            current_pin += 1

        # 上边框引脚 (left+bottom+right+1 -> total) - 垂直放置，从右到左
        for i in range(detail.top):
            # 从右到左排列
            x_pos = top_start_x + top_spacing * (detail.top - 1 - i)
            if is_qfn:
                # QFN焊盘在芯片内部，距离芯片上边缘的距离为qfn_pad_margin
                y_pos = body_top + qfn_pad_margin
            else:
                # 其他封装焊盘在芯片外部
                y_pos = body_top - pin_rect_width
            
            pin = self._get_pin_by_number(chip, current_pin)
            if pin and pin.is_visible:
                parts.append(f'<rect fill="{pin_color}" height="{pin_rect_width}" rx="{pin_radius}" ry="{pin_radius}" stroke="{pin_stroke_color}" stroke-width="{pin_stroke_width}" width="{pin_rect_height}" x="{x_pos - pin_rect_height/2}" y="{y_pos}"/>')
                if pin.occupies_pin_number:
                    # 顶部和底部焊盘pin号旋转90度
                    # 对于垂直放置的焊盘，文本需要特殊处理
                    # 计算焊盘的中心点
                    pad_center_x = x_pos - (pin_rect_height / 2)/1.4
                    pad_center_y = y_pos + pin_rect_width / 2
                    # 对于旋转90度的文本，我们使用不同的锚点设置
                    # 当文本旋转90度时，text-anchor和dominant-baseline的行为会改变
                    # 我们需要调整文本位置以确保它在焊盘内居中
                    parts.append(f'<text fill="{pin_number_font_color}" font-family="{pin_number_font}" font-size="{pin_number_font_size}" stroke="#ffffff" text-anchor="middle" x="{pad_center_x}" y="{pad_center_y}" transform="rotate(90, {pad_center_x}, {pad_center_y})">{current_pin}</text>')
            current_pin += 1

        # 绘制中心焊盘引脚（如果有）
        if chip.has_center_pad:
            center_pin = self._get_pin_by_number(chip, 0)
            if center_pin and center_pin.is_visible:
                # 中心焊盘的位置和大小已经在_generate_chip_body_four_row中处理
                # 这里只需要添加引脚编号
                center_x = self._svg_width // 2
                center_y = self._svg_height // 2
                parts.append(f'<text fill="{pin_number_font_color}" font-family="{pin_number_font}" font-size="{pin_number_font_size}" stroke="#ffffff" text-anchor="middle" x="{center_x}" y="{center_y + 3}">0</text>')

        parts.append('</g>')
        return '\n'.join(parts)

    def _generate_labels_two_row(self, chip: ChipModel, half_pins: int) -> str:
        parts = ['<g class="label_layer">']

        # 计算芯片主体大小
        body_width, body_height, body_left, body_right, body_top, body_bottom, _ = self._calculate_body_size_two_row(half_pins, self._pin_rect_height)
        # 获取封装类型配置前缀
        package_prefix = self._get_package_config_prefix(chip.package_type.value)
        # 读取焊盘配置
        pad_config = self.config_manager.get(f'焊盘.{package_prefix}焊盘', {})
        # 读取标签间距
        label_spacing = pad_config.get(f'{package_prefix}标签间距', 10)
        # 读取焊盘间距
        pin_spacing = pad_config.get(f'{package_prefix}焊盘间距', 10)
        pidspacing = self.config_manager.get('焊盘.PID焊盘.PID标签间距', 6)
        pidspacingpin = self.config_manager.get('焊盘.PID焊盘.PID引脚与标签间距', 6)

        # 计算引脚列的总高度
        total_pin_height = (half_pins - 1) * pin_spacing + self._pin_rect_height
        # 计算引脚列的起始位置，使其与芯片主体居中对齐
        start_y = body_top + (body_height - total_pin_height) / 2

        for i in range(half_pins):
            pin_num_left = i + 1
            pin_num_right = 2 * half_pins - i
            
            pin_left = self._get_pin_by_number(chip, pin_num_left)
            pin_right = self._get_pin_by_number(chip, pin_num_right)
            
            y_pos = start_y + pin_spacing * i + self._pin_rect_height / 2

            # Left side labels
            if pin_left and pin_left.is_visible:
                # 左侧焊盘的位置
              
                label_x_left = body_left - self._pin_rect_width +  pidspacing - pidspacingpin +1 ###################
                for j, func in enumerate(pin_left.functions):
                    style = self.style_manager.get_style(func.group_name)
                    if style:
                        # 计算标签宽度
                        style = self.style_manager.get_style(func.group_name)
                        font_size = style.font_size if style else 12
                        width = self._calculate_text_width(func.name, style.font_family, font_size) + 7 
                        # 左侧标签起始位置 = 焊盘x - 间距 - 标签宽度
                        label_x = label_x_left - pidspacing - width 
                        print("===============================================")
                        print("L=",pidspacing)
                        print("L=",label_spacing)
                        parts.append(self._generate_function_label(func, style, label_x, y_pos))
                        # 更新下一个标签的起始位置
                        label_x_left = label_x

            # Right side labels
            if pin_right and pin_right.is_visible:

                label_x_right = body_right + self._pin_rect_width - pidspacing + pidspacingpin###################
                for j, func in enumerate(pin_right.functions):
                    style = self.style_manager.get_style(func.group_name)
                    if style:
                        # 右侧标签起始位置 = 焊盘x + 焊盘宽度 + 间距
                        label_x = label_x_right + pidspacing 
                        print("===============================================")
                        print("R=",pidspacing)
                        print("R=",label_spacing)
                        parts.append(self._generate_function_label(func, style, label_x, y_pos))
                        # 计算标签宽度并更新下一个标签的起始位置
                        style = self.style_manager.get_style(func.group_name)
                        font_size = style.font_size if style else 12
                        width = self._calculate_text_width(func.name, style.font_family, font_size) + 7 
                        label_x_right = label_x + width

        parts.append('</g>')
        return '\n'.join(parts)

    def _generate_labels_four_row(self, chip: ChipModel, detail: PinCount) -> str:
        parts = ['<g class="label_layer">']

        # 计算芯片主体大小
        body_width, body_height, body_left, body_top, body_right, body_bottom, _, _, _, _ = self._calculate_body_size_four_row(detail, self._pin_rect_height)
        
        # 获取封装类型配置前缀
        package_prefix = self._get_package_config_prefix(chip.package_type.value)
        
        # 读取焊盘配置
        pad_config = self.config_manager.get(f'焊盘.{package_prefix}焊盘', {})
        
        # 从配置文件中读取焊盘间距
        pin_spacing = pad_config.get(f'{package_prefix}焊盘间距', 10)
        # 从配置文件中读取标签间距
        label_spacing = pad_config.get(f'{package_prefix}标签间距', 10)
        # 从配置文件中读取引脚与标签间距
        pin2labelspacing = pad_config.get(f'{package_prefix}引脚与标签间距', 2)
        
        # 计算各边引脚间距（固定间距）
        top_spacing = pin_spacing if detail.top > 0 else 0
        right_spacing = pin_spacing if detail.right > 0 else 0
        bottom_spacing = pin_spacing if detail.bottom > 0 else 0
        left_spacing = pin_spacing if detail.left > 0 else 0
        
        # 计算各边焊盘的起始位置，确保居中对齐
        # 左边框引脚起始位置
        left_start_y = body_top + (body_height - (detail.left - 1) * left_spacing) / 2
        # 下边框引脚起始位置
        bottom_start_x = body_left + (body_width - (detail.bottom - 1) * bottom_spacing) / 2
        # 右边框引脚起始位置
        right_start_y = body_top + (body_height - (detail.right - 1) * right_spacing) / 2
        # 上边框引脚起始位置
        top_start_x = body_left + (body_width - (detail.top - 1) * top_spacing) / 2

        spacing = 2  # 引脚与标签的间距
        



        current_pin = 1
        # 左边框引脚标签 - 水平放置，从上到下
        for i in range(detail.left):
            x_pos = body_left - self._pin_rect_width + 17
            y_pos = left_start_y + left_spacing * i
            
            pin = self._get_pin_by_number(chip, current_pin)
            if pin and pin.is_visible:
                label_x_left = x_pos - self.QFN_pin2labelspacing
                for j, func in enumerate(pin.functions):
                    style = self.style_manager.get_style(func.group_name)
                    if style:
                        # 计算标签宽度
                        #style = self.style_manager.get_style(func.group_name)
                        font_size = style.font_size if style else 12
                        width = self._calculate_text_width(func.name, style.font_family, font_size) + 0 + label_spacing
                        # 左侧标签起始位置 = 焊盘x - 间距 - 标签宽度
                        label_x = label_x_left - label_spacing - width
                        parts.append(self._generate_function_label(func, style, label_x, y_pos))
                        # 更新下一个标签的起始位置
                        label_x_left = label_x
            current_pin += 1

        # 下边框引脚标签 - 右转90度，从左到右
        for i in range(detail.bottom):
            x_pos = bottom_start_x + bottom_spacing * i
            y_pos = body_bottom + self._pin_rect_width - 17
            pin = self._get_pin_by_number(chip, current_pin)
            if pin and pin.is_visible:
                label_y_bottom = y_pos+ self.QFN_pin2labelspacing
                for j, func in enumerate(pin.functions):
                    style = self.style_manager.get_style(func.group_name)
                    if style:
                        # 计算标签宽度（旋转后标签的宽度是垂直方向的长度）
                        style = self.style_manager.get_style(func.group_name)
                        font_size = style.font_size if style else 12
                        width = self._calculate_text_width(func.name, style.font_family, font_size) + 0 + label_spacing
                        # 下侧标签起始位置 = 焊盘y + 间距
                        label_y = label_y_bottom + label_spacing
                        # 调整x坐标，确保标签与焊盘左右对齐
                        label_x = x_pos
                        parts.append(self._generate_function_label(func, style, label_x, label_y, rotation=90))
                        # 更新下一个标签的起始位置
                        label_y_bottom = label_y + width
            current_pin += 1

        # 右边框引脚标签 - 水平放置，从下到上
        for i in range(detail.right):
            x_pos = body_right + self._pin_rect_width - 17
            # 从下到上排列，与引脚排列顺序一致
            y_pos = right_start_y + right_spacing * (detail.right - 1 - i)
            
            pin = self._get_pin_by_number(chip, current_pin)
            if pin and pin.is_visible:
                label_x_right = x_pos + self.QFN_pin2labelspacing
                for j, func in enumerate(pin.functions):
                    style = self.style_manager.get_style(func.group_name)
                    if style:
                        # 右侧标签起始位置 = 焊盘x + 焊盘宽度 + 间距
                        label_x = label_x_right + label_spacing
                        parts.append(self._generate_function_label(func, style, label_x, y_pos))
                        # 计算标签宽度并更新下一个标签的起始位置
                        style = self.style_manager.get_style(func.group_name)
                        font_size = style.font_size if style else 12
                        width = self._calculate_text_width(func.name, style.font_family, font_size) + 0 + label_spacing
                        label_x_right = label_x + width
            current_pin += 1

        # 上边框引脚标签 - 左转90度，从右到左
        for i in range(detail.top):
            # 从右到左排列，与引脚排列顺序一致
            x_pos = top_start_x + top_spacing * (detail.top - 1 - i)
            y_pos = body_top - self._pin_rect_width + 17
            
            pin = self._get_pin_by_number(chip, current_pin)
            if pin and pin.is_visible:
                label_y_top = y_pos - self.QFN_pin2labelspacing

                for j, func in enumerate(pin.functions):
                    style = self.style_manager.get_style(func.group_name)
                    if style:
                        # 上侧标签起始位置 = 焊盘y - 间距
                        label_y = label_y_top - label_spacing
                        # 调整x坐标，确保标签与焊盘左右对齐
                        label_x = x_pos
                        parts.append(self._generate_function_label(func, style, label_x, label_y, rotation=-90))
                        # 计算标签宽度（旋转后标签的宽度是垂直方向的长度）
                        style = self.style_manager.get_style(func.group_name)
                        font_size = style.font_size if style else 12
                        width = self._calculate_text_width(func.name, style.font_family, font_size) + 0 + label_spacing
                        # 更新下一个标签的起始位置
                        label_y_top = label_y - width
            current_pin += 1

        # 中心焊盘标签
        if chip.has_center_pad:
            center_pin = self._get_pin_by_number(chip, 0)
            if center_pin and center_pin.is_visible:
                center_x = self._svg_width // 2
                center_y = self._svg_height // 2
                label_y = center_y
                for j, func in enumerate(center_pin.functions):
                    style = self.style_manager.get_style(func.group_name)
                    if style:
                        # 中心焊盘标签在中心位置
                        label_x = center_x
                        parts.append(self._generate_function_label(func, style, label_x, label_y))
                        # 计算标签高度并更新下一个标签的位置
                        height = self._label_height + label_spacing
                        label_y = label_y + height

        parts.append('</g>')
        return '\n'.join(parts)

    def _generate_function_label(self, func, style: GroupStyle, x: float, y: float, rotation: int = 0) -> str:
        # 使用实际字体大小计算宽度 标签宽度计算
        font_size = style.font_size
        width = len(func.name) * font_size * 0.6 + 20  # 0.6是一个调整因子，因为字体宽度通常小于字体大小
        width = self._calculate_text_width(func.name, style.font_family, font_size) + 6
        height = self._label_height
        radius = style.border_radius
        
        # 构建字体属性
        font_weight = "bold" if style.font_bold else "normal"
        font_style = "italic" if style.font_italic else "normal"
        
        # 构建SVG元素
        elements = []
        
        # 添加矩形和文本
        if rotation != 0:
            # 对于旋转的标签，使用不同的坐标计算
            if rotation == 90:
                # 右转90度（下边框），标签从引脚下方开始，向右排列
                elements.append(f'<g transform="translate({x}, {y})"><g transform="rotate(90)"><rect fill="{style.background_color}" height="{height}" rx="{radius}" ry="{radius}" ' 
                              f'stroke="{style.border_color}" stroke-width="{style.border_width}" width="{width}" x="0" y="-{height/2}"/></g></g>')
                elements.append(f'<g transform="translate({x}, {y})"><g transform="rotate(90)"><text fill="{style.font_color}" font-family="{style.font_family}" font-size="{style.font_size}" ' 
                              f'font-weight="{font_weight}" font-style="{font_style}" text-anchor="middle" x="{width/2}" y="5">{func.name}</text></g></g>')
            elif rotation == -90:
                # 左转90度（上边框），标签从引脚上方开始，向左排列
                elements.append(f'<g transform="translate({x}, {y})"><g transform="rotate(-90)"><rect fill="{style.background_color}" height="{height}" rx="{radius}" ry="{radius}" ' 
                              f'stroke="{style.border_color}" stroke-width="{style.border_width}" width="{width}" x="0" y="-{height/2}"/></g></g>')
                elements.append(f'<g transform="translate({x}, {y})"><g transform="rotate(-90)"><text fill="{style.font_color}" font-family="{style.font_family}" font-size="{style.font_size}" ' 
                              f'font-weight="{font_weight}" font-style="{font_style}" text-anchor="middle" x="{width/2}" y="5">{func.name}</text></g></g>')
        else:
            # 非旋转标签（左右边框）
            elements.append(f'<rect fill="{style.background_color}" height="{height}" rx="{radius}" ry="{radius}" ' 
                          f'stroke="{style.border_color}" stroke-width="{style.border_width}" width="{width}" x="{x}" y="{y - height/2}"/>')
            elements.append(f'<text fill="{style.font_color}" font-family="{style.font_family}" font-size="{style.font_size}" ' 
                          f'font-weight="{font_weight}" font-style="{font_style}" text-anchor="middle" x="{x + width/2}" y="{y + 5}">{func.name}</text>')
        
        return ''.join(elements)

    def _generate_style_legend(self) -> str:
        parts = [f'<g class="legend_layer" transform="translate({self._legend_x}, {self._legend_y})" id="legend">']
        styles = self.style_manager.get_all_styles()
        items_per_column = self._legend_items_per_column
        column_width = self._legend_item_width + self._legend_column_spacing  # 列间距
        
        for i, style in enumerate(styles):
            # 计算所在列和行
            column = i // items_per_column
            row = i % items_per_column
            # 计算x和y坐标
            x = column * column_width
            y = row * self._legend_item_height
            
            # 构建字体属性
            font_weight = "bold" if style.font_bold else "normal"
            font_style = "italic" if style.font_italic else "normal"
            
            parts.append(f'<rect fill="{style.background_color}" height="{self._label_height}" rx="{style.border_radius}" ry="{style.border_radius}" stroke="{style.border_color}" stroke-width="{style.border_width}" width="{self._legend_item_width}" x="{x}" y="{y}"/>')
            parts.append(f'<text fill="{style.font_color}" font-family="{style.font_family}" font-size="{style.font_size}" font-weight="{font_weight}" font-style="{font_style}" text-anchor="middle" x="{x + self._legend_item_width/2}" y="{y + 12}">{style.name}</text>')
        parts.append('</g>')
        return '\n'.join(parts)

    def _generate_chip_title(self, chip: ChipModel) -> str:
        parts = []
        center_x = self._svg_width // 2
        center_y = self._svg_height // 2

        # 厂商名
        if chip.maker:
            parts.append(f'<text fill="#B2B2B2" font-family="{self._chip_title_font_family}" font-size="{self._chip_title_font_size}" font-weight="bold"  text-anchor="middle" x="{center_x}" y="{center_y - 30}">{chip.maker}</text>')
        # 芯片名称
        parts.append(f'<text fill="#B2B2B2" font-family="{self._chip_name_font_family}" font-size="{self._chip_name_font_size}" font-weight="bold" text-anchor="middle" x="{center_x}" y="{center_y - 0}">{chip.name}</text>')
        # 封装类型
        parts.append(f'<text fill="#B2B2B2" font-family="{self._chip_info_font_family}" font-size="{self._chip_info_font_size}" text-anchor="middle" x="{center_x}" y="{center_y + 20}">{chip.package_type.value}</text>')
        # 引脚数量
        parts.append(f'<text fill="#B2B2B2" font-family="{self._chip_info_font_family}" font-size="10" text-anchor="middle" x="{center_x}" y="{center_y + 30}">{chip.pin_count} PIN</text>')
 
        return '\n'.join(parts) 

    def _get_pin_by_number(self, chip: ChipModel, number: int) -> Optional[PinModel]:
        """根据重新计算的引脚序号获取引脚"""
        current_number = 1
        for pin in chip.pin_list:
            if pin.is_center_pad:
                continue
            if pin.occupies_pin_number:
                if current_number == number:
                    return pin
                current_number += 1
        return None
