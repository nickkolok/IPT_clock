import sys, os
import csv
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import *
import math
import time, datetime

def printMinuteSecondDelta(delta):
    s = delta.total_seconds()
    return '{min:02d}:{sec:02d}'.format(min=int(s % 3600) // 60, sec=int(s % 60))

labelFontCoeff = 15
countDownFontCoeff = 20
logoSizeCoeff = 5


class App(QWidget):
    def __init__(self, states):
        super().__init__()
        self.title = 'IPT clock'
        self.state = 0
        self.prev_state = 0
        self.states = states
        # self.state.append({'name': 'Timeout', 'duration': 60})

        self.setWindowTitle(self.title)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QColor(255,255,255))
        self.setPalette(p)

        # Title of the state
        self.label = QLabel()
        self.label.setText(self.states[self.state]['name'])
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFont(QFont('Arial', self.frameGeometry().height()/labelFontCoeff))

        # Initialize the clock
        self.m = AnalogClock(self.states[self.state]['duration'], parent=self)
        self.m.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.m.show()

        # Right layout
        self.countDown = QLabel()
        self.countDown.setAlignment(Qt.AlignCenter)
        self.countDown.setFont(QFont('Arial', self.frameGeometry().height()/countDownFontCoeff))
        self.rightLayout = QVBoxLayout()

        self.rightLayout.addWidget(self.label)
        self.rightLayout.addWidget(self.m)
        self.rightLayout.addWidget(self.countDown)

        # Left layout
        self.leftLayout = QVBoxLayout()
        self.logoSFP = QLabel()
        self.logoFPT = QLabel()

        if hasattr(sys, "_MEIPASS"):  # For PyInstaller
            SFPFile = os.path.join(sys._MEIPASS, 'img1.png')
            FPTFile = os.path.join(sys._MEIPASS, 'img2.png')
        else:
            SFPFile = 'img1.png'
            FPTFile = 'img2.png'

        self.pixmapSFP = QPixmap(SFPFile)
        self.logoSFP.setPixmap(self.pixmapSFP)
        self.logoSFP.setMinimumSize(1, 1)
        self.logoSFP.installEventFilter(self)

        self.pixmapFPT = QPixmap(FPTFile)
        self.logoFPT.setPixmap(self.pixmapSFP)
        self.logoFPT.setMinimumSize(1, 1)
        self.logoFPT.installEventFilter(self)

        self.logoSFP.setMinimumWidth(self.frameGeometry().width()/logoSizeCoeff)
        self.logoFPT.setMinimumWidth(self.frameGeometry().width()/logoSizeCoeff)

        self.leftLayout.addWidget(self.logoSFP)
        self.leftLayout.addWidget(self.logoFPT)

        # Complete layout
        self.fullLayout = QHBoxLayout()
        self.fullLayout.addLayout(self.leftLayout)
        self.fullLayout.addLayout(self.rightLayout)
        self.setLayout(self.fullLayout)

        self.childWindow = ClockControls(self)  # Clock controls
        self.childWindow.generateList(states)

        # Start at first event
        self.selectState(0)

    def eventFilter(self, source, event):
        if (source is self.logoSFP and event.type() == QEvent.Resize):
            # re-scale the pixmap when the label resizes
            self.logoSFP.setPixmap(self.pixmapSFP.scaled(
                self.logoSFP.size(), Qt.KeepAspectRatio,
                Qt.SmoothTransformation))
        if (source is self.logoFPT and event.type() == QEvent.Resize):
            # re-scale the pixmap when the label resizes
            self.logoFPT.setPixmap(self.pixmapFPT.scaled(
                self.logoFPT.size(), Qt.KeepAspectRatio,
                Qt.SmoothTransformation))
        return super(QWidget, self).eventFilter(source, event)

    def selectState(self, i):
        self.childWindow.list.setCurrentItem(self.childWindow.statesList[i])

    def setEvent(self, i):
        if i < len(self.states):
            self.prev_state = self.state
            self.state = i
            print('Stepping to state {}'.format(
                self.states[self.state]['name']))

            self.m.reset(self.states[self.state]['duration'])

            self.update_state_appearance()
        else:
            self.close()

    def returnToLastState(self):
        print('Canceling mistake')
        self.state = self.prev_state

        self.childWindow.list.currentItemChanged.disconnect(self.childWindow.changeState)
        self.selectState(self.state)
        self.childWindow.list.currentItemChanged.connect(self.childWindow.changeState)

        self.m.cancelChange()

        self.update_state_appearance()

    def update_state_appearance(self):
            # Change the label for the state name
            self.label.setText(self.states[self.state]['name'])

            self.update()

    def stepEvent(self):
        i = self.state
        self.selectState(i+1)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_N:
            self.setEvent(self.state + 1)

    def resizeEvent(self, event):
        self.label.setFont(QFont('Arial', self.frameGeometry().height()/labelFontCoeff))
        self.countDown.setFont(QFont('Arial', self.frameGeometry().height()/countDownFontCoeff))

        #self.logoSFP.setMinimumWidth(self.frameGeometry().width()/logoSizeCoeff)
        self.logoFPT.setMinimumWidth(self.frameGeometry().width()/logoSizeCoeff)

class AnalogClock(QWidget):

    def __init__(self, duration, parent=None):
        super().__init__(parent)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(10)
        self.startPause = datetime.datetime.now()

        self.elapsedTimeClock = datetime.timedelta()
        self.prev_elapsed = datetime.timedelta()
        self.datestart = datetime.datetime.now()
        self.prev_datestart = self.datestart

        self.duration = duration
        self.prev_duration = self.duration
        self.paused = True
        self.overtime = False

        self.parent = parent

        self.setMinimumSize(500, 500)

    def paintEvent(self, event):
        side = int(min(self.width(), self.height()) * 0.8 / 2)
        if not(self.paused):
            self.elapsedTimeClock = (datetime.datetime.now() - self.datestart)
            self.prev_elapsed = datetime.datetime.now() - self.prev_datestart
        self.elapsedTime = self.elapsedTimeClock.total_seconds()

        # Create and start a QPainter
        self.painter = QPainter()

        self.painter.begin(self)
        self.painter.setRenderHint(QPainter.Antialiasing)

        # Put the origin at the center
        self.painter.translate(self.width() / 2, self.height() / 2)

        # Setup pen and brush
        self.painter.setPen(Qt.NoPen)
        self.painter.setBrush(QColor(0, 200, 0))

        # Do the actual painting
        self.painter.save()
        currentAngle = - 2 * math.pi * self.elapsedTime / self.duration
        if not(abs(currentAngle) > 2 * math.pi):
            self.painter.drawPie(-side, -side, 2 * side, 2 * side, 90 * 16,
                                 currentAngle * (360 / (2 * math.pi)) * 16)
            self.parent.countDown.setText(
                'Time remaining : ' + printMinuteSecondDelta(datetime.timedelta(seconds=self.duration) - self.elapsedTimeClock))
        elif 4 * math.pi > abs(currentAngle) > 2 * math.pi:
            self.overtime = True
            self.painter.drawPie(-side, -side, 2 * side,
                                 2 * side, 90 * 16, 360 * 16)
            self.painter.setBrush(QColor(200, 0, 0))
            self.painter.drawPie(-side, -side, 2 * side, 2 * side, 90 * 16,
                                 (currentAngle + 2 * math.pi) *
                                 (360 / (2 * math.pi)) * 16)
        else:
            self.painter.setBrush(QColor(200, 0, 0))
            self.painter.drawPie(-side, -side, 2 * side,
                                 2 * side, 90 * 16, 360 * 16)
        self.painter.setPen(QColor(0, 0, 0))
        self.painter.setBrush(Qt.NoBrush)
        self.painter.drawLine(QPoint(0, 0), QPoint(
            -side * math.cos(math.pi / 2 - currentAngle),
            -side * math.sin(math.pi / 2 - currentAngle)))
        self.painter.drawArc(-side, -side, 2 * side,
                             2 * side, 90 * 16, 360 * 16)
        self.painter.restore()

        self.painter.end()

    def switchPause(self):
        if self.paused:
            self.paused = False
            # Act as if there was no pause
            delta = (datetime.datetime.now() - self.startPause)
            self.datestart += delta
            self.prev_datestart += delta
        else:
            self.paused = True
            self.elapsedTimeClock = (datetime.datetime.now() - self.datestart)
            self.prev_elapsed = (datetime.datetime.now() - self.prev_datestart)
            self.startPause = datetime.datetime.now()

    def reset(self, duration):
        self.overtime = False
        self.prev_duration = self.duration
        self.prev_datestart = self.datestart
        self.duration = duration
        self.datestart = datetime.datetime.now()

        if self.paused:
            self.prev_pause = self.startPause
            self.startPause = datetime.datetime.now()

        self.elapsedTimeClock = datetime.timedelta()
        self.datestart = datetime.datetime.now()

    def cancelChange(self):
        self.elapsedTimeClock = self.prev_elapsed
        self.duration = self.prev_duration
        self.datestart = self.prev_datestart
        if self.paused:
            self.startPause = self.prev_pause

    def addMinute(self):
        self.duration += 60


class ClockControls(QDialog):
    def __init__(self, parent,):
        QDialog.__init__(self, parent)
        self.title = 'IPT clock controls'
        self.state = 0
        self.setWindowTitle(self.title)
        self.parent = parent

        self.list = QListWidget()
        self.nextButton = QPushButton()
        self.nextButton.setText('Next')
        self.pauseButton = QPushButton()
        self.pauseButton.setText('Start')
        self.moreTime = QPushButton()
        self.moreTime.setText('Add 1 minute')
        self.cancelMistake = QPushButton()
        self.cancelMistake.setText('Cancel mistake')
        self.vLayout = QVBoxLayout()
        self.vLayout.addWidget(self.list)
        self.vLayout.addWidget(self.nextButton)
        self.vLayout.addWidget(self.pauseButton)
        self.vLayout.addWidget(self.moreTime)
        self.vLayout.addWidget(self.cancelMistake)
        self.setLayout(self.vLayout)

        self.list.currentItemChanged.connect(self.changeState)
        self.pauseButton.clicked.connect(self.switchPause)
        self.nextButton.clicked.connect(self.parent.stepEvent)
        self.moreTime.clicked.connect(self.parent.m.addMinute)
        self.cancelMistake.clicked.connect(self.parent.returnToLastState)

    def generateList(self, states):
        self.statesList = []
        for state in states:
            item = QListWidgetItem('{} (duration : {} s)'.format(
                state['name'].replace('<br/>',''), state['duration']))
            self.statesList.append(item)
            self.list.addItem(item)

    def switchPause(self):
        if self.parent.m.paused:
            self.pauseButton.setText('Pause again')
        else:
            self.pauseButton.setText('Start again')
        self.parent.m.switchPause()

    def changeState(self, curr):
        new_state = self.statesList.index(curr)
        self.parent.setEvent(new_state)


if __name__ == '__main__':
    if hasattr(sys, "_MEIPASS"):  # For PyInstaller
        statesFile = os.path.join(sys._MEIPASS, 'states.csv')
    else:
        statesFile = 'states.csv'

    states = []
    with open(statesFile, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';', quotechar='|')
        for row in reader:
            states.append({'name': row[0], 'duration': float(row[1])*60})

    app = QApplication(sys.argv)
    ex = App(states)
    ex.show()
    ex.childWindow.show()
    sys.exit(app.exec_())
