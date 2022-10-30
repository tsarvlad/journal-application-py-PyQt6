
from datetime import datetime
import re
import random
import hashlib
import sys

from matplotlib.backends.backend_qtagg import (FigureCanvasQTAgg as FigureCanvas,
                                               NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Qt5Agg')

import seaborn as sns
import pandas as pd

from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QMessageBox, QFontDialog, QDialog
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import QDate
from PyQt6 import QtCore


from uidesign import Ui_MainWindow


class ApplicationWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.show()
        self.setWindowIcon(QIcon("images\Hopstarter-Book-Starbucks-Diary-Book.ico"))
        self.setWindowTitle("SIndex")

        #set default page to first
        self.tabWidget.setCurrentIndex(0)

        #enabling menu bar
        self.enable_menu_functionality()

        #read pandas
        self.pandas_read()

        #Add new tab (1)
        self.textEdit.setTabChangesFocus(True)

        self.textEdit.textChanged.connect(self.words_counter)
        self.pushButton.clicked.connect(self.submit)

        self.points_manager()

        #submit button will be clickable from enter
        self.pushButton.setDefault(True)
    

        #Chart tab (2)
        #matplotlib
        self.matplotlibCanvas()
        #automatically runs chart
        self.plotOnCanvas()


        #Page tab(3)
        self.pushButton_list.clicked.connect(self.try_password)        
        self.lineEdit_listPassword.textChanged.connect(self.lock)
        self.calendarWidget.selectionChanged.connect(self.date_selection)
        self.pushButton_random.clicked.connect(self.random_selection)

        #autorization handling
        self.authorization()



    def submit(self):
        if self.textEdit.toPlainText() == '':
            ret = QMessageBox.information(self, 'Text of Message', 'Your message text is empty, do you want to submit?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret == QMessageBox.StandardButton.No:
                return False

        if not self.authentication(self.lineEdit_password.text()):
            QMessageBox.warning(self, 'Password', "Incorrect key")
            return False

        if not self.isValidValueToPointer(self.lineEdit.text()):
            QMessageBox.warning(self, 'Points', 'Incorrect format of points. It must be positive float number ')
            return False
        
        self.write(self.point_validator(self.lineEdit.text()))

        #clear text after submittion
        self.lineEdit.clear()
        self.lineEdit_password.clear()
        self.textEdit.clear()
        self.label.setText("Submitted!")
        self.label.setStyleSheet("QLabel {color:green}")

        #lock submition for this day
        self.lock_submit()

        #update chart
        self.pandas_read()
        self.plotOnCanvas()

    def write(self, points):
        with open("index.csv", "a") as file:
            file.write(
                f'{self.mm_dd_yy()},{points},"{self.textEdit.toPlainText()}"\n'
            )

    def check_submition(self):
        request = QDate.currentDate().toString('MM/dd/yy')
        response = self.index[self.index.Year == request]
        if response.index.array:
            self.lock_submit()

    def lock_submit(self):
        self.textEdit.setText("You can't submit more than one entry per day!")
        self.textEdit.setDisabled(True)
        self.spinbox.setValue(0)
        self.spinbox.setDisabled(True)
        self.lineEdit_password.setDisabled(True)
        self.lineEdit_password.clear()
        self.lineEdit.setDisabled(True)
        self.lineEdit.setPlaceholderText("")
        self.lineEdit.clear()
        self.pushButton.setDisabled(True)

    def points_manager(self):
        try:
            self.last_point = round(self.index["Points"][len(self.index.Points) -1], 2)
        except:
            self.last_point = 0
        self.lineEdit.setPlaceholderText(str(self.last_point))
        self.spinbox.valueChanged.connect(lambda: self.lineEdit.setText(str(self.point_percentage())))

    def point_percentage(self):
        number = round((self.last_point /100) * (100+self.spinbox.value()),2)
        if number < 0:
            return 0.1
        elif number > 100:
            return 100
        return number


    def point_validator(self, points):
        number = float(points)
        if number < 0:
            return 0.1
        elif number > 100:
            return 100
        return number


    def words_counter(self):
        message = self.textEdit.toPlainText()
        count = len(re.findall(r'\w+', message))
        self.label_countwords.setText(f"Number of words: {str(count)}")

    def pandas_read(self):
        try:
            index = pd.read_csv("index.csv")
            index["Difference"] = index.Points - index.Points.shift()
            index["Percentage"] = index.Difference / index.Points.shift() * 100
        except:
            with open("index.csv", 'x') as f:
                f.write('Year,Points,Reason of trendline\n')
            index = pd.read_csv("index.csv")
        self.index = index

    def plotOnCanvas(self):
        self.figure.clear()
        
        sns.lineplot(data = self.index, y = "Points", x="Year")
        sns.scatterplot(data = self.index, y = "Points", x="Year", s = 10)
        plt.yticks([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        plt.xticks([])

        self.canvas.draw()

    def matplotlibCanvas(self):
        #create a vertical and horizontal layout inside of frame (chart tab)
        self.verticalLayout_frame = QVBoxLayout(self.frame)

        self.horizontalLayout_frame = QHBoxLayout(self.frame)
        self.horizontalLayout_frame.setObjectName('horizontalLayout_frame')

        #Canvas here
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        #addCanvas
        self.horizontalLayout_frame.addWidget(self.canvas)

        self.verticalLayout_frame.addLayout(self.horizontalLayout_frame)
        self.verticalLayout_frame.addWidget(NavigationToolbar(self.canvas, self))

    def date_selection(self):
        self.clean_information()

        request = self.calendarWidget.selectedDate().toString('MM/dd/yy')

        response = self.index[self.index.Year == request]

        if response["Reason of trendline"].array.size > 0:
            self.display_entry(response)

    def random_selection(self):
        df = self.index.dropna(subset = ['Reason of trendline'])
        if list(df.index.array):
            response = df.iloc[random.randint(0, len(df)-1)]
            #.to_frame() and .transpose() is used to cast Series to correct DataFrame
            self.display_entry(response.to_frame().transpose())


    def display_entry(self, response):
        #textEdit
        text = response["Reason of trendline"].values[0]
        self.textEdit_list.setText(self.text_validation(text))

        #lineEditPoints
        self.lineEdit_points.setText(str(round(float(response.Points), 2)))

        #label_fullDate
        date = response.Year.values[0]
        date_dtm = datetime.strptime(date, "%m/%d/%y")
        date_str = date_dtm.strftime("%B %d, %Y")
        self.label_fullDate.setText(date_str)

        #lineEdit_difference
        difference = str(round(float(response.Percentage),2))+'%' if str(response.Percentage.values) != "[nan]" else ''
        self.lineEdit_difference.setText(difference)
        if float(response["Percentage"]) < 0:
            self.lineEdit_difference.setStyleSheet("QLineEdit {color:red}")
        else:
            self.lineEdit_difference.setStyleSheet("QLineEdit {color:green}")

    def try_password(self):
        if self.authentication(self.lineEdit_listPassword.text()):
            self.unlock()
        else:
            QMessageBox.warning(self, 'Password', "Incorrect key")

    def lock(self):
        self.clean_information()

        self.calendarWidget.setDisabled(True)
        self.pushButton_random.setDisabled(True)
        self.pushButton_list.setDisabled(False)
        
    def unlock(self):
        self.calendarWidget.setDisabled(False)
        self.pushButton_random.setDisabled(False)
        self.pushButton_list.setDisabled(True)

    def clean_information(self):
        self.label_fullDate.clear()
        self.lineEdit_points.clear()
        self.lineEdit_difference.clear()
        self.lineEdit_difference.setStyleSheet("")
        self.textEdit_list.clear()
    
    def enable_menu_functionality(self):
        self.menu_format()
        # self.menu_edit()
        self.menu_settings()

    def menu_edit(self):
        self.actionUndo.triggered.connect(self.textEdit.undo)
        self.actionRedo.triggered.connect(self.textEdit.redo)
        self.actionCut.triggered.connect(self.textEdit.cut)
        self.actionCopy.triggered.connect(self.textEdit.copy)
        self.actionPaste.triggered.connect(self.textEdit.paste)

    def menu_format(self):
        self.actionBold.triggered.connect(self.text_bold)
        self.actionItalics.triggered.connect(self.italic)
        self.actionUnderline.triggered.connect(self.underline)

        self.actionFont.triggered.connect(self.font_dialog)

    def menu_settings(self):
        self.actionSet_password.triggered.connect(self.setPassword)
        self.actionWipe_story.triggered.connect(self.wipe_journal_dialog)
        self.actionAbout_app.triggered.connect(self.about_window)
        
    def text_bold(self):
        font = QFont()
        font.setBold(True)
        self.textEdit.setFont(font)
    def italic(self):
        font = QFont()
        font.setItalic(True)
        self.textEdit.setFont(font)
    def underline(self):
        font = QFont()
        font.setUnderline(True)
        self.textEdit.setFont(font)
    def font_dialog(self):
        font, ok = QFontDialog.getFont()
        if ok:
            self.textEdit.setFont(font)

    def password_handling(self):
        try:
            with open('passwordhash.txt') as f:
                pass
        except:
            with open('passwordhash.txt', 'x') as f:
                f.write(hashlib.sha512(''.encode('utf-8') + ''.encode('utf-8')).hexdigest())
            QMessageBox.about(self, 'Welcome', 
             """Welcome to our application.
    In a first page you can add your entry. Notice, it's possible to 
    add only one entry per day
    In a second page you can see chart of your points.
    In a third page you can see list of your entries. 
    By default there is no password. But you can set if you 
    want in "Settings" panel of menu bar
    I hope you will have good experience!""")

        if self.default_password_checker():
            #tab1
            self.lineEdit_password.setDisabled(True)

            #tab3
            self.unlock()
            self.lineEdit_listPassword.setDisabled(True)
        
        elif not self.default_password_checker():
            #tab1
            self.lineEdit_password.setDisabled(False)

            #tab3
            self.lock()
            self.lineEdit_listPassword.setDisabled(False)

    def setPassword(self):
        self.dlg = QDialog(self)
        self.dlg.setWindowTitle("Change Password")
        self.dlg_label_old = QtWidgets.QLabel("Old Password")
        self.dlg_label_old.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.dlg_lineedit_old_password = QtWidgets.QLineEdit()
        self.dlg_lineedit_old_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        self.dlg_label_new = QtWidgets.QLabel("New Password")
        self.dlg_label_new.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.dlg_lineedit_new_password = QtWidgets.QLineEdit()
        self.dlg_lineedit_new_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
            
        pushButton = QtWidgets.QPushButton("Submit")

        vbox = QVBoxLayout()
        if not self.default_password_checker():
            vbox.addWidget(self.dlg_label_old)
            vbox.addWidget(self.dlg_lineedit_old_password)
        vbox.addWidget(self.dlg_label_new)
        vbox.addWidget(self.dlg_lineedit_new_password)
        vbox.addWidget(pushButton)

        pushButton.clicked.connect(self.apply_form)

        self.dlg.setLayout(vbox)
        self.dlg.exec()
    
        self.authorization()


    #pushButton
    def apply_form(self):
        if self.authentication(self.dlg_lineedit_old_password.text()):
            self.change_password(self.dlg_lineedit_new_password.text())
            QMessageBox.about(self, "Information", "Your password is successfully changed!")
            self.dlg.close()
        else:
            QMessageBox.warning(self, 'Password','Incorrect old key')

    def wipe_journal_dialog(self):
        if self.default_password_checker():
            self.delete_journal()
            return
            
        self.wpj = QDialog(self)
        self.wpj.setWindowTitle("Delete Journal story")
        self.wpj_label = QtWidgets.QLabel("Provide Password")
        self.wpj_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.wpj_lineedit_password = QtWidgets.QLineEdit()
        self.wpj_lineedit_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

        pushButton = QtWidgets.QPushButton("Submit")

        vbox = QVBoxLayout()

        vbox.addWidget(self.wpj_label)
        vbox.addWidget(self.wpj_lineedit_password)
        vbox.addWidget(pushButton)

        pushButton.clicked.connect(self.delete_journal_middleware)

        self.wpj.setLayout(vbox)
        self.wpj.exec()
    
    def delete_journal_middleware(self):
        if self.authentication(self.wpj_lineedit_password.text()):
            self.delete_journal()
            self.wpj.close()
        else:
            QMessageBox.warning(self, 'Password','Incorrect key')

    def delete_journal(self):
        confirmation = QMessageBox.warning(self, "Delete journal", "Are you sure you want to delete journal? Action can't be undone, files can't be restored, ", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirmation == QMessageBox.StandardButton.Yes:
            with open("index.csv", 'w') as f:
                f.write('Year,Points,Reason of trendline\n')
            #just for making lineedit on first page equal not to previous value
            #I DON"T  KNOW HOW TO SOLVE THAT!
        else:
            return

    def about_window(self):
        QMessageBox.about(self, "About App", "This is simple submit-diary application with PyQt6. In development since 10/25/2022.")

    def authorization(self):
        self.password_handling()
        self.check_submition()


    @staticmethod
    def default_password_checker():
        with open('passwordhash.txt') as f:
                hashed_password = f.readline()
        if hashed_password == hashlib.sha512(''.encode('utf-8') + ''.encode('utf-8')).hexdigest():
            return True
        return False

    @staticmethod
    def change_password(string):
        password = salt = string
        hashed_password = hashlib.sha512(password.encode(
            'utf-8') + salt.encode('utf-8')).hexdigest()
        with open('passwordhash.txt', 'w') as f:
            f.write(hashed_password)

    @staticmethod
    def authentication(string):
        password = salt = string
        hashed_try = hashlib.sha512(password.encode(
            'utf-8') + salt.encode('utf-8')).hexdigest()
        with open('passwordhash.txt') as f:
            password = f.readline()
        if hashed_try == password:
            return True
        return False

    @staticmethod
    def text_validation(text):
        try:
            if str(text) == 'nan':
                return "-"
        except:
            return "-"
        return text

    @staticmethod
    def isValidValueToPointer(points):
        try:
            float(points)
            return True
        except:
            return False

    @staticmethod
    def mm_dd_yy():
        ts = datetime.timestamp(datetime.now())
        date_time = datetime.fromtimestamp(ts)
        return date_time.strftime("%m/%d/%y")



app = QApplication(sys.argv)
w = ApplicationWindow()

app.exec()




