from PyQt5.QtWidgets import QApplication, QWidget, QLabel

if __name__ == '__main__':
    print('Starting test...')
    app = QApplication([])
    print('App created')
    
    window = QWidget()
    print('Window created')
    
    label = QLabel('Hello')
    print('Label created')
    
    window.show()
    print('Window shown')
    
    app.exec_()