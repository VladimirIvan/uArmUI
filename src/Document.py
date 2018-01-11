import math
import numpy as np
import pickle

def distance(A, B):
    return math.sqrt(math.pow(A[0]-B[0],2) + math.pow(A[1]-B[1],2))

def length(segs):
    d=0.0
    for i in range(1,len(segs)):
        d=d+distance(segs[i-1], segs[i])
    return d

def maxLen(segs):
    imax=0
    dmax=0.0
    for i in range(len(segs)):
        d=length(segs[i])
        if d>dmax:
            dmax=d
            imax=i
    return imax

def checkCoords(x,y,z):
    if x<132.0 or x>300.0 or y<-200.0 or y>200.0 or z<-100.0:
        return False
    return True

def gCodeMove(x,y,z,F):
    return 'G0 X%.2f Y%.2f Z%.2f F%.2f\n'%(x, y, z, F)

def gCodeBurn(x,y,z,F):
    return 'G1 X%.2f Y%.2f Z%.2f F%.2f\n'%(x, y, z, F)

class Document:
    def __init__(self):
        self.segs=[]
        self.gcode=[]
        self.computeDistances()
        self.height=0.0
        self.F=100
        self.F0=1000
        self.zoffset=81.5
        self.lift=10.0
        self.filename=''
        self.mode=1

    def sortSegs(self, dir=0):
        n = len(self.segs)
        if n<=1:
            return [0]
        a=np.zeros(n)
        if dir==0:
            for i in range(n):
                a[i]=self.segs[i][0][0]
            return np.argsort(a)
        elif dir==1:
            for i in range(n):
                a[i]=-self.segs[i][0][0]
            return np.argsort(a)
        elif dir==2:
            for i in range(n):
                a[i]=self.segs[i][0][1]
            return np.argsort(a)
        elif dir==3:
            for i in range(n):
                a[i]=-self.segs[i][0][1]
            return np.argsort(a)

    def joinSegsDist(self, i, j, D):
        self.segs[i] = self.segs[i]+self.segs[j][1:]
        del self.segs[j]
        D[i]=D[j]
        D[i,i]=np.inf
        D=np.delete(D,j,0)
        D=np.delete(D,j,1)

    def closestSeg(self, ii, toCheck):
        imin=toCheck[0]+1
        dmin=np.inf
        for i in range(0,len(toCheck)):
            d1=distance(self.segs[ii][-1],self.segs[toCheck[i]][0])
            d2=distance(self.segs[ii][-1],self.segs[toCheck[i]][-1])
            if d1<dmin:
                dmin=d1
                imin=toCheck[i]+1
            if d2<dmin:
                dmin=d2
                imin=-(toCheck[i]+1)
        return imin

    def sortGreedy(self):
        toCheck=list(range(len(self.segs)))
        ret=[]
        temp=maxLen(self.segs)+1
        while True:
            toCheck.remove(abs(temp)-1)
            ret.append(temp)
            if len(toCheck)==0:
                break
            temp=closestSeg(abs(temp)-1, self.segs, toCheck)
            if temp<0:
                self.segs[abs(temp)-1].reverse()
        for i in range(len(ret)):
            ret[i]=abs(ret[i])-1
        return ret

    def joinSegs(self):
        n=len(self.segs)
        D=np.ones((n,n))*np.inf
        for i in range(0,n):
            for j in range(0,n):
                if i!=j:
                    D[i,j] = distance(self.segs[i][-1], self.segs[j][0])
        while True:
            a = (D.min(1)==0)
            if a.any()==False:
                break
            i=a.argmax()
            j=D.argmin(1)[i]
            (self.segs,D)=joinSegsDist(i,j,self.segs,D)
        return D

    def importPLYraw(self, filename):
        self.filename=filename
        f=open(filename)
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

    def orderSegments(self, order=0):
        segs=loadSegs(filename)
        D=joinSegs(segs)
        if order<=0:
            segOrd=sortGreedy(segs)
        elif order==1:
            segOrd=sortSegs(segs,0)
        elif order==2:
            segOrd=sortSegs(segs,1)
        elif order==3:
            segOrd=sortSegs(segs,2)
        elif order==4:
            segOrd=sortSegs(segs,3)
        else:
            raise 'Unknown order!'

        dist=0.0
        bdist=0.0
        ret=[]
        for i in range(len(segOrd)):
            ret.append(self.segs[segOrd[i]])
        self.computeDistances()
        self.segs = ret

    def computeDistances(self):
        self.travelDist=0.0
        self.cutDist=0.0
        for i in range(len(self.segs)):
            self.cutDist+=length(self.segs[i])
            if i>0:
                self.travelDist+=distance(self.segs[i-1][-1], self.segs[i][0])

    def updateGcode(self):
        self.gcode = []
        z=self.height+self.zoffset
        for i in range(len(self.segs)):
            v=self.segs[i][0]
            if not checkCoords(v[0], v[1], z):
                raise('Invalid coordinates (%f, %f, %f)'%(v[0], v[1], z))
            self.gcode.append(gCodeMove(v[0], v[1], z, self.F0))
            for j in range(1,len(self.segs[i])):
                v=self.segs[i][j]
                if not checkCoords(v[0], v[1], z):
                    raise('Invalid coordinates (%f, %f, %f)'%(v[0], v[1], z))
                self.gcode.append(gCodeBurn(v[0], v[1], z, self.F))
        v=self.segs[-1][0]
        if not checkCoords(v[0], v[1], z):
            raise('Invalid coordinates (%f, %f, %f)'%(v[0], v[1], z))
        self.gcode.append(gCodeMove(v[0], v[1], z, self.F0))

    def updateGcodeDraw(self):
        self.gcode = []
        z=self.height+self.zoffset
        for i in range(len(self.segs)):
            v=self.segs[i][0]
            if not checkCoords(v[0], v[1], z):
                raise('Invalid coordinates (%f, %f, %f)'%(v[0], v[1], z))
            if not checkCoords(v[0], v[1], z):
                raise('Invalid coordinates (%f, %f, %f)'%(v[0], v[1], z+self.lift))
            self.gcode.append(gCodeMove(v[0], v[1], z+self.lift, self.F0))
            self.gcode.append(gCodeMove(v[0], v[1], z, self.F0))
            for j in range(1,len(self.segs[i])):
                v=self.segs[i][j]
                if not checkCoords(v[0], v[1], z):
                    raise('Invalid coordinates (%f, %f, %f)'%(v[0], v[1], z))
                self.gcode.append(gCodeMove(v[0], v[1], z, self.F))
            v=self.segs[i][-1]
            if not checkCoords(v[0], v[1], z):
                raise('Invalid coordinates (%f, %f, %f)'%(v[0], v[1], z))
            self.gcode.append(gCodeMove(v[0], v[1], z+self.lift, self.F))

    def save(self, filename=None):
        if filename == None:
            filename=self.filename
        pickle.dump(self,open(filename,'w'))

    @staticmethod
    def load(filename):
        if filename[-4:]=='.plt':
            ret=Document()
            ret.importPLYraw(filename)
        elif filename[-5:]=='.uarm':
            ret=pickle.load(open(filename))
            ret.filename=filename
        return ret
