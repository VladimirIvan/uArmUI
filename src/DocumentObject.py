import numpy as np
from svgpathtools import svg2paths
from xml.dom.minidom import parse

class DocumentObject:
    def __init__(self):
        self.segs=[]
        self.transform = np.identity(3)
        self.updateBoundingBox()
        self.deselectCallback=None
        self.selectCallback=None

    def select(self):
        if(self.selectCallback):
            self.selectCallback()

    def deselect(self):
        if(self.deselectCallback):
            self.deselectCallback()
        
    def move(self, trans):
        for i in range(2):
            for j in range(3):
                self.transform[i,j] = trans[i,j]
        self.updateBoundingBox()

    def updateBoundingBox(self):
        self.bbox=[0,0,0,0]
        self.center=[0,0]
        for seg in self.segs:
            for pt in seg:
                ptt=self.transform*np.matrix([[pt[0],pt[1],1]]).transpose()
                self.bbox[0]=min(self.bbox[0],ptt[0])
                self.bbox[1]=min(self.bbox[1],ptt[1])
                self.bbox[2]=max(self.bbox[0],ptt[0])
                self.bbox[3]=max(self.bbox[1],ptt[1])
        self.center=[(self.bbox[0]+self.bbox[2])*0.5,(self.bbox[1]+self.bbox[3])*0.5]

    def importPLYraw(self, filename):
        f=open(self.filename)
        cmds=f.read().split(';')
        f.close()
        unit=49.6

        self.segs = []
        if cmds[0]!='IN':
            raise 'Invalid PLT file format'

        self.segs = []
        prev_pos = [0,0]
        nseg=0
        for cmd in cmds:
            if len(cmd)<2:
                continue
            c = cmd[0:2]
            if len(cmd)<=2:
                v = prev_pos
            else:
                vs = cmd[2:].split(',')
                v = [float(vs[1])/unit, 105.0-float(vs[0])/unit]
                prev_pos=v
            if c == 'IN':
                continue
            if c == 'PU':
                self.segs.append([])
                nseg=nseg+1
                self.segs[nseg-1].append(v)
            if c == 'PD':
                self.segs[nseg-1].append(v)
        self.segs=self.segs[0:-1]
        self.updateBoundingBox()

    def importSVG(self, filename):
        def pt2list(pt, trans):
            pos = trans*np.matrix([[pt.real],[pt.imag],[1]])
            pos=pos[0:2,0].transpose().tolist()[0]
            return [297.0-pos[1],105.0-pos[0]]

        def splitCurve(seg, append, trans, thr=0.01, minArc=0.001):
            if append:
                ret=[]
            else:
                ret = [pt2list(seg.point(0.0), trans)]
            t=0.0
            cur=seg.curvature(t)
            arcMax=seg.length()
            while cur>0.0 and t<1.0:
                t=min(t+max(minArc,thr/cur)/arcMax,1.0)
                if t<1.0:
                    ret.append(pt2list(seg.point(t), trans))
                    cur=seg.curvature(t)
            ret.append(pt2list(seg.point(1.0), trans))
            return ret

        def parseTrans(trans):
            if not trans:
                return np.matrix([[1,0,0],[0,1,0],[0,0,1]])
            if trans.startswith('matrix'):
                arr=np.array([float(val) for val in trans[7:-1].split(',')])
                arr=np.append(arr.reshape(3,2).transpose(),[[0,0,1]],0)
                return np.matrix(arr)
            elif trans.startswith('translate'):
                arr=[float(val) for val in trans[10:-1].split(',')]
                if len(arr)==1:
                    arr.append(0.0)
                return np.matrix([[1,0,arr[0]],[0,1,arr[1]],[0,0,1]])
            elif trans.startswith('scale'):
                arr=[float(val) for val in trans[6:-1].split(',')]
                if len(arr)==1:
                    arr.append(arr[0])
                return np.matrix([[arr[0],0,0],[0,arr[1],0],[0,0,1]])
            elif trans.startswith('rotate'):
                arr=[float(val) for val in trans[7:-1].split(',')]
                if len(arr)==1:
                    arr+=[0.,0.]
                return np.matrix([[ np.cos(arr[0]),-np.sin(arr[0]),arr[1]-arr[1]*np.cos(arr[0])+arr[2]*np.sin(arr[0])],
                                  [ np.sin(arr[0]),np.cos(arr[0]),arr[2]-arr[2]*np.cos(arr[0])-arr[1]*np.sin(arr[0])],
                                  [0,0,1]])
            elif trans.startswith('skewX'):
                arr=[float(val) for val in trans[6:-1].split(',')]
                return np.matrix([[1,np.tan(arr[0]),0],[0,1,0],[0,0,1]])
            elif trans.startswith('skewY'):
                arr=[float(val) for val in trans[6:-1].split(',')]
                return np.matrix([[1,0,0],[np.tan(arr[0]),1,0],[0,0,1]])
            else:
                raise ValueError('Wrong trnsformation value!')

        def getTransforms(filename, attributes):
            doc = parse(filename)
            ret=[]
            parents={}
            for geometryType in ['path','polyline','polygon','line','ellipse','circle','rect']:
                newParents={el.getAttribute('id'): el.parentNode for el in doc.getElementsByTagName(geometryType)}
                parents.update(newParents)
                if geometryType != 'path' and len(newParents)>0:
                    raise RuntimeError('Non-path type vector objects are not supported. Please convert all objects to paths!')
            for attr in attributes:
                id=attr.get('id')
                trans = np.matrix([[1,0,0],[0,1,0],[0,0,1]]);
                group = parents[id]
                while group!=doc:
                    trans = parseTrans(group.getAttribute('transform'))*trans
                    group = group.parentNode
                ret.append(trans)
            return ret

        paths, attributes = svg2paths(filename)
        trans = getTransforms(filename, attributes)

        self.segs=[]
        i=0
        for rpath in paths:
            for cpath in rpath.continuous_subpaths():
                subsegs=[]
                append=False
                for segment in cpath:
                    subsegs+=splitCurve(segment,append,trans[i],0.02,0.05)
                    append=True
                self.segs.append(subsegs)
            i+=1
        self.updateBoundingBox()