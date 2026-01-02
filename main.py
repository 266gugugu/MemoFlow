# main.py
import sys
from PyQt6.QtWidgets import QApplication
from src.presenter.main_presenter import MainPresenter

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    presenter = MainPresenter()
    presenter.start()

    # Use a variable to avoid potential syntax issues with nested calls in some environments
    ret = app.exec()
    sys.exit(ret)

if __name__ == "__main__":
    main()
