#!/usr/bin/python

import sys, os

try:
    from PySide import QtCore, uic, QtWidgets
except:
    from PyQt5 import QtCore, uic, QtWidgets

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from Device import *
from DocumentWindow import *
from CommandDialog import *

class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        uic.loadUi('ui/mainwindow.ui', self)
        self.menuDevice.aboutToShow.connect(self.handleUpdateDevices)
        self.menuPort.triggered.connect(self.selectPort)
        self.actionConnect.triggered.connect(self.connect)
        self.actionDisconnect.triggered.connect(self.disconnect)
        self.actionCommand.triggered.connect(self.command)
        self.actionConnect.setEnabled(False)
        self.actionDisconnect.setEnabled(False)
        self.actionCommand.setEnabled(False)
        self.ports={}
        self.device=None
        self.connectTimer = QtCore.QTimer(self)
        self.connectTimer.timeout.connect(self.updateStatus)
        self.settings = QtCore.QSettings('uArm','uArmUI')
        self.port=self.settings.value("Port")
        self.handleUpdateDevices()
        self.selectPort()
        self.documentCount=0

        self.actionNew.triggered.connect(self.newDocument)
        self.actionLoad.triggered.connect(self.openDocument)
        self.actionSave.triggered.connect(self.saveDocument)
        self.actionSaveAs.triggered.connect(self.saveDocumentAs)

    def command(self):
        wnd=self.mdiArea.activeSubWindow()
        if wnd:
            doc=wnd.widget().doc
            CommandDialog.command(self,doc, self.device)


    def newDocument(self):
        self.documentCount+=1
        sub = QtWidgets.QMdiSubWindow()
        sub.setWidget(DocumentWindow(Document(),self,sub))
        sub.setWindowTitle("Untitled"+str(self.documentCount))
        self.mdiArea.addSubWindow(sub)
        sub.show()
        return sub

    def openDocument(self):
        dir=self.settings.value('OpenFilePath')
        (filename,ftype) = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', dir,"All supported files (*.uarm *.plt *.svg);;uArmUI plot files (*.uarm);;HP plotter plot files (*.plt);;SVG vector graphics (*.svg)")
        if filename:
            self.settings.setValue('OpenFilePath',os.path.dirname(str(filename)))
            self.documentCount+=1
            sub = QtWidgets.QMdiSubWindow()
            sub.setWidget(DocumentWindow(Document.load(filename),self,sub))
            sub.setWindowTitle(filename)
            self.mdiArea.addSubWindow(sub)
            sub.show()

    def saveDocument(self):
        if self.mdiArea.activeSubWindow():
            doc=self.mdiArea.activeSubWindow().widget().doc
            if doc.filename=='' or doc.filename[-5:]!='.uarm':
                self.saveDocumentAs()
            else:
                doc.save()

    def saveDocumentAs(self):
        wnd=self.mdiArea.activeSubWindow()
        if wnd:
            doc=wnd.widget().doc
            dir=self.settings.value('SaveFilePath')
            (filename,ftype) = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file as', dir,"uArmUI plot files (*.uarm)")
            if filename:
                if filename[-5:]!='.uarm':
                    filename+='.uarm'
                self.settings.setValue('SaveFilePath',os.path.dirname(str(filename)))
                doc.filename=filename
                doc.save()
                wnd.setWindowTitle(filename)

    def updateStatus(self):
        if self.device:
            txt='%s Device: %s %s, SW: %s, API: %s'%(self.port, self.device.getDeviceName(), self.device.getHWVersion(), self.device.getSWVersion(), self.device.getAPIVersion())
            self.statusbar.showMessage(txt)
            self.connectTimer.stop()
        else:
            self.statusbar.showMessage(self.port)

    def connect(self):
        self.device = Device(self.port)
        if self.device.isConnected():
            self.actionConnect.setEnabled(False)
            self.actionDisconnect.setEnabled(True)
            self.actionCommand.setEnabled(True)
            self.connectTimer.start(2000)
        else:
            self.device = None

    def disconnect(self):
        self.device.disconnect()
        self.device = None
        self.selectPort()
        self.actionDisconnect.setEnabled(False)
        self.actionCommand.setEnabled(False)

    def handleUpdateDevices(self):
        p=listDevices()
        i=1
        self.menuPort.clear()
        ag = QtWidgets.QActionGroup(self, exclusive=True)
        for port in p:
            menu=ag.addAction(QtWidgets.QAction(port, self, checkable=True))
            self.menuPort.addAction(menu)
            if port==self.port:
                menu.setChecked(True)
            self.ports[port]=menu

    def selectPort(self):
        self.actionConnect.setEnabled(False)
        for p, menu in self.ports.items():
            if menu.isChecked():
                self.port = p
                self.statusbar.showMessage(self.port)
                self.settings.setValue("Port", self.port)
                if self.device == None:
                  self.actionConnect.setEnabled(True)

    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()

    def about(self):
        QtWidgets.QMessageBox.about(self, 'About','uArm UI')

qApp = QtWidgets.QApplication(sys.argv)

aw = ApplicationWindow()
aw.setWindowTitle('uArmUI')
aw.show()
sys.exit(qApp.exec_())
