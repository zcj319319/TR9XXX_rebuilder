# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import sys
import traceback

from PyQt5 import QtWidgets

from file_opeartion.loadingPanel import LoadingPanel
app = QtWidgets.QApplication(sys.argv)

if __name__ == "__main__":
    try:
        ex = LoadingPanel()
        ex.show()
        sys.exit(app.exec_())
    except Exception as e:
        traceback.print_exc()
        sys.exit(-1)

