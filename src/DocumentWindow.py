try:
    from PySide import QtCore, uic, QtWidgets
except:
    from PyQt5 import QtCore, uic, QtWidgets

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import collections as mc
from matplotlib import transforms
from matplotlib.widgets import RectangleSelector
import numpy as np
import os
import types

from SnaptoCursor import *
from DocumentPropertiesDialog import *
from Document import *
from ObjectWidget import *

def getArc(d):
    th0=np.arcsin(105.0/d)
    th=np.linspace(-th0,th0,30)
    return np.matrix([np.cos(th)*d,np.sin(th)*d]).transpose().tolist()


class DocumentWindow(QtWidgets.QMainWindow):
    def __init__(self, doc, parent=None, mdi=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        uic.loadUi('ui/document.ui', self)

        self.mdi = mdi
        self.parent = parent
        self.fig = Figure((400, 400))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.centralwidget)
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        self.canvas.updateGeometry()
        self.grid = [0,0,20,20]

        self.mpl_toolbar = NavigationToolbar(self.canvas, self.centralwidget)

        self.verticalLayout.addWidget(self.canvas)
        self.verticalLayout.addWidget(self.mpl_toolbar)

        self.plt = self.fig.gca()
        self.doc = doc
        self.updatePlot()

        self.actionProperties.triggered.connect(self.updateProperties)
        self.actionImport.triggered.connect(self.importObject)

        #self.cur = Cursor(self.plt, useblit=True)
        self.cursor = SnaptoCursor(self, useblit=True)
        self.selector = RectangleSelector(self.plt, self.onselect, drawtype='box',
            rectprops=dict(facecolor='white', edgecolor = 'black', alpha=0.5, fill=False, linestyle='--'), 
            useblit=True, button=3, 
            state_modifier_keys={'center':'None' ,'None':'space', 'clear':'escape', 'square':'shift'})


    def importObject(self):
        dir=self.parent.settings.value('OpenFilePath')
        (filename,ftype) = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', dir,"All supported files (*.plt *.svg);;HP plotter plot files (*.plt);;SVG vector graphics (*.svg)")
        if filename:
            self.parent.settings.setValue('OpenFilePath',os.path.dirname(str(filename)))
            self.doc.importObject(str(filename),str(filename)[-3:])
            self.updatePlot()
            self.canvas.draw()
            self.doc.objects[-1].select()

    def updateProperties(self):
        DocumentPropertiesDialog.getProperties(self, self.doc)

    def trans(self):
        return transforms.Affine2D().rotate_deg(90)+self.plt.transData

    def plot(self, lines, colors=[0, 0, 0, 1], linestyles='solid', linewidths=1.0, owner=None):
        lc = mc.LineCollection(lines, colors=colors, linestyles=linestyles, linewidths=linewidths)
        
        self.plt.add_collection(lc)
        if owner:
            objectTrans=transforms.Affine2D(owner.transform)
            dataTrans=lc.get_transform()
            lc.set_transform(transforms.CompositeGenericTransform(objectTrans,dataTrans))
            ObjectWidget(lc,owner,self)

    def getGrid(self):
        ret=[]
        pos_ = np.array([0,-105])
        orig = np.array(self.grid)
        start = np.ceil((pos_-orig[0:1])/orig[2:3])*orig[2:3]+orig[0:1]
        for x in np.arange(start[0], 297, orig[2]):
            ret.append([[x,-105],[x,105]])
        for y in np.arange(start[1], 105, orig[3]):
            ret.append([[0,y],[297,y]])
        return ret

    def plotSheet(self):
        self.plot(self.getGrid(), colors=[0.92,0.92,0.92,1], linestyles='-', linewidths=1)
        self.plot([ [[0, -105],[0,105],[297,105],[297,-105],[0, -105]],
                    getArc(125.0),
                    getArc(180.0),
                    getArc(260.0),
                    [[0,0],[260,0]]],
                    colors=[0.9,0.9,0.9,1], linestyles=':', linewidths=2)

    def updatePlot(self):
        self.plt.clear()
        self.plotSheet()
        for obj in self.doc.objects:
            self.plot(obj.segs, owner=obj)
        self.plt.autoscale()
        self.plt.axis('equal')
        self.plt.margins(0.05)

    def onselect(self, eclick, erelease):
        'eclick and erelease are matplotlib events at press and release'
        print(' startposition : (%f, %f)' % (eclick.xdata, eclick.ydata))
        print(' endposition   : (%f, %f)' % (erelease.xdata, erelease.ydata))
        print(' used button   : ', eclick.button)

    def toggle_selector(self, event):
        print(' Key pressed.')
        if event.key in ['Q', 'q'] and self.selector.active:
            print(' RectangleSelector deactivated.')
            self.selector.set_active(False)
        if event.key in ['A', 'a'] and not self.selector.active:
            print(' RectangleSelector activated.')
            self.selector.set_active(True)