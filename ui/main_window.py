from typing import List, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QGroupBox, QScrollArea,
    QFrame, QGridLayout, QSizePolicy, QSpacerItem
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtBoundSignal
from models.chip_model import ChipModel, PackageType, PinCount
from models.pin_model import PinModel
from models.style_model import StyleManager
from ui.pin_list_widget import PinListWidget
from ui.svg_viewer import SvgViewerWidget

class InfoBarWidget(QWidget):
    chip_name_changed: pyqtSignal = pyqtSignal(str)
    chip_maker_changed: pyqtSignal = pyqtSignal(str)
    package_type_changed: pyqtSignal = pyqtSignal(str)
    pin_count_changed: pyqtSignal = pyqtSignal(int)
    pin_count_detail_changed: pyqtSignal = pyqtSignal(object)
    style_manager_clicked: pyqtSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 控件样式
        label_style = "QLabel { font-weight: bold; }"
        line_edit_style = """
        QLineEdit {
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 4px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border: 2px solid #4CAF50;
        }
        """
        combo_box_style = """
        QComboBox {
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 4px;
            font-size: 14px;
        }
        QComboBox:focus {
            border: 2px solid #4CAF50;
        }
        """
        spin_box_style = """
        QSpinBox {
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 4px;
            font-size: 14px;
        }
        QSpinBox:focus {
            border: 2px solid #4CAF50;
        }
        """
        button_style = """
        QPushButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 6px 12px;
            text-align: center;
            text-decoration: none;
            font-size: 14px;
            margin: 2px 1px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #0b7dda;
        }
        QPushButton:pressed {
            background-color: #0a6bc1;
        }
        """

        self.lbl_chip_name = QLabel("芯片名称:")
        #self.lbl_chip_name.setStyleSheet(label_style)
        self.txt_chip_Maker = QLineEdit()
        self.txt_chip_Maker.setPlaceholderText("芯片厂商")
        self.txt_chip_Maker.setFixedWidth(180)  # 大约10个汉字字符长度
        self.txt_chip_Maker.setStyleSheet(line_edit_style)
        self.txt_chip_name = QLineEdit()
        self.txt_chip_name.setPlaceholderText("芯片名称")
        self.txt_chip_name.setFixedWidth(270)  # 大约15个汉字字符长度
        self.txt_chip_name.setStyleSheet(line_edit_style)

        self.lbl_package = QLabel("封装类型:")
        #self.lbl_package.setStyleSheet(label_style)
        self.cmb_package = QComboBox()
        self.cmb_package.addItems([pt.value for pt in PackageType])
        #self.cmb_package.setStyleSheet(combo_box_style)

        self.lbl_pin_count = QLabel("引脚数:") #
        #self.lbl_pin_count.setStyleSheet(label_style)
        self.spn_pin_count = QSpinBox()
        self.spn_pin_count.setRange(1, 999)
        self.spn_pin_count.setValue(16)
        self.spn_pin_count.setPrefix("")
        self.spn_pin_count.setSuffix("")
        self.spn_pin_count.setStyleSheet(spin_box_style)

        self.frame_pin_count_detail = QFrame()
        self.frame_pin_count_detail.setFrameShape(QFrame.StyledPanel)
        self.frame_pin_count_detail.setStyleSheet("background-color: #f9f9f9; padding: 2px;")
        detail_layout = QHBoxLayout(self.frame_pin_count_detail)
        detail_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_top = QLabel("上:")
        #self.lbl_top.setStyleSheet(label_style)
        self.spn_top = QSpinBox()
        self.spn_top.setRange(0, 99)
        self.spn_top.setValue(8)
        #self.spn_top.setStyleSheet(spin_box_style)
        self.lbl_left = QLabel("左:")
        #self.lbl_left.setStyleSheet(label_style)
        self.spn_left = QSpinBox()
        self.spn_left.setRange(0, 99)
        self.spn_left.setValue(8)
        #self.spn_left.setStyleSheet(spin_box_style)
        self.lbl_bottom = QLabel("下:")
        #self.lbl_bottom.setStyleSheet(label_style)
        self.spn_bottom = QSpinBox()
        self.spn_bottom.setRange(0, 99)
        self.spn_bottom.setValue(8)
        #self.spn_bottom.setStyleSheet(spin_box_style)
        self.lbl_right = QLabel("右:")
        #self.lbl_right.setStyleSheet(label_style)
        self.spn_right = QSpinBox()
        self.spn_right.setRange(0, 99)
        self.spn_right.setValue(8)
        #self.spn_right.setStyleSheet(spin_box_style)

        detail_layout.addWidget(self.lbl_top)
        detail_layout.addWidget(self.spn_top)
        detail_layout.addWidget(self.lbl_left)
        detail_layout.addWidget(self.spn_left)
        detail_layout.addWidget(self.lbl_bottom)
        detail_layout.addWidget(self.spn_bottom)
        detail_layout.addWidget(self.lbl_right)
        detail_layout.addWidget(self.spn_right)
        detail_layout.addStretch()

        self.btn_style_manager = QPushButton("样式管理")
        self.btn_style_manager.setFixedWidth(80)
        self.btn_style_manager.setStyleSheet(button_style)

        layout.addWidget(self.lbl_chip_name)
        layout.addWidget(self.txt_chip_Maker)
        layout.addWidget(self.txt_chip_name)
        layout.addWidget(self.lbl_package)
        layout.addWidget(self.cmb_package)
        layout.addWidget(self.lbl_pin_count)
        layout.addWidget(self.spn_pin_count)
        layout.addWidget(self.frame_pin_count_detail)
        layout.addStretch()  # 添加stretch，使所有左边的控件向左靠齐
        layout.addWidget(self.btn_style_manager)

        self._update_pin_count_visibility()

    def _connect_signals(self):
        self.txt_chip_name.textChanged.connect(self.chip_name_changed.emit)
        self.txt_chip_Maker.textChanged.connect(self.chip_maker_changed.emit)
        self.cmb_package.currentIndexChanged.connect(self._on_package_changed)
        self.spn_pin_count.valueChanged.connect(self.pin_count_changed.emit)
        self.btn_style_manager.clicked.connect(self.style_manager_clicked.emit)

        self.spn_top.valueChanged.connect(self._emit_pin_count_detail)
        self.spn_left.valueChanged.connect(self._emit_pin_count_detail)
        self.spn_bottom.valueChanged.connect(self._emit_pin_count_detail)
        self.spn_right.valueChanged.connect(self._emit_pin_count_detail)

    def _on_package_changed(self, index):
        package_type = PackageType(self.cmb_package.currentText())
        self._update_pin_count_visibility()
        self.package_type_changed.emit(package_type.value)
        self._emit_pin_count_detail()

    def _update_pin_count_visibility(self):
        package_type = PackageType(self.cmb_package.currentText())
        if package_type.is_four_row:
            self.lbl_pin_count.hide()
            self.spn_pin_count.hide()
            self.frame_pin_count_detail.show()
        else:
            self.lbl_pin_count.show()
            self.spn_pin_count.show()
            self.frame_pin_count_detail.hide()

    def _emit_pin_count_detail(self):
        detail = PinCount(
            left=self.spn_left.value(),
            top=self.spn_top.value(),
            right=self.spn_right.value(),
            bottom=self.spn_bottom.value()
        )
        self.pin_count_detail_changed.emit(detail)

    def get_chip_model(self) -> ChipModel:
        package_type = PackageType(self.cmb_package.currentText())
        model = ChipModel(
            name=self.txt_chip_name.text(),
            maker=self.txt_chip_Maker.text(),
            package_type=package_type,
            pin_count=self.spn_pin_count.value()
        )
        if package_type.is_four_row:
            model.pin_count_detail = PinCount(
                left=self.spn_left.value(),
                top=self.spn_top.value(),
                right=self.spn_right.value(),
                bottom=self.spn_bottom.value()
            )
            model.pin_count = model.pin_count_detail.total
        return model

    def set_chip_model(self, model: ChipModel):
        self.txt_chip_name.setText(model.name)
        self.txt_chip_Maker.setText(model.maker)
        index = self.cmb_package.findText(model.package_type.value)
        if index >= 0:
            self.cmb_package.setCurrentIndex(index)
        if model.package_type.is_four_row:
            self.spn_left.setValue(model.pin_count_detail.left)
            self.spn_top.setValue(model.pin_count_detail.top)
            self.spn_right.setValue(model.pin_count_detail.right)
            self.spn_bottom.setValue(model.pin_count_detail.bottom)
        else:
            self.spn_pin_count.setValue(model.pin_count)

    def set_chip_name(self, name: str):
        self.txt_chip_name.setText(name)


class MainWindow(QWidget):
    read_clicked: pyqtSignal = pyqtSignal()
    save_clicked: pyqtSignal = pyqtSignal()
    export_clicked: pyqtSignal = pyqtSignal()
    load_style_clicked: pyqtSignal = pyqtSignal()
    save_style_clicked: pyqtSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        self.setWindowTitle("芯片引脚功能图绘制工具")
        self.setMinimumSize(1200, 800)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.info_bar = InfoBarWidget()
        main_layout.addWidget(self.info_bar)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(5)

        self.svg_viewer = SvgViewerWidget()
        self.svg_viewer.setMinimumWidth(700)
        content_layout.addWidget(self.svg_viewer, 3)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.pin_list_widget = PinListWidget()
        self.pin_list_widget.setMinimumWidth(350)
        right_layout.addWidget(self.pin_list_widget)

        file_ops_frame = QFrame()
        file_ops_frame.setFrameShape(QFrame.StyledPanel)
        file_ops_frame.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        file_ops_layout = QHBoxLayout(file_ops_frame)
        file_ops_layout.setContentsMargins(5, 5, 5, 5)

        # 按钮样式
        button_style = """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            text-align: center;
            text-decoration: none;
            font-size: 14px;
            margin: 4px 2px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        """

        self.btn_read = QPushButton("读取")
        self.btn_read.setStyleSheet(button_style)
        self.btn_save = QPushButton("保存")
        self.btn_save.setStyleSheet(button_style)
        self.btn_export = QPushButton("输出图片")
        self.btn_export.setStyleSheet(button_style)
        self.btn_load_style = QPushButton("载入样式")
        self.btn_load_style.setStyleSheet(button_style)
        self.btn_save_style = QPushButton("保存样式")
        self.btn_save_style.setStyleSheet(button_style)

        file_ops_layout.addWidget(self.btn_read)
        file_ops_layout.addWidget(self.btn_save)
        file_ops_layout.addWidget(self.btn_export)
        file_ops_layout.addStretch()
        file_ops_layout.addWidget(self.btn_load_style)
        file_ops_layout.addWidget(self.btn_save_style)

        right_layout.addWidget(file_ops_frame)

        content_layout.addWidget(right_panel, 1)

        main_layout.addLayout(content_layout)

    def _setup_connections(self):
        self.btn_read.clicked.connect(self.read_clicked.emit)
        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_export.clicked.connect(self.export_clicked.emit)
        self.btn_load_style.clicked.connect(self.load_style_clicked.emit)
        self.btn_save_style.clicked.connect(self.save_style_clicked.emit)

    def get_info_bar(self) -> InfoBarWidget:
        return self.info_bar

    def get_pin_list_widget(self) -> PinListWidget:
        return self.pin_list_widget

    def get_svg_viewer(self) -> SvgViewerWidget:
        return self.svg_viewer

    def get_chip_model(self) -> ChipModel:
        return self.info_bar.get_chip_model()

    def set_chip_model(self, model: ChipModel):
        self.info_bar.set_chip_model(model)
