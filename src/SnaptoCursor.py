from matplotlib.widgets import AxesWidget
import numpy as np

class SnaptoCursor(AxesWidget):
    mousex = 0.0
    mousey = 0.0
    snapping = False

    def __init__(self, parent, useblit=False, snapDist=5, snapType={'Segments':False,'SegmentEnds':False, 'Origin':True, 'Grid':True, 'Centers':True}):
        self.parent = parent
        self.doc = self.parent.doc
        self.ax = self.parent.plt
        self.canvas = self.parent.canvas
        self.snapDist = snapDist
        self.snapType = self.setSnapType(snapType)
        SnaptoCursor.snapping = False
        
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
        self.snapToCenters = False
        if type.get('All'):
            self.snapToSegEnds = True
            self.snapToGrid = True
            self.snapToOrigin = True
            self.snapToSegs = True
            self.snapToCenters = True
        if type.get('Grid'):
            self.snapToGrid = True
        if type.get('Origin'):
            self.snapToOrigin = True
        if type.get('Segments'):
            self.snapToSegs = True
        if type.get('SegmentEnds'):
            self.snapToSegEnds = True
        if type.get('Centers'):
            self.snapToCenters = True


    def findSnapPoints(self, x, y):
        pos = self.ax.transData.transform(np.array([x, y]))
        minpt=pos
        mindist=np.inf
        if self.snapToCenters:
            for obj in self.doc.objects:
                if obj.moving: continue
                pt=obj.center
                d=np.linalg.norm(self.ax.transData.transform(pt)-pos)
                if d<mindist:
                    mindist=d
                    minpt=pt
        if self.snapToSegEnds:
            for obj in self.doc.objects:
                if obj.moving: continue
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
                if obj.moving: continue
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
        SnaptoCursor.snapping = False
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
        SnaptoCursor.mousex = x
        SnaptoCursor.mousey = y
        SnaptoCursor.snapping = vis
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