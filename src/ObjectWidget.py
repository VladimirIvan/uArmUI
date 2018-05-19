from matplotlib.widgets import AxesWidget
from SnaptoCursor import *
import numpy as np

class ObjectWidget:
    def __init__(self, lc, obj, parent, useblit=False):
        self.parent = parent
        self.ax = self.parent.plt
        self.canvas = self.parent.canvas
        self.obj = obj
        self.lc = lc
        self.lc.objectWidget = self
        self.useblit = useblit

        self.connected = False
        self.background = None
        self.press = None

        self.obj.deselectCallback = self.disconnect
        self.obj.selectCallback = self.connect

    def on_press(self, event):
        if event.inaxes != self.ax: return
        if event.button != 1: return
        self.obj.moving = True
        if SnaptoCursor.snapping:
            self.press = self.obj.transform.copy(), SnaptoCursor.mousex, SnaptoCursor.mousey
        else:
            self.press = self.obj.transform.copy(), event.xdata, event.ydata
        self.lc.set_animated(self.useblit and self.canvas.supports_blit)
        self.canvas.draw()
        if self.useblit and self.canvas.supports_blit:
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.redraw()

    def connect(self):
        'connect to all the events we need'
        self.lc.set_color([0.2,0.8,0.2,1.0])
        if not self.connected:
            self.connected = True
            self.cidpress = self.canvas.mpl_connect(
                'button_press_event', self.on_press)
            self.cidrelease = self.canvas.mpl_connect(
                'button_release_event', self.on_release)
            self.cidmotion = self.canvas.mpl_connect(
                'motion_notify_event', self.on_motion)
        self.canvas.draw()

    def disconnect(self):
        'disconnect all the stored connection ids'
        self.obj.moving = False
        self.lc.set_color([0,0,0,1.0])
        if self.connected:
            self.connected=False
            self.canvas.mpl_disconnect(self.cidpress)
            self.canvas.mpl_disconnect(self.cidrelease)
            self.canvas.mpl_disconnect(self.cidmotion)
        self.canvas.draw()

    def on_motion(self, event):
        if event.inaxes != self.ax: return
        if not self.press: return
        transOrig, xpress, ypress = self.press
        trans=transOrig.copy()
        if SnaptoCursor.snapping:
            trans[0,2]=transOrig[0,2] + SnaptoCursor.mousex - xpress
            trans[1,2]=transOrig[1,2] + SnaptoCursor.mousey - ypress
        else:
            trans[0,2]=transOrig[0,2] + event.xdata - xpress
            trans[1,2]=transOrig[1,2] + event.ydata - ypress
        self.obj.move(trans)
        self.redraw()

    def on_release(self, event):
        self.press = None
        self.obj.moving = False
        self.background = None
        self.lc.set_animated(False)
        self.canvas.draw()

    def redraw(self):
        if not self.canvas.widgetlock.available(self):
            return
        if self.useblit and self.canvas.supports_blit:
            if self.background is not None:
                self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.lc)
            self.canvas.blit(self.ax.bbox)
        else:
            self.canvas.draw_idle()
