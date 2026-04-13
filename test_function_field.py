from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from ui.pin_list_widget import FunctionField
from models.pin_model import PinFunction

if __name__ == '__main__':
    app = QApplication([])
    
    # 创建一个FunctionField实例
    func = PinFunction(name="Test Function")
    field = FunctionField(0, 0, func)
    
    # 创建一个窗口来显示它
    window = QWidget()
    layout = QVBoxLayout(window)
    layout.addWidget(field)
    window.show()
    
    app.exec_()