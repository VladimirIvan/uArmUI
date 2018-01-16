try:
    from PySide import QtCore, uic, QtWidgets
except:
    from PyQt5 import QtCore, uic, QtWidgets
    
class DocumentPropertiesDialog(QtWidgets.QDialog):
    def __init__(self, parent = None, doc=None):
        self.doc=doc
        super(DocumentPropertiesDialog, self).__init__(parent)
        uic.loadUi('ui/documentproperties.ui', self)
        self.comboMode.currentIndexChanged.connect(self.modeChanged)
        self.loadProperties()

    def modeChanged(self, i):
        if i == 0:
            self.label_5.hide()
            self.doubleLift.hide()
        else:
            self.label_5.show()
            self.doubleLift.show()

    def loadProperties(self):
        if self.doc.mode==1:
            self.comboMode.setCurrentIndex(0)
            self.modeChanged(0)
        else:
            self.comboMode.setCurrentIndex(1)
            self.modeChanged(1)
        self.doubleHeight.setValue(self.doc.height)
        self.doubleF.setValue(self.doc.F)
        self.doubleF0.setValue(self.doc.F0)
        self.doubleZoffset.setValue(self.doc.zoffset)
        self.doubleLift.setValue(self.doc.lift)

    def storeProperties(self):
        if self.comboMode.currentIndex() == 0:
            self.doc.mode=1
        else:
            self.doc.mode=3
        self.doc.height = self.doubleHeight.value()
        self.doc.F = self.doubleF.value()
        self.doc.F0 = self.doubleF0.value()
        self.doc.zoffset = self.doubleZoffset.value()
        self.doc.lift = self.doubleLift.value()

    @staticmethod
    def getProperties(parent = None, doc=None):
        dialog = DocumentPropertiesDialog(parent, doc)
        result = dialog.exec_()
        if result:
            dialog.storeProperties()
            return True
        return False