try:
    from PySide import QtGui, QtCore, uic
except:
    from PyQt5 import QtGui, QtCore, uic, QtWidgets

from Document import Document
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import collections  as mc
from matplotlib import transforms
import matplotlib as mpl
import numpy as np
import os

from matplotlib.widgets import AxesWidget
from matplotlib.widgets import Cursor
from matplotlib.widgets import RectangleSelector
import matplotlib.animation as animation

def getArc(d):
    th0=np.arcsin(105.0/d)
    th=np.linspace(-th0,th0,30)
    return np.matrix([np.cos(th)*d,np.sin(th)*d]).transpose().tolist()

class SnaptoCursor(AxesWidget):
    def __init__(self, parent, useblit=False, snapDist=5, snapType={'Segments':True,'SegmentEnds':False, 'Origin':True, 'Grid':True}):
        self.parent = parent
        self.doc = self.parent.doc
        self.ax = self.parent.plt
        self.canvas = self.parent.canvas
        self.snapDist = snapDist
        self.snapType = self.setSnapType(snapType)
        
        AxesWidget.__init__(self, self.ax)

        self.connect_event('motion_notify_event', self.onmove)
        self.connect_event('draw_event', self.clear)

        self.useblit = useblit and self.canvas.supports_blit

        self.cursor, = self.ax.plot(0, 0, 'rx', animated=self.useblit)
        self.cursor.set_visible(False)
        self.visible = True

        self.background = None
        self.needclear = False

    def setSnapType(self, type):
        self.snapToSegEnds = False
        self.snapToGrid = False
        self.snapToOrigin = False
        self.snapToSegs = False
        if type.get('All'):
            self.snapToSegEnds = True
            self.snapToGrid = True
            self.snapToOrigin = True
            self.snapToSegs = True
        if type.get('Grid'):
            self.snapToGrid = True
        if type.get('Origin'):
            self.snapToOrigin = True
        if type.get('Segments'):
            self.snapToSegs = True
        if type.get('SegmentEnds'):
            self.snapToSegEnds = True


    def findSnapPoints(self, x, y):
        pos = self.ax.transData.transform(np.array([x, y]))
        minpt=pos
        mindist=np.inf
        if self.snapToSegEnds:
            for obj in self.doc.objects:
                for seg in obj.segs:
                    pts = [np.array(seg[0]),np.array(seg[-1])]
                    for pt in pts:
                        ptt=((obj.transform*np.matrix([[pt[0],pt[1],1]]).transpose())[0:2,0]).transpose().tolist()[0]
                        d=np.linalg.norm(self.ax.transData.transform(ptt)-pos)
                        if d<mindist:
                            mindist=d
                            minpt=ptt
        if self.snapToSegs:
            for obj in self.doc.objects:
                for seg in obj.segs:
                    for pta in seg:
                        pt=((obj.transform*np.matrix([[pta[0],pta[1],1]]).transpose())[0:2,0]).transpose().tolist()[0]
                        d=np.linalg.norm(self.ax.transData.transform(pt)-pos)
                        if d<mindist:
                            mindist=d
                            minpt=pt
        if self.snapToOrigin:
            pts = [np.array([0,0]),
                   np.array([125,0]),
                   np.array([180,0]),
                   np.array([160,0]),]
            for pt in pts:
                d=np.linalg.norm(self.ax.transData.transform(pt)-pos)
                if d<mindist:
                    mindist=d
                    minpt=pt
        if self.snapToGrid:
            orig = np.array(self.parent.grid)
            pos_ = np.array([x, y])
            pt = np.round((pos_-orig[0:1])/orig[2:3])*orig[2:3]+orig[0:1]
            d=np.linalg.norm(self.ax.transData.transform(pt)-pos)
            if d<mindist:
                mindist=d
                minpt=pt
        return (minpt[0],minpt[1],mindist<self.snapDist)

    def onmove(self, event):
        """on mouse motion draw the cursor if visible"""
        if self.ignore(event):
            return
        if not self.canvas.widgetlock.available(self):
            return
        if event.inaxes != self.ax:
            self.cursor.set_visible(False)

            if self.needclear:
                self.canvas.draw()
                self.needclear = False
            return
        self.needclear = True
        if not self.visible:
            return
        x, y, vis, = self.findSnapPoints(event.xdata, event.ydata)
        self.cursor.set_xdata(x)
        self.cursor.set_ydata(y)
        self.cursor.set_visible(vis)
        self._update()

    def _update(self):
        if self.useblit:
            if self.background is not None:
                self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.cursor)
            self.canvas.blit(self.ax.bbox)
        else:
            self.canvas.draw_idle()
        return False

    def clear(self, event):
        """clear the cursor"""
        if self.ignore(event):
            return
        if self.useblit:
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.cursor.set_visible(False)

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

    def updateProperties(self):
        DocumentPropertiesDialog.getProperties(self, self.doc)

    def trans(self):
        return mpl.transforms.Affine2D().rotate_deg(90)+self.plt.transData

    def plot(self, linesLocal, colors=[0, 0, 0, 1], linestyles='solid', linewidths=1.0, transform=np.identity(3)):
        lines=[]
        for seg in linesLocal:
            sg=[]
            for pta in seg:
                sg.append(((transform*np.matrix([[pta[0],pta[1],1]]).transpose())[0:2,0]).transpose().tolist()[0])
            lines.append(sg)
        lc = mc.LineCollection(lines, colors=colors, linestyles=linestyles, linewidths=linewidths)
        self.plt.add_collection(lc)

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
        for objs in self.doc.objects:
            self.plot(objs.segs, transform=objs.transform)
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
