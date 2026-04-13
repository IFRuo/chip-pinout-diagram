import sys
import os
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt
from models import ChipModel, PinModel, StyleManager
from ui import MainWindow
from utils import StyleLoader, FileParser, SvgGenerator
from dialogs import StyleSelectDialog

class ChipPinApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyle('Fusion')

        self.style_manager = StyleManager()
        self._load_styles()

        self.main_window = MainWindow()
        self._setup_connections()

        self.file_parser = FileParser(self.style_manager)
        self.svg_generator = SvgGenerator(self.style_manager)

    def _load_styles(self):
        loader = StyleLoader(self.style_manager)
        preset_path = loader.get_default_preset_path()
        if os.path.exists(preset_path):
            loader.load_from_file(preset_path)
        else:
            loader.save_default_preset()

    def _setup_connections(self):
        main_window = self.main_window
        info_bar = main_window.get_info_bar()
        pin_list = main_window.get_pin_list_widget()
        svg_viewer = main_window.get_svg_viewer()

        info_bar.chip_name_changed.connect(self._on_chip_name_changed)
        info_bar.chip_maker_changed.connect(self._on_chip_name_changed)
        info_bar.package_type_changed.connect(self._on_package_type_changed)
        info_bar.pin_count_changed.connect(self._on_pin_count_changed)
        info_bar.pin_count_detail_changed.connect(self._on_pin_count_detail_changed)
        info_bar.style_manager_clicked.connect(self._on_style_manager_clicked)

        pin_list.set_style_manager(self.style_manager)
        pin_list.add_pin_clicked.connect(self._on_add_pin_clicked)
        pin_list.pin_updated.connect(self._on_pin_updated)

        # 连接SVG查看器的画布大小变化信号
        svg_viewer.canvas_size_changed.connect(self._on_canvas_size_changed)

        main_window.read_clicked.connect(self._on_read_clicked)
        main_window.save_clicked.connect(self._on_save_clicked)
        main_window.export_clicked.connect(self._on_export_clicked)
        main_window.load_style_clicked.connect(self._on_load_style_clicked)
        main_window.save_style_clicked.connect(self._on_save_style_clicked)

    def _create_default_pins(self, count: int, has_center_pad: bool = False):
        pins = []
        if has_center_pad:
            center_pin = PinModel(number=0)
            center_pin.add_function("NC", "NC")
            pins.append(center_pin)

        for i in range(1, count + 1):
            pin = PinModel(number=i)
            pin.add_function(f"P{i}", "GPIO")
            pins.append(pin)

        return pins

    def _on_chip_name_changed(self, name: str):
        self._update_svg()

    def _on_package_type_changed(self, package: str):
        self._update_svg()

    def _on_pin_count_changed(self, count: int):
        # 检查PinListWidget中的引脚列表是否为空，而不是检查芯片模型中的
        pin_list_widget = self.main_window.get_pin_list_widget()
        if len(pin_list_widget.get_pins()) == 0:
            pins = self._create_default_pins(count, False)
            pin_list_widget.set_pins(pins)
        self._update_svg()

    def _on_pin_count_detail_changed(self, detail):
        # 检查PinListWidget中的引脚列表是否为空，而不是检查芯片模型中的
        pin_list_widget = self.main_window.get_pin_list_widget()
        if len(pin_list_widget.get_pins()) == 0:
            total_pins = detail.total
            pins = self._create_default_pins(total_pins, False)
            pin_list_widget.set_pins(pins)
        self._update_svg()

    def _on_style_manager_clicked(self):
        dialog = StyleSelectDialog(self.style_manager, self.main_window, readonly=False)
        # 连接样式更新信号
        dialog.styles_updated.connect(self._on_styles_updated)
        dialog.exec_()
    
    def _on_styles_updated(self):
        """处理样式更新事件，刷新功能列表和绘制区"""
        # 刷新功能列表
        pin_list_widget = self.main_window.get_pin_list_widget()
        if pin_list_widget:
            pin_list_widget._rebuild_pin_rows()
        # 刷新绘制区
        self._update_svg()

    def _on_load_style_clicked(self):
        """处理载入样式按钮点击事件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "载入样式文件",
            ".",
            "样式文件 (*.gn);;所有文件 (*.*)"
        )
        if file_path:
            try:
                loader = StyleLoader(self.style_manager)
                loader.load_from_file(file_path)
                # 刷新功能列表和绘制区
                self._on_styles_updated()
            except Exception as e:
                QMessageBox.warning(self.main_window, "错误", f"载入样式文件失败: {str(e)}")

    def _on_save_style_clicked(self):
        """处理保存样式按钮点击事件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "保存样式文件",
            ".",
            "样式文件 (*.gn);;所有文件 (*.*)"
        )
        if file_path:
            try:
                loader = StyleLoader(self.style_manager)
                loader.save_to_file(file_path)
            except Exception as e:
                QMessageBox.warning(self.main_window, "错误", f"保存样式文件失败: {str(e)}")

    def _on_add_pin_clicked(self):
        chip = self.main_window.get_chip_model()
        new_pin_num = len(chip.pin_list) + 1
        new_pin = PinModel(number=new_pin_num)
        new_pin.add_function("", "GPIO")
        self.main_window.get_pin_list_widget().add_pin(new_pin)
        self._update_svg()

    def _on_pin_updated(self, index: int, pin: PinModel):
        if index == -1:
            # 整体更新，重新计算芯片引脚数
            chip = self.main_window.get_chip_model()
            visible_pins = [p for p in self.main_window.get_pin_list_widget().get_pins() if p.occupies_pin_number and p.number != 0]
            chip.pin_count = len(visible_pins)
            # 只更新引脚数，不重新设置整个模型，避免递归更新
            self.main_window.get_info_bar().spn_pin_count.setValue(chip.pin_count)
        self._update_svg()

    def _on_read_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            "读取芯片引脚文件",
            ".",
            "芯片引脚文件 (*.txt);;所有文件 (*.*)"
        )
        if not file_path:
            return

        # 先读取文件内容，检查是否包含样式配置
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            QMessageBox.warning(self.main_window, "错误", f"读取文件失败: {str(e)}")
            return

        # 检查文件是否包含样式配置
        has_styles = False
        lines = content.strip().split('\n')
        if lines and lines[0].strip() == '[Chip pin function]':
            # 新格式文件，检查是否有样式行
            for line in lines[4:]:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('*'):
                    line = line.lstrip('*').strip()
                if not line:
                    continue
                if '\t:' in line:
                    has_styles = True
                    break

        # 如果有样式配置，询问是否载入
        include_styles = True
        if has_styles:
            reply = QMessageBox.question(
                self.main_window,
                "载入样式配置",
                "是否载入文件中的样式配置？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            include_styles = (reply == QMessageBox.Yes)

        # 根据用户选择读取文件
        current_chip = self.main_window.get_chip_model()
        chip = self.file_parser.parse_chip_file(file_path, current_chip, include_styles)
        if chip:
            self.main_window.set_chip_model(chip)
            self.main_window.get_pin_list_widget().set_pins(chip.pin_list)
            # 如果载入了样式配置，刷新功能列表
            if include_styles:
                self.main_window.get_pin_list_widget()._rebuild_pin_rows()
            self._update_svg()
        else:
            QMessageBox.warning(self.main_window, "错误", "文件格式错误或读取失败！")

    def _on_save_clicked(self):
        chip = self.main_window.get_chip_model()
        chip.pin_list = self.main_window.get_pin_list_widget().get_pins()

        default_name = chip.get_file_name() if chip.name else "未命名"
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "保存芯片引脚文件",
            f"{default_name}.txt",
            "芯片引脚文件 (*.txt);;所有文件 (*.*)"
        )
        if not file_path:
            return

        # 提示是否写入样式配置
        reply = QMessageBox.question(
            self.main_window,
            "保存样式配置",
            "是否写入样式配置到文件？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        # 根据用户选择生成文件内容
        if reply == QMessageBox.Yes:
            content = self.file_parser.generate_chip_file_content(chip)
        else:
            # 生成不包含样式配置的文件内容
            content = self.file_parser.generate_chip_file_content(chip, include_styles=False)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            #QMessageBox.information(self.main_window, "成功", "文件保存成功！")
        except Exception as e:
            QMessageBox.warning(self.main_window, "错误", f"保存失败: {str(e)}")

    def _on_export_clicked(self):
        chip = self.main_window.get_chip_model()
        chip.pin_list = self.main_window.get_pin_list_widget().get_pins()

        default_name = chip.get_file_name() if chip.name else "未命名"
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "导出SVG图片",
            f"{default_name}.svg",
            "SVG文件 (*.svg);;所有文件 (*.*)"
        )
        if not file_path:
            return

        svg_content = self.svg_generator.generate(chip)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            #QMessageBox.information(self.main_window, "成功", "SVG导出成功！")
        except Exception as e:
            QMessageBox.warning(self.main_window, "错误", f"导出失败: {str(e)}")

    def _on_canvas_size_changed(self, width: int, height: int):
        """处理画布大小变化事件"""
        # 更新SVG生成器的画布大小
        self.svg_generator.set_canvas_size(width, height)
        # 重新生成SVG
        self._update_svg()

    def _update_svg(self):
        chip = self.main_window.get_chip_model()
        chip.pin_list = self.main_window.get_pin_list_widget().get_pins()

        # 计算芯片图内容大小
        width, height = self.svg_generator.calculate_chip_bounds(chip)
        # 更新芯片图大小标签
        self.main_window.get_svg_viewer().set_chip_size(width, height)

        # 生成SVG（这会自动调整画布大小）
        svg_content = self.svg_generator.generate(chip)
        # 更新SVG查看器
        self.main_window.get_svg_viewer().set_svg_content(svg_content)
        
        # 获取实际画布大小并更新输入框
        svg_width = int(self.svg_generator._svg_width / 1.2)  # 除以1.2，因为内部存储的是放大后的大小
        svg_height = int(self.svg_generator._svg_height / 1.2)
        self.main_window.get_svg_viewer().txt_width.setText(str(svg_width))
        self.main_window.get_svg_viewer().txt_height.setText(str(svg_height))

    def run(self):
        chip = self.main_window.get_chip_model()
        pins = self._create_default_pins(chip.pin_count, chip.has_center_pad)
        self.main_window.get_pin_list_widget().set_pins(pins)

        self._update_svg()

        self.main_window.show()
        return self.app.exec_()

def main():
    app = ChipPinApp()
    sys.exit(app.run())

if __name__ == '__main__':
    main()
