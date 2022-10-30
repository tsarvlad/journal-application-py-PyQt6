from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
import pandas as pd

class MyCalendar(QtWidgets.QCalendarWidget):
    def __init__(self, parent=None):
        QtWidgets.QCalendarWidget.__init__(self, parent)

    def paintCell(self, painter, rect, date):
        QtWidgets.QCalendarWidget.paintCell(self, painter, rect, date)

        index = pd.read_csv("index.csv")

        entries_dates = set(index.Year.array)

        if date.toString('MM/dd/yy') in entries_dates:
            painter.setBrush(QtGui.QColor(0, 200, 200, 50))
            painter.drawRect(rect)