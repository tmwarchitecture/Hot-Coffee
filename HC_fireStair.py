#!/usr/bin/env python

import rhinoscriptsyntax as rs
import math

__author__ = "Timothy Williams"
__credits__ = ["Timothy Williams", "Kit Chung"]
__version__ = "0.0.2"

class Run():
    def __init__(self, Rect, deltaHeight, numRisers, thickness, runNum):
        self.Rect = Rect
        self.segments = rs.ExplodeCurves(self.Rect)
        self.deltaHeight = deltaHeight
        self.numRisers = int(numRisers)
        self.thickness = thickness
        self.riserHeight = self.deltaHeight/self.numRisers
        self.firstRiserEdge = self.segments[0]
        self.runLongEdge = self.segments[1]
        self.treadLength = rs.CurveLength(self.runLongEdge)/self.numRisers
        self.runNum = runNum+1
    def make(self):
        runVector = rs.VectorCreate(rs.CurveEndPoint(self.runLongEdge),rs.CurveStartPoint(self.runLongEdge))
        unitRunVec = rs.VectorUnitize(runVector)
        treadVec = rs.VectorScale(unitRunVec, self.treadLength) 
        riseVec = rs.VectorCreate( [0,0,self.riserHeight], [0,0,0])
        
        newPt = [rs.CurveStartPoint(self.firstRiserEdge).X, rs.CurveStartPoint(self.firstRiserEdge).Y, rs.CurveStartPoint(self.firstRiserEdge).Z-self.deltaHeight]
        
        ptList = []
        ptList.append(rs.AddPoint(newPt))
        for i in range(self.numRisers):
            tempPt = rs.CopyObject(ptList[-1])
            rs.MoveObject(tempPt, riseVec)
            ptList.append(tempPt)
            tempPt = rs.CopyObject(ptList[-1])
            rs.MoveObject(tempPt, treadVec)
            ptList.append(tempPt)
        
        #construct offset line
        undersideLine = rs.AddLine(ptList[0], ptList[-1])
        closestPtParam = rs.CurveClosestPoint(undersideLine, ptList[1])
        closestPt = rs.EvaluateCurve(undersideLine, closestPtParam)
        perpVec = rs.VectorUnitize(rs.VectorCreate(ptList[1], closestPt))
        stringerBtm = rs.MoveObject(undersideLine, rs.VectorScale(perpVec, -self.thickness))
        cnstrLine = rs.ScaleObject(stringerBtm, rs.CurveMidPoint(stringerBtm),[2,2,2]) 
        
        #line going down
        btmPt = rs.MoveObject(ptList[0], [0,0,-self.thickness]) 
        moveDir = rs.VectorCreate(ptList[2], ptList[1] )
        btmPtMoved = rs.MoveObject(rs.CopyObject(btmPt), rs.VectorScale(moveDir, 3))
        btmLineCnstr = rs.AddLine(btmPt, btmPtMoved)
        ptIntersectBtm = rs.AddPoint(rs.LineLineIntersection(btmLineCnstr, cnstrLine)[0]) #yes
        
        #top lines
        topVec = rs.VectorScale(rs.VectorCreate(ptList[-1], ptList[-2]), 5)
        topPtTemp = rs.MoveObject(rs.CopyObject(ptList[-1]), topVec)
        topLine = rs.AddLine(ptList[-1], topPtTemp)
        ptIntersectTop = rs.AddPoint(rs.LineLineIntersection(topLine, cnstrLine)[0]) #yes
        
        ptList.append(ptIntersectTop)
        ptList.append(ptIntersectBtm)
                
        stringer = rs.AddPolyline(ptList)
        closeCrv = rs.AddLine(rs.CurveStartPoint(stringer), rs.CurveEndPoint(stringer))
        
        newStringer = rs.JoinCurves([stringer, closeCrv], True)
        
        stair = rs.ExtrudeCurve(newStringer, self.firstRiserEdge)
        
        rs.CapPlanarHoles(stair)
        
        rs.DeleteObject(btmLineCnstr)
        rs.DeleteObject(btmPtMoved)
        rs.DeleteObject(btmLineCnstr)
        rs.DeleteObject(ptIntersectTop)
        rs.DeleteObject(undersideLine)
        rs.DeleteObject(topPtTemp)
        rs.DeleteObject(topLine)
        rs.DeleteObject(stringer)
        rs.DeleteObject(newStringer)
        rs.DeleteObjects(ptList)
        rs.DeleteObject(self.firstRiserEdge)
        rs.DeleteObject(self.runLongEdge)
        rs.DeleteObjects(self.segments)
        return stair
    def printStats(self):
        print "Run {}: {} risers at {}mm with {}mm tread length.".format(self.runNum, self.numRisers, self.riserHeight, self.treadLength)


def makeFireStair(rect, landingLevels):
    #HARD VARIABLES
    minGapSize = .2
    minTread = .260
    maxRiser = .180
    thickness = .3
    maxRisersInRun = 18
    maxWidth = 2.4
    scissorStair = True
    
    #(1)Determine Run Direction
    rs.SimplifyCurve(rect)
    rectSegments = rs.ExplodeCurves(rect)
    edge1 = rectSegments[0]
    edge3 = rectSegments[1]
    if rs.CurveLength(edge1) > rs.CurveLength(edge3):
        longEdge = edge1
        shortEdge = edge3
    else:
        longEdge = edge3
        shortEdge = edge1
    longVec = rs.VectorCreate(rs.CurveStartPoint(longEdge), rs.CurveEndPoint(longEdge))
    longVecRev = rs.VectorReverse(longVec)
    shortVec = rs.VectorCreate(rs.CurveStartPoint(shortEdge), rs.CurveEndPoint(shortEdge))
    shortVecRev = rs.VectorReverse(shortVec)
    
    #(2)Stair Width
    stairWidth = (rs.CurveLength(shortEdge)-minGapSize)/2
    if stairWidth < .6:
        print "ERROR: Stair is ridiculously too narrow."
        return 
    
    #(3)Run Length
    runLength = rs.CurveLength(longEdge) - (stairWidth*2)
    if runLength < 1:
        print "ERROR: Stair is ridiculously too short."
        return 
    
    #LandingRect
    landing1Plane = rs.PlaneFromFrame(rs.CurveStartPoint(shortEdge), shortVecRev, longVecRev)
    landing1 = rs.AddRectangle(landing1Plane, rs.CurveLength(shortEdge), stairWidth)
    landing2Plane = rs.PlaneFromFrame(rs.CurveEndPoint(longEdge), shortVec, longVec)
    landing2 = rs.AddRectangle(landing2Plane, rs.CurveLength(shortEdge), stairWidth)
    
    
    #RunRects
    run1Plane = rs.PlaneFromFrame(rs.CurveEditPoints(landing1)[3], shortVecRev, longVecRev)
    run1Rect = rs.AddRectangle(run1Plane, stairWidth, runLength)
    run2Plane = rs.PlaneFromFrame(rs.CurveEditPoints(landing2)[3], shortVec, longVec)
    run2Rect = rs.AddRectangle(run2Plane, stairWidth, runLength)
    
    #(4)Num Flights between Landings
    numLevels = len(landingLevels)
    deltaLevels = []
    runsPerLevel = []
    mostRisersInRun = math.floor(runLength/minTread)
    if mostRisersInRun > maxRisersInRun:
        mostRisersInRun = maxRisersInRun
    numRuns = 0
    
    for i in range(0, numLevels-1):
        deltaLevels.append(landingLevels[i+1]-landingLevels[i])
        minNumRisers = math.ceil(deltaLevels[i]/maxRiser)
        runsPerLevel.append(math.ceil(minNumRisers/mostRisersInRun))
        numRuns = numRuns + int(runsPerLevel[i])
    
    #(5) Which flights
    
    listOfRuns = []
    for i in range(0, numRuns):
        if i%2: #if even
            listOfRuns.append(rs.CopyObject(run1Rect))
        else:
            listOfRuns.append(rs.CopyObject(run2Rect))
    
    #(6) Num Treads per run
    runsDeltaHeight = []
    for i in range(0, numLevels-1):
        for j in range(0,int(runsPerLevel[i])):
            runsDeltaHeight.append(deltaLevels[i]/runsPerLevel[i])
    
    numRisersPerRun = []
    for i in range(0, numRuns):
        numRisersPerRun.append(math.ceil(runsDeltaHeight[i]/maxRiser))
    
    
    
    #(7) Move Runs
    elevation = 0
    landings = []
    for i in range(0, numRuns):
        elevation = elevation + runsDeltaHeight[i]
        translation = rs.VectorCreate([0,0,elevation], [0,0,0])
        rs.MoveObject(listOfRuns[i], translation)
        if i%2:
            landings.append(rs.MoveObject(rs.CopyObject(landing2), translation))
        else:
            landings.append(rs.MoveObject(rs.CopyObject(landing1), translation))
    
    #(8) Make Landings
    stairGeo = []
    for i in range(0, numRuns):
        dir = rs.VectorCreate([0,0,0], [0,0,runsDeltaHeight[i]])
        #rs.MoveObject(landings[i], dir)
        path = rs.AddLine([0,0,0], [0,0,-thickness])
        geo = rs.ExtrudeCurve(landings[i], path)
        rs.CapPlanarHoles(geo)
        stairGeo.append(geo)
        rs.DeleteObject(path)
    rs.DeleteObjects(landings)
    
    #(9) Draw Stairs
    runs = []
    for i in range(0, numRuns):
        runs.append(Run(listOfRuns[i], runsDeltaHeight[i], numRisersPerRun[i], thickness, i))
        stairGeo.append(runs[i].make())
        runs[i].printStats()
    
    finalGeo = rs.BooleanUnion(stairGeo, delete_input = True)
    
    #(10) Scissor Stairs
    if scissorStair:
        pt0 = rs.CurveMidPoint(rectSegments[0])
        pt1 = rs.CurveMidPoint(rectSegments[1])
        pt2 = rs.CurveMidPoint(rectSegments[2])
        pt3 = rs.CurveMidPoint(rectSegments[3])
        mir1 = rs.MirrorObject(finalGeo, pt0, pt2, copy = True)
        mirroredStair = rs.MirrorObject(mir1, pt1, pt3, copy = False)
    
    #(11)Label
    rs.SetUserText(finalGeo, "Brew", "Hot Coffee")
    rs.SetUserText(mirroredStair, "Brew", "Hot Coffee")
    
    #Cleanup
    rs.DeleteObjects(listOfRuns)
    rs.DeleteObjects(rectSegments)
    rs.DeleteObject(landing1)
    rs.DeleteObject(landing2)
    rs.DeleteObject(run1Rect)
    rs.DeleteObject(run2Rect)
    print"done"
    return None

def main():
    rect = rs.VisibleObjects()  
    if rect is None:
        return
    rs.EnableRedraw(False)
    landingLevels = [0,6,11.5]
    makeFireStair(rect, landingLevels)
    rs.EnableRedraw(True)

if __name__ == "__main__":
    main()    