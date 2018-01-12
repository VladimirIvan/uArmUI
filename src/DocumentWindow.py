try:
    from PySide import QtGui, QtCore, uic
except:
    from PyQt5 import QtGui, QtCore, uic, QtWidgets

from Document import Document
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import collections  as mc
import matplotlib as mpl
import numpy as np

def getArc(d):
    th0=np.arcsin(105.0/d)
    th=np.linspace(-th0,th0,30)
    return np.matrix([np.cos(th)*d,np.sin(th)*d]).transpose().tolist()

class DocumentWindow(QtWidgets.QMainWindow):
    def __init__(self, doc, parent=None, mdi=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        uic.loadUi('ui/document.ui', self)

        self.mdi = mdi

        self.fig = Figure((400, 400))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.centralwidget)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.updateGeometry()

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.centralwidget)

        self.verticalLayout.addWidget(self.canvas)
        self.verticalLayout.addWidget(self.mpl_toolbar)

        self.plt = self.fig.gca()
        self.doc = doc
        self.updatePlot()

        self.actionProperties.triggered.connect(self.updateProperties)

    def updateProperties(self):
        DocumentPropertiesDialog.getProperties(self, self.doc)

    def trans(self):
        return mpl.transforms.Affine2D().rotate_deg(90)+self.plt.transData

    def plot(self, lines, colors=[0, 0, 0, 1], linestyles='solid', linewidths=1.0):
        lc = mc.LineCollection(lines, colors=colors, linestyles=linestyles, linewidths=linewidths)
        #lc.set_transform(self.trans())
        self.plt.add_collection(lc)

    def plotSheet(self):
        self.plot([ [[0, -105],[0,105],[297,105],[297,-105],[0, -105]],
                    getArc(125.0),
                    getArc(180.0),
                    getArc(260.0),
                    [[0,0],[260,0]]],
                    colors=[0.8,0.8,0.8,1], linestyles='dotted', linewidths=2)

    def updatePlot(self):
        self.plt.clear()
        self.plotSheet()
        self.plot(self.doc.segs)
        self.plt.autoscale()
        self.plt.axis('equal')
        self.plt.margins(0.05)

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
