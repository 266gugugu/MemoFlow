# main.py
import sys
from PyQt6.QtWidgets import QApplication
from src.windows import MainWindow


def main():
    app = QApplication(sys.argv)

    # 【核心修复】关键设置！
    # 设置为 False，意味着即使所有窗口都关闭（隐藏）了，程序也不会退出
    # 只有显式调用 app.quit() 才会真正退出
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
