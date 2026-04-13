from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView, QGraphicsScene, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QBuffer, QIODevice
from PyQt5.QtGui import QPainter
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer

class SvgViewerWidget(QWidget):
    canvas_size_changed = pyqtSignal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._scale = 1.0
        self._min_scale = 0.1
        self._max_scale = 5.0
        self._canvas_width = 1280
        self._canvas_height = 960

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建标题栏布局
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(5, 0, 5, 0)
        
        self.lbl_title = QLabel("显示绘制区")
        self.lbl_title.setStyleSheet("background-color: #fce8e8; padding: 5px;")
        
        # 添加画布大小设置
        self.lbl_canvas_size = QLabel("画布大小:")
        self.lbl_canvas_size.setStyleSheet("background-color: #fce8e8; padding: 5px;")
        self.lbl_canvas_size.setAlignment(Qt.AlignRight)
        
        self.txt_width = QLineEdit("1600")
        self.txt_width.setFixedHeight(20)  # 设置固定高度为30像素
        #self.txt_width.setStyleSheet("background-color: #ffffff; padding: 2px; border: 1px solid #000000;")
        self.txt_width.setStyleSheet("background-color: #e0ffe0; ")
        self.txt_width.setFixedWidth(80)  # 设置为6位字符长度
        self.txt_width.setAlignment(Qt.AlignCenter)
        
        self.lbl_x = QLabel("X")
        self.lbl_x.setStyleSheet("background-color: #fce8e8; padding: 5px;")
        
        self.txt_height = QLineEdit("1024")
        self.txt_height.setFixedHeight(20)  # 设置固定高度为30像素
        #self.txt_height.setStyleSheet("background-color: #ffffff; padding: 2px; border: 1px solid #000000;")
        self.txt_height.setStyleSheet("background-color: #deffef; ")
        self.txt_height.setFixedWidth(80)  # 设置为6位字符长度
        self.txt_height.setAlignment(Qt.AlignCenter)
        
        self.btn_apply = QPushButton("应用")
        self.btn_apply.setStyleSheet("padding: 2px 8px;")
        self.btn_apply.clicked.connect(self._on_apply_clicked)
        
        # 添加芯片图大小标签
        self.lbl_size = QLabel("大小: 0x0")
        self.lbl_size.setStyleSheet("background-color: #fce8e8; padding: 5px;")
        self.lbl_size.setAlignment(Qt.AlignRight)
        
        # 添加放大百分比标签
        self.lbl_zoomtext = QLabel("缩放:")
        self.lbl_zoomtext.setStyleSheet("background-color: #fce8e8; padding: 5px;")
        self.lbl_zoomtext.setAlignment(Qt.AlignRight)
        self.lbl_zoom = QLabel("100%")
        self.lbl_zoom.setStyleSheet("background-color: #fce8e8; padding: 5px;")
        self.lbl_zoom.setAlignment(Qt.AlignRight)
        
        title_layout.addWidget(self.lbl_title)
        title_layout.addStretch()
        title_layout.addWidget(self.lbl_canvas_size)
        title_layout.addWidget(self.txt_width)
        title_layout.addWidget(self.lbl_x)
        title_layout.addWidget(self.txt_height)
        title_layout.addWidget(self.btn_apply)
        title_layout.addWidget(self.lbl_size)
        title_layout.addWidget(self.lbl_zoomtext)
        title_layout.addWidget(self.lbl_zoom)
        
        # 创建标题栏容器
        title_widget = QWidget()
        title_widget.setStyleSheet("background-color: #fce8e8;")
        title_widget.setLayout(title_layout)
        
        main_layout.addWidget(title_widget)

        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setRenderHint(QPainter.TextAntialiasing)
        self.graphics_view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.graphics_view.setFrameShape(QGraphicsView.NoFrame)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.wheelEvent = self._on_wheel

        self.scene = QGraphicsScene()
        self.graphics_view.setScene(self.scene)

        main_layout.addWidget(self.graphics_view)

    def _on_wheel(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self._scale *= 1.1
        else:
            self._scale /= 1.1

        self._scale = max(self._min_scale, min(self._max_scale, self._scale))
        self._update_view()

    def _update_view(self):
        self.graphics_view.resetTransform()
        self.graphics_view.scale(self._scale, self._scale)
        # 更新放大百分比标签
        zoom_percent = int(self._scale * 100)
        self.lbl_zoom.setText(f"{zoom_percent}%")

    def load_svg(self, svg_content: str):
        self._svg_content = svg_content
        self.scene.clear()
        
        if svg_content:
            print(f"Loading SVG content, length: {len(svg_content)}")
            try:
                # 直接使用QSvgRenderer的构造函数加载SVG内容
                renderer = QSvgRenderer(svg_content.encode('utf-8'))
                print(f"SVG renderer valid: {renderer.isValid()}")
                if renderer.isValid():
                    # 创建QGraphicsSvgItem并设置renderer
                    self._svg_item = QGraphicsSvgItem()
                    self._svg_item.setSharedRenderer(renderer)
                    self.scene.addItem(self._svg_item)
                    print(f"SVG item added to scene")
                    # 调整场景大小以适应SVG
                    size = renderer.defaultSize()
                    print(f"SVG default size: {size.width()}x{size.height()}")
                    # 如果默认大小为0x0，设置一个默认大小
                    if size.width() == 0 or size.height() == 0:
                        size.setWidth(800)
                        size.setHeight(600)
                    self.scene.setSceneRect(0, 0, size.width(), size.height())
                    self._update_view()
                else:
                    print("Invalid SVG content")
                    # 添加一个文本项来显示错误
                    self.scene.addText("Invalid SVG content")
            except Exception as e:
                print(f"Error loading SVG: {e}")
                # 添加一个文本项来显示错误
                self.scene.addText(f"Error loading SVG: {e}")

    def set_svg_content(self, svg_content: str):
        self.load_svg(svg_content)

    def clear(self):
        self.scene.clear()
        self._svg_item = None
        self._svg_content = ""
    
    def _on_apply_clicked(self):
        """处理应用按钮点击事件"""
        try:
            # 获取用户输入的宽度和高度
            width = int(self.txt_width.text())
            height = int(self.txt_height.text())
            
            # 验证输入是否有效（大于0）
            if width > 0 and height > 0:
                # 更新内部变量
                self._canvas_width = width
                self._canvas_height = height
                # 发出信号通知主程序
                self.canvas_size_changed.emit(width, height)
        except ValueError:
            # 输入不是有效的整数，忽略
            pass
    
    def set_chip_size(self, width: float, height: float):
        """设置芯片图大小"""
        self.lbl_size.setText(f"内容大小: {int(width)}x{int(height)}")
