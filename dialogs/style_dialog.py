from typing import Optional, List
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QFrame,
    QGridLayout, QColorDialog, QFontDialog, QSpinBox,
    QLineEdit, QCheckBox, QGroupBox, QScrollArea,
    QWidget, QMessageBox, QTextEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from models.style_model import GroupStyle, StyleManager
from utils.style_loader import StyleLoader

class StyleSelectDialog(QDialog):
    style_selected: pyqtSignal = pyqtSignal(str)
    styles_updated: pyqtSignal = pyqtSignal()  # 样式更新信号

    def __init__(self, style_manager: StyleManager, parent=None, readonly: bool = False):
        super().__init__(parent)
        self.style_manager = style_manager
        self.style_loader = StyleLoader(style_manager)
        self.readonly = readonly
        self.selected_style_name: Optional[str] = None
        self._setup_ui()
        self._load_styles()

    def _setup_ui(self):
        self.setWindowTitle("功能组样式选择")
        self.setMinimumSize(400, 300)
        self.setModal(True)

        main_layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(5)
        self.scroll_area.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll_area)

        if not self.readonly:
            btn_layout = QHBoxLayout()
            self.btn_edit = QPushButton("编辑")
            self.btn_add = QPushButton("添加新功能组")
            self.btn_close = QPushButton("关闭")
            self.btn_edit.clicked.connect(self._on_edit_clicked)
            self.btn_add.clicked.connect(self._on_add_clicked)
            self.btn_close.clicked.connect(self.close)
            btn_layout.addWidget(self.btn_edit)
            btn_layout.addWidget(self.btn_add)
            btn_layout.addStretch()
            btn_layout.addWidget(self.btn_close)
            main_layout.addLayout(btn_layout)
        
        # 添加提示文本
        hint_label = QLabel("双击标签编辑样式 点击组名重命名 清空组名删除")
        hint_label.setStyleSheet("color: #93a1a1; font-size: 10pt;")
        hint_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(hint_label)

    def _load_styles(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for style in self.style_manager.get_all_styles():
            item_widget = self._create_style_item(style)
            self.scroll_layout.addWidget(item_widget)

        self.scroll_layout.addStretch()

    def _create_style_item(self, style: GroupStyle) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {style.background_color};
                border: {style.border_width}px solid {style.border_color};
                border-radius: {style.border_radius}px;
                padding: 5px;
            }}
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)

        color_block = QFrame()
        color_block.setFixedSize(60, 20)
        color_block.setStyleSheet(f"background-color: {style.background_color}; border: 1px solid {style.border_color};")
        layout.addWidget(color_block)

        # 创建名称标签
        name_label = QLabel(style.name)
        name_label.setStyleSheet(f"color: {style.font_color}; font-family: {style.font_family}; font-size: {style.font_size}pt;")
        layout.addWidget(name_label)

        # 创建编辑框
        name_edit = QLineEdit(style.name)
        name_edit.setStyleSheet(f"color: {style.font_color}; font-family: {style.font_family}; font-size: {style.font_size}pt; border: 1px solid {style.border_color};")
        name_edit.hide()
        layout.addWidget(name_edit)

        layout.addStretch()

        if not self.readonly:
            # 双击事件
            frame.mouseDoubleClickEvent = lambda e, s=style: self._on_item_double_clicked(s)
            
            # 单击事件 - 进入编辑状态
            name_label.mousePressEvent = lambda e, lbl=name_label, edit=name_edit, s=style: self._on_name_clicked(lbl, edit, s)
            
            # 编辑完成事件
            name_edit.returnPressed.connect(lambda: self._on_name_edit_finished(name_edit, name_label, style))
            name_edit.editingFinished.connect(lambda: self._on_name_edit_finished(name_edit, name_label, style))

        return frame

    def _on_item_double_clicked(self, style: GroupStyle):
        if not self.readonly:
            # 打开功能组编辑窗口，并将当前功能组的属性作为初始值传入
            dialog = StyleEditDialog(self.style_manager, style, self)
            if dialog.exec_() == QDialog.Accepted:
                updated_style = dialog.get_style()
                if updated_style:
                    self.style_manager.update_style(updated_style)
                    self._load_styles()
                    # 保存到预设文件
                    self.style_loader.save_default_preset()
                    # 发送样式更新信号
                    self.styles_updated.emit()
            # 不需要发送style_selected信号，因为我们只是编辑样式，不是选择样式

    def _on_name_clicked(self, label: QLabel, edit: QLineEdit, style: GroupStyle):
        """处理名称标签的单击事件，进入编辑状态"""
        label.hide()
        edit.show()
        edit.setFocus()
        edit.selectAll()

    def _on_name_edit_finished(self, edit: QLineEdit, label: QLabel, style: GroupStyle):
        """处理名称编辑完成事件"""
        new_name = edit.text().strip()
        if not new_name:
            # 组名为空，弹出确认删除对话框
            reply = QMessageBox.question(self, "确认删除", f"确定要删除功能组 '{style.name}' 吗？", QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.style_manager.remove_style(style.name)
                self._load_styles()
                # 保存到预设文件
                self.style_loader.save_default_preset()
            else:
                # 取消删除，恢复原来的名称
                edit.setText(style.name)
                label.setText(style.name)
        else:
            # 更新样式名称
            if new_name != style.name:
                # 创建新的样式对象，更新名称，保留关联引脚名
                new_style = GroupStyle(
                    name=new_name,
                    font_family=style.font_family,
                    font_bold=style.font_bold,
                    font_italic=style.font_italic,
                    font_size=style.font_size,
                    font_color=style.font_color,
                    border_radius=style.border_radius,
                    border_width=style.border_width,
                    border_color=style.border_color,
                    background_color=style.background_color,
                    related_names=style.related_names
                )
                # 先删除旧样式，再添加新样式
                self.style_manager.remove_style(style.name)
                self.style_manager.add_style(new_style)
                self._load_styles()
                # 保存到预设文件
                self.style_loader.save_default_preset()
                # 发送样式更新信号
                self.styles_updated.emit()
            else:
                # 名称未变，恢复显示
                label.setText(new_name)
        # 恢复标签显示，隐藏编辑框
        label.show()
        edit.hide()

    def _on_edit_clicked(self):
        current_items = self.scroll_layout.itemAt(0)
        if not current_items:
            return

        dialog = StyleEditDialog(self.style_manager, None, self)
        if dialog.exec_() == QDialog.Accepted:
            new_style = dialog.get_style()
            if new_style:
                if new_style.name:
                    self.style_manager.update_style(new_style)
                else:
                    self.style_manager.add_style(new_style)
            self._load_styles()
            # 保存到预设文件
            self.style_loader.save_default_preset()
            # 发送样式更新信号
            self.styles_updated.emit()

    def _on_add_clicked(self):
        dialog = StyleEditDialog(self.style_manager, None, self)
        if dialog.exec_() == QDialog.Accepted:
            new_style = dialog.get_style()
            if new_style and new_style.name:
                self.style_manager.add_style(new_style)
                self._load_styles()
                # 保存到预设文件
                self.style_loader.save_default_preset()
                # 发送样式更新信号
                self.styles_updated.emit()


class StyleEditDialog(QDialog):
    def __init__(self, style_manager: StyleManager, style: Optional[GroupStyle] = None, parent=None):
        super().__init__(parent)
        self.style_manager = style_manager
        self.original_style = style
        self._setup_ui()
        if style:
            self._load_style(style)

    def _setup_ui(self):
        self.setWindowTitle("功能组样式编辑")
        self.setMinimumSize(450, 400)
        self.setModal(True)

        main_layout = QVBoxLayout(self)

        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.StyledPanel)
        preview_frame.setFixedHeight(50)
        preview_layout = QHBoxLayout(preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)

        self.lbl_preview = QLabel("预览")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.lbl_preview)
        preview_frame.setStyleSheet("border: 1px solid #000000;")
        main_layout.addWidget(preview_frame)

        form_layout = QGridLayout()

        form_layout.addWidget(QLabel("组名:"), 0, 0)
        self.txt_name = QLineEdit()
        self.txt_name.setMaxLength(50)
        form_layout.addWidget(self.txt_name, 0, 1)

        form_layout.addWidget(QLabel("字体:"), 1, 0)
        font_layout = QHBoxLayout()
        self.btn_font = QPushButton("选择字体")
        self.btn_font.clicked.connect(self._on_font_clicked)
        self.lbl_font = QLabel("默认字体")
        font_layout.addWidget(self.btn_font)
        font_layout.addWidget(self.lbl_font)
        font_layout.addStretch()
        form_layout.addLayout(font_layout, 1, 1)

        self.chk_bold = QCheckBox("加粗")
        self.chk_italic = QCheckBox("斜体")
        style_layout = QHBoxLayout()
        style_layout.addWidget(self.chk_bold)
        style_layout.addWidget(self.chk_italic)
        style_layout.addStretch()
        form_layout.addLayout(QLabel("样式:").layout() or QHBoxLayout(), 2, 0)
        form_layout.addLayout(style_layout, 2, 1)

        form_layout.addWidget(QLabel("字号:"), 3, 0)
        self.spn_font_size = QSpinBox()
        self.spn_font_size.setRange(8, 72)
        self.spn_font_size.setValue(16)
        form_layout.addWidget(self.spn_font_size, 3, 1)

        form_layout.addWidget(QLabel("字体颜色:"), 4, 0)
        color_layout = QHBoxLayout()
        self.btn_font_color = QPushButton("        ")
        self.btn_font_color.setStyleSheet("background-color: #000000; color: #ffffff; border: 1px solid #000000;")
        self.btn_font_color.clicked.connect(lambda: self._on_color_clicked("font"))
        color_layout.addWidget(self.btn_font_color)
        color_layout.addStretch()
        form_layout.addLayout(color_layout, 4, 1)

        form_layout.addWidget(QLabel("背景颜色:"), 5, 0)
        bg_layout = QHBoxLayout()
        self.btn_bg_color = QPushButton("        ")
        self.btn_bg_color.setStyleSheet("background-color: #ffffff; color: #000000; border: 1px solid #000000;")
        self.btn_bg_color.clicked.connect(lambda: self._on_color_clicked("bg"))
        bg_layout.addWidget(self.btn_bg_color)
        bg_layout.addStretch()
        form_layout.addLayout(bg_layout, 5, 1)

        form_layout.addWidget(QLabel("边框颜色:"), 6, 0)
        border_layout = QHBoxLayout()
        self.btn_border_color = QPushButton("        ")
        self.btn_border_color.setStyleSheet("background-color: #000000; color: #ffffff; border: 1px solid #000000;")
        self.btn_border_color.clicked.connect(lambda: self._on_color_clicked("border"))
        border_layout.addWidget(self.btn_border_color)
        border_layout.addStretch()
        form_layout.addLayout(border_layout, 6, 1)

        form_layout.addWidget(QLabel("圆角半径:"), 7, 0)
        self.spn_radius = QSpinBox()
        self.spn_radius.setRange(0, 20)
        self.spn_radius.setValue(3)
        form_layout.addWidget(self.spn_radius, 7, 1)

        form_layout.addWidget(QLabel("边框线宽:"), 8, 0)
        self.spn_border_width = QSpinBox()
        self.spn_border_width.setRange(0, 10)
        self.spn_border_width.setValue(1)
        form_layout.addWidget(self.spn_border_width, 8, 1)

        form_layout.addWidget(QLabel("关联引脚功能名:"), 9, 0)
        related_names_layout = QHBoxLayout()
        self.txt_related_names = QLineEdit()
        self.txt_related_names.setPlaceholderText("用逗号分隔，如: GPIO,ADC,UART")
        related_names_layout.addWidget(self.txt_related_names)
        
        # 添加"?"按钮
        self.btn_help = QPushButton("?")
        self.btn_help.setFixedSize(24, 24)
        self.btn_help.setToolTip("通配符使用帮助")
        self.btn_help.clicked.connect(self._show_wildcard_help)
        related_names_layout.addWidget(self.btn_help)
        
        form_layout.addLayout(related_names_layout, 9, 1)

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.btn_delete = QPushButton("删除")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok = QPushButton("确认")
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_ok.clicked.connect(self._on_ok_clicked)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        main_layout.addLayout(btn_layout)

        self.font_color = "#000000"
        self.bg_color = "#ffffff"
        self.border_color = "#000000"
        self.font_family = "Cursive"
        self.font_size = 16

        self.txt_name.textChanged.connect(self._update_preview)
        self.spn_font_size.valueChanged.connect(self._update_preview)
        self.chk_bold.toggled.connect(self._update_preview)
        self.chk_italic.toggled.connect(self._update_preview)
        self.spn_radius.valueChanged.connect(self._update_preview)
        self.spn_border_width.valueChanged.connect(self._update_preview)

    def _load_style(self, style: GroupStyle):
        self.txt_name.setText(style.name)
        self.font_family = style.font_family
        self.font_size = style.font_size
        self.lbl_font.setText(f"{style.font_family}, {style.font_size}pt")
        self.chk_bold.setChecked(style.font_bold)
        self.chk_italic.setChecked(style.font_italic)
        self.spn_font_size.setValue(style.font_size)
        self.font_color = style.font_color
        self.bg_color = style.background_color
        self.border_color = style.border_color
        self.spn_radius.setValue(style.border_radius)
        self.spn_border_width.setValue(style.border_width)
        # 加载关联引脚功能名
        self.txt_related_names.setText(",".join(style.related_names))

        # 更新按钮颜色
        text_color = "#ffffff" if self.font_color == "#000000" else "#000000"
        self.btn_font_color.setStyleSheet(f"background-color: {self.font_color}; color: {text_color}; border: 1px solid #000000;")
        
        text_color = "#000000" if self.bg_color == "#ffffff" else "#ffffff"
        self.btn_bg_color.setStyleSheet(f"background-color: {self.bg_color}; color: {text_color}; border: 1px solid #000000;")
        
        text_color = "#ffffff" if self.border_color == "#000000" else "#000000"
        self.btn_border_color.setStyleSheet(f"background-color: {self.border_color}; color: {text_color}; border: 1px solid #000000;")

        self._update_preview()

    def _on_font_clicked(self):
        font, ok = QFontDialog.getFont()
        if ok:
            self.font_family = font.family()
            self.font_size = font.pointSize()
            self.lbl_font.setText(f"{self.font_family}, {self.font_size}pt")
            self._update_preview()

    def _on_color_clicked(self, color_type: str):
        color_map = {
            "font": (self.font_color, "字体颜色"),
            "bg": (self.bg_color, "背景颜色"),
            "border": (self.border_color, "边框颜色")
        }
        current_color = color_map[color_type][0]
        title = color_map[color_type][1]

        color = QColorDialog.getColor(QColor(current_color), self, title)
        if color.isValid():
            color_hex = color.name()
            if color_type == "font":
                self.font_color = color_hex
                # 更新按钮颜色
                text_color = "#ffffff" if color_hex == "#000000" else "#000000"
                self.btn_font_color.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; border: 1px solid #000000;")
            elif color_type == "bg":
                self.bg_color = color_hex
                # 更新按钮颜色
                text_color = "#000000" if color_hex == "#ffffff" else "#ffffff"
                self.btn_bg_color.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; border: 1px solid #000000;")
            else:
                self.border_color = color_hex
                # 更新按钮颜色
                text_color = "#ffffff" if color_hex == "#000000" else "#000000"
                self.btn_border_color.setStyleSheet(f"background-color: {color_hex}; color: {text_color}; border: 1px solid #000000;")
            self._update_preview()

    def _update_preview(self):
        name = self.txt_name.text() or "预览"
        self.lbl_preview.setText(name)
        self.lbl_preview.setStyleSheet(f"""
            background-color: {self.bg_color};
            color: {self.font_color};
            font-family: {self.font_family};
            font-size: {self.spn_font_size.value()}pt;
            font-weight: {'bold' if self.chk_bold.isChecked() else 'normal'};
            font-style: {'italic' if self.chk_italic.isChecked() else 'normal'};
            border: {self.spn_border_width.value()}px solid {self.border_color};
            border-radius: {self.spn_radius.value()}px;
            padding: 5px;
        """)

    def _show_wildcard_help(self):
        """显示通配符使用帮助"""
        help_text = "将引脚功能(如:TXD,RXD,CTS,RTS,nCTS,)添加到\"功能组\"(如:USART)中,系统将自动匹配功能样式. 多个功能以\",\"逗号分割. 支持通配符 正则表达式\n\n"
        help_text += "通配符使用说明:\n\n"
        help_text += "1. 基本匹配:\n"
        help_text += "   - 直接输入功能名，如: GPIO, ADC\n"
        help_text += "\n"
        help_text += "2. 通配符匹配:\n"
        help_text += "   - *: 匹配任意字符（包括空字符）\n"
        help_text += "     如: GPIO* 匹配 GPIO, GPIOD, GPIOA1 等\n"
        help_text += "   - ?: 匹配单个字符\n"
        help_text += "     如: GPIO? 匹配 GPIOA, GPIOB 等，但不匹配 GPIO\n"
        help_text += "   - []: 匹配括号内的任意一个字符\n"
        help_text += "     如: GPIO[A-C] 匹配 GPIOA, GPIOB, GPIOC\n"
        help_text += "   - [^]: 匹配不在括号内的任意一个字符\n"
        help_text += "     如: GPIO[^A-C] 匹配 GPIOD, GPIOE 等\n"
        help_text += "\n"
        help_text += "3. 正则表达式:\n"
        help_text += "   - 可以使用完整的正则表达式语法\n"
        help_text += "   - 如: GPIO[0-9]+ 匹配 GPIO1, GPIO12 等\n"
        help_text += "\n"
        help_text += "4. 示例:\n"
        help_text += "   - GPIO*: 匹配所有以 GPIO 开头的功能名\n"
        help_text += "   - *ADC*: 匹配所有包含 ADC 的功能名\n"
        help_text += "   - PWM[0-9]: 匹配 PWM0 到 PWM9\n"
        
        dialog = QDialog(self)
        dialog.setWindowTitle("通配符使用帮助")
        dialog.resize(500, 400)
        
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setPlainText(help_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def _on_delete_clicked(self):
        reply = QMessageBox.question(self, "确认删除", "确定要删除此功能组吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.original_style:
                self.style_manager.remove_style(self.original_style.name)
                # 保存到预设文件
                StyleLoader(self.style_manager).save_default_preset()
            self.reject()

    def _on_ok_clicked(self):
        self.accept()

    def get_style(self) -> Optional[GroupStyle]:
        name = self.txt_name.text().strip()
        if not name:
            return None

        # 从文本框中读取关联引脚功能名
        related_names_text = self.txt_related_names.text().strip()
        related_names = []
        if related_names_text:
            related_names = [name.strip() for name in related_names_text.split(",")]
        elif self.original_style:
            # 如果文本框为空，使用原始样式的related_names（如果存在）
            related_names = self.original_style.related_names

        return GroupStyle(
            name=name,
            font_family=self.font_family,
            font_bold=self.chk_bold.isChecked(),
            font_italic=self.chk_italic.isChecked(),
            font_size=self.spn_font_size.value(),
            font_color=self.font_color,
            border_radius=self.spn_radius.value(),
            border_width=self.spn_border_width.value(),
            border_color=self.border_color,
            background_color=self.bg_color,
            related_names=related_names
        )