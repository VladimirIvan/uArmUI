try:
    from PySide import QtCore, uic, QtWidgets
except:
    from PyQt5 import QtCore, uic, QtWidgets

class CommandDialog(QtWidgets.QDialog):
    def __init__(self, parent = None, doc=None, device=None):
        self.doc=doc
        self.device=device
        super(CommandDialog, self).__init__(parent)
        uic.loadUi('ui/command.ui', self)
        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect(self.updateStatus)
        self.updateStatus()
        self.device.progress = 0.0
        self.device.running=False
        self.device.pause=False
        self.device.stop=False
        self.updateTimer.start(100)
        self.pushStop.setEnabled(False)
        self.pushPause.setEnabled(False)
        self.pushStart.clicked.connect(self.commandStart)
        self.pushPause.clicked.connect(self.commandPause)
        self.pushStop.clicked.connect(self.commandStop)

    def stopCallback(self):
        self.pushStart.setEnabled(False)
        self.pushStop.setEnabled(False)
        self.pushPause.setEnabled(False)

    def commandStart(self):
        if not self.device.running:
            if self.doc.mode == 1:
                self.device.setMode(1)
            else:
                self.device.setMode(3)
            self.doc.updateGcode()    
            self.device.startPlot(self.doc.gcode,self.stopCallback)
        else:
            self.device.pause=False
        self.pushStart.setEnabled(False)
        self.pushStop.setEnabled(True)
        self.pushPause.setEnabled(True)

    def commandPause(self):
        self.pushStart.setEnabled(False)
        self.pushStop.setEnabled(False)
        self.pushPause.setEnabled(False)
        self.device.pause=True

    def commandStop(self):
        self.device.stop=True
        self.pushStart.setEnabled(False)
        self.pushStop.setEnabled(False)
        self.pushPause.setEnabled(False)

    def updateStatus(self):
        self.progressBar.setValue(int(self.device.progress))
        if self.device.running:
            if self.device.pause:
                self.pushStart.setEnabled(True)
        else:
            if self.device.stop:
                self.pushStart.setEnabled(True)
                self.device.stop=False
                self.device.pause=False
                self.device.progress=0.0

    @staticmethod
    def command(parent = None, doc=None, device=None):
        dialog = CommandDialog(parent, doc,device)
        dialog.exec_()