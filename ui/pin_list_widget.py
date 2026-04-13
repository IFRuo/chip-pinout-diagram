from typing import List, Optional, Callable
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QGridLayout, QPushButton,
    QCheckBox, QLineEdit, QToolButton, QSizePolicy,
    QSpacerItem, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtBoundSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from models.pin_model import PinModel, PinFunction
from models.style_model import GroupStyle, StyleManager

class FunctionField(QFrame):
    clicked: pyqtSignal = pyqtSignal(int, int)
    double_clicked: pyqtSignal = pyqtSignal(int, int)
    text_edited: pyqtSignal = pyqtSignal(int, int, str)

    def __init__(self, pin_index: int, func_index: int, func: PinFunction, style: Optional[GroupStyle] = None, parent=None):
        super().__init__(parent)
        self.pin_index = pin_index
        self.func_index = func_index
        self.func = func
        self.style = style
        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumHeight(20)
        self.setMinimumWidth(60)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        self.lbl_func_name = QLabel(self.func.name if self.func.name else "")
        self.lbl_func_name.setAlignment(Qt.AlignCenter)
        self.lbl_func_name.setWordWrap(False)

        self.le_edit = QLineEdit(self.func.name if self.func.name else "")
        self.le_edit.setAlignment(Qt.AlignCenter)
        self.le_edit.hide()
        self.le_edit.returnPressed.connect(self._on_edit_finished)
        self.le_edit.editingFinished.connect(self._on_edit_finished)

        layout.addWidget(self.lbl_func_name)
        layout.addWidget(self.le_edit)

    def mousePressEvent(self, event):
        self._start_editing()

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.pin_index, self.func_index)

    def _update_style(self):
        if self.style:
            # 为QLabel和QLineEdit设置明确的字体大小
            self.lbl_func_name.setStyleSheet(
                f"color: {self.style.font_color}; "
                f"font-family: {self.style.font_family}; "
                f"font-size: {self.style.font_size}pt; "
                f"font-weight: {'bold' if self.style.font_bold else 'normal'}; "
                f"font-style: {'italic' if self.style.font_italic else 'normal'};"
            )
            self.le_edit.setStyleSheet(
                f"color: {self.style.font_color}; "
                f"font-family: {self.style.font_family}; "
                f"font-size: {self.style.font_size}pt; "
                f"font-weight: {'bold' if self.style.font_bold else 'normal'}; "
                f"font-style: {'italic' if self.style.font_italic else 'normal'}; "
                f"border: none; "
                f"padding: 0;"
            )
            # 设置QFrame的样式
            self.setStyleSheet(
                f"QFrame {{ "
                f"background-color: {self.style.background_color}; "
                f"border: {self.style.border_width}px solid {self.style.border_color}; "
                f"border-radius: {self.style.border_radius}px; "
                f"}}"
            )
        else:
            # 没有功能组样式时的默认样式
            self.lbl_func_name.setStyleSheet("font-size: 12pt;")
            self.le_edit.setStyleSheet("border: none; padding: 0; font-size: 12pt;")
            self.setStyleSheet(
                "QFrame { background-color: #ffffff; border: 1px solid #000000; border-radius: 3px; }"
            )



    def _start_editing(self):
        self.lbl_func_name.hide()
        self.le_edit.setText(self.func.name if self.func.name else "")
        self.le_edit.show()
        self.le_edit.setFocus()
        self.le_edit.selectAll()

    def _on_edit_finished(self):
        text = self.le_edit.text().strip()
        self.lbl_func_name.setText(text)
        self.lbl_func_name.show()
        self.le_edit.hide()
        self.text_edited.emit(self.pin_index, self.func_index, text)

    def set_function_name(self, name: str):
        self.func.name = name
        self.lbl_func_name.setText(name)

    def set_style(self, style: Optional[GroupStyle]):
        self.style = style
        self._update_style()


class PinRowWidget(QFrame):
    visibility_changed: pyqtSignal = pyqtSignal(int, bool)
    occupies_changed: pyqtSignal = pyqtSignal(int, bool)
    function_clicked: pyqtSignal = pyqtSignal(int, int)
    function_double_clicked: pyqtSignal = pyqtSignal(int, int)
    function_text_edited: pyqtSignal = pyqtSignal(int, int, str)
    add_function_clicked: pyqtSignal = pyqtSignal(int)
    remove_pin_clicked: pyqtSignal = pyqtSignal(int)

    def __init__(self, pin: PinModel, pin_index: int, style_manager: StyleManager, parent=None):
        super().__init__(parent)
        self.pin = pin
        self.pin_index = pin_index
        self.style_manager = style_manager
        self._setup_ui()
        self._update_from_pin()

    def _setup_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setMinimumHeight(25)
        self.setMaximumHeight(30)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)

        self.chk_visible = QCheckBox()
        self.chk_visible.setFixedWidth(20)
        self.chk_visible.stateChanged.connect(self._on_visibility_changed)

        self.chk_occupies = QCheckBox()
        self.chk_occupies.setFixedWidth(20)
        self.chk_occupies.stateChanged.connect(self._on_occupies_changed)

        self.lbl_pin_number = QLabel(f"{self.pin.number:02d}")
        self.lbl_pin_number.setFixedWidth(30)
        self.lbl_pin_number.setAlignment(Qt.AlignCenter)

        self.frame_functions = QFrame()
        self.frame_functions.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        functions_layout = QHBoxLayout(self.frame_functions)
        functions_layout.setContentsMargins(0, 0, 0, 0)
        functions_layout.setSpacing(2)

        self.btn_add = QPushButton("+")
        self.btn_add.setFixedWidth(20)
        self.btn_add.clicked.connect(self._on_add_clicked)
        
        # 对于pin0的特殊处理
        if self.pin.is_center_pad:
            self.btn_add.setEnabled(False)
            self.chk_occupies.setEnabled(False)

        main_layout.addWidget(self.chk_visible)
        main_layout.addWidget(self.chk_occupies)
        main_layout.addWidget(self.lbl_pin_number)
        main_layout.addWidget(self.frame_functions)
        main_layout.addWidget(self.btn_add)

    def _update_from_pin(self):
        self.chk_visible.setChecked(self.pin.is_visible)
        self.chk_occupies.setChecked(self.pin.occupies_pin_number)
        self.lbl_pin_number.setText(f"{self.pin.number:02d}")

        functions_layout = self.frame_functions.layout()
        while functions_layout.count():
            child = functions_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, func in enumerate(self.pin.functions):
            style = self.style_manager.get_style(func.group_name)
            func_widget = FunctionField(self.pin_index, i, func, style)
            func_widget.clicked.connect(self._on_function_clicked)
            func_widget.double_clicked.connect(self._on_function_double_clicked)
            func_widget.text_edited.connect(self._on_function_text_edited)
            functions_layout.addWidget(func_widget)

    def _on_visibility_changed(self, state):
        self.visibility_changed.emit(self.pin_index, state == Qt.Checked)

    def _on_occupies_changed(self, state):
        self.occupies_changed.emit(self.pin_index, state == Qt.Checked)

    def _on_function_clicked(self, pin_idx, func_idx):
        self.function_clicked.emit(pin_idx, func_idx)

    def _on_function_double_clicked(self, pin_idx, func_idx):
        self.function_double_clicked.emit(pin_idx, func_idx)

    def _on_function_text_edited(self, pin_idx, func_idx, text):
        self.function_text_edited.emit(pin_idx, func_idx, text)

    def _on_add_clicked(self):
        self.add_function_clicked.emit(self.pin_index)

    def update_pin(self, pin: PinModel):
        self.pin = pin
        self._update_from_pin()


class PinListWidget(QWidget):
    add_pin_clicked: pyqtSignal = pyqtSignal()
    pin_updated: pyqtSignal = pyqtSignal(int, object)  # 使用object类型以支持None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pins: List[PinModel] = []
        self.style_manager = StyleManager()
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.lbl_title = QLabel("引脚功能分配")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("background-color: #fce8e8; padding: 5px;")
        main_layout.addWidget(self.lbl_title)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(2)
        self.content_layout.addStretch()

        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)

        self.btn_add_pin = QPushButton("添加引脚")
        self.btn_add_pin.clicked.connect(self.add_pin_clicked.emit)
        main_layout.addWidget(self.btn_add_pin)

    def set_style_manager(self, manager: StyleManager):
        self.style_manager = manager

    def set_pins(self, pins: List[PinModel]):
        self.pins = pins
        self._rebuild_pin_rows()

    def get_pins(self) -> List[PinModel]:
        return self.pins

    def add_pin(self, pin: PinModel):
        self.pins.append(pin)
        # 重新计算引脚序号
        self._update_pin_numbers()
        # 重新构建引脚行，确保所有引脚的编号都正确显示
        self._rebuild_pin_rows()
        # 发送信号通知主窗口更新芯片信息
        self.pin_updated.emit(-1, None)  # -1表示整体更新

    def remove_pin(self, pin_index: int):
        """删除指定索引的引脚"""
        if 0 <= pin_index < len(self.pins):
            del self.pins[pin_index]
            self._rebuild_pin_rows()
            # 发送整体更新信号
            self.pin_updated.emit(-1, None)

    def _rebuild_pin_rows(self):
        while self.content_layout.count() > 1:
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i, pin in enumerate(self.pins):
            self._add_pin_row(pin, i)

        stretch_item = self.content_layout.takeAt(self.content_layout.count() - 1)
        if stretch_item:
            self.content_layout.addStretch()

    def _add_pin_row(self, pin: PinModel, index: int):
        row = PinRowWidget(pin, index, self.style_manager)
        row.visibility_changed.connect(self._on_visibility_changed)
        row.occupies_changed.connect(self._on_occupies_changed)
        row.function_clicked.connect(self._on_function_clicked)
        row.function_double_clicked.connect(self._on_function_double_clicked)
        row.function_text_edited.connect(self._on_function_text_edited)
        row.add_function_clicked.connect(self._on_add_function_clicked)

        count = self.content_layout.count()
        if count > 0:
            last_item = self.content_layout.itemAt(count - 1)
            if last_item and last_item.spacerItem():
                self.content_layout.insertWidget(count - 1, row)
            else:
                self.content_layout.insertWidget(count, row)
        else:
            self.content_layout.addWidget(row)

    def _on_visibility_changed(self, pin_index, is_visible):
        if 0 <= pin_index < len(self.pins):
            self.pins[pin_index].is_visible = is_visible
            self.pin_updated.emit(pin_index, self.pins[pin_index])

    def _on_occupies_changed(self, pin_index, occupies):
        if 0 <= pin_index < len(self.pins):
            self.pins[pin_index].occupies_pin_number = occupies
            # 重新计算引脚序号
            self._update_pin_numbers()
            self._rebuild_pin_rows()
            # 发送信号通知主窗口更新芯片信息
            self.pin_updated.emit(-1, None)  # -1表示整体更新

    def _update_pin_numbers(self):
        """重新计算引脚序号"""
        current_pin_number = 1
        for pin in self.pins:
            if pin.is_center_pad:
                continue
            if pin.occupies_pin_number:
                pin.number = current_pin_number
                current_pin_number += 1
        # 不需要发送信号，因为已经在调用处发送了

    def _on_function_clicked(self, pin_index, func_index):
        pass

    def _on_function_double_clicked(self, pin_index, func_index):
        pass

    def _on_function_text_edited(self, pin_index, func_index, text):
        if 0 <= pin_index < len(self.pins):
            pin = self.pins[pin_index]
            if 0 <= func_index < len(pin.functions):
                if not text:
                    # 对于pin0，不能删除功能字段，只清空内容
                    if pin.is_center_pad:
                        pin.functions[func_index].name = ""
                        pin.functions[func_index].group_name = ""
                    else:
                        pin.remove_function(func_index)
                        # 检查该引脚是否还有其他功能字段
                        if len(pin.functions) == 0:
                            # 如果没有功能字段，删除该引脚
                            self.remove_pin(pin_index)
                    self._rebuild_pin_rows()
                    self.pin_updated.emit(pin_index, pin)
                else:
                    pin.functions[func_index].name = text
                    # 自动匹配功能组
                    matched_style = self.style_manager.find_style_by_function(text)
                    if matched_style:
                        pin.functions[func_index].group_name = matched_style.name
                    else:
                        pin.functions[func_index].group_name = ""
                    self._rebuild_pin_rows()
                    self.pin_updated.emit(pin_index, pin)

    def _on_add_function_clicked(self, pin_index):
        if 0 <= pin_index < len(self.pins):
            self.pins[pin_index].add_function("", "")
            self._rebuild_pin_rows()
            self.pin_updated.emit(pin_index, self.pins[pin_index])
