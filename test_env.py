print('Hello, World!')
import sys
print(f'Python version: {sys.version}')
try:
    from PyQt5.QtWidgets import QApplication
    print('PyQt5 imported successfully')
except Exception as e:
    print(f'Error importing PyQt5: {e}')