from ghpythonlib.componentbase import executingcomponent as component
import Grasshopper, GhPython
import System
import Rhino
import rhinoscriptsyntax as rs
#From 0.01
class FireStair(component):
    
    def RunScript(self, rect, lvls):
        """Provides a scripting component.
            Inputs:
                rect: Rectangle
                lvls: Landing Levels
            Output:
                geo: Stair Geometry"""
        
        __version__ = 0.01
        
        __author__ = "Tim"
        
        import rhinoscriptsyntax as rs
        import math
        
        class Run():
            def __init__(self, Rect, deltaHeight, numRisers):
                self.Rect = Rect
                self.deltaHeight = deltaHeight
                self.numRisers = int(numRisers)
                self.thickness = .15
            
            def make(self):
                self.segments = rs.ExplodeCurves(self.Rect)
                
                treadLength = rs.CurveLength(self.segments[1])/self.numRisers
                riserHeight = self.deltaHeight/self.numRisers
                runVector = rs.VectorCreate(rs.CurveEndPoint(self.segments[1]),rs.CurveStartPoint(self.segments[1]))
                unitRunVec = rs.VectorUnitize(runVector)
                treadVec = rs.VectorScale(unitRunVec, treadLength) 
                riseVec = rs.VectorCreate( [0,0,riserHeight], [0,0,0])
                
                newPt = [rs.CurveStartPoint(self.segments[0]).X, rs.CurveStartPoint(self.segments[0]).Y, rs.CurveStartPoint(self.segments[0]).Z-self.deltaHeight]
                ptList = []
                ptList.append(rs.AddPoint(newPt))
                for i in range(self.numRisers):
                    tempPt = rs.CopyObject(ptList[-1])
                    rs.MoveObject(tempPt, riseVec)
                    ptList.append(tempPt)
                    tempPt = rs.CopyObject(ptList[-1])
                    rs.MoveObject(tempPt, treadVec)
                    ptList.append(tempPt)
                
                downLine = rs.VectorCreate([0,0,0], [0,0,self.thickness])
                newBtmPt = rs.MoveObject(rs.CopyObject(ptList[0]), downLine)
                ptList.insert(0, newBtmPt)
                newBtmPt2 = rs.MoveObject(rs.CopyObject(ptList[-1]), downLine)
                ptList.append(newBtmPt2)
                
                stringer = rs.AddPolyline(ptList)
                closeCrv = rs.AddLine(rs.CurveStartPoint(stringer), rs.CurveEndPoint(stringer))
                
                newStringer = rs.JoinCurves([stringer, closeCrv], True)
                
                stair = rs.ExtrudeCurve(newStringer, self.segments[0])
                rs.CapPlanarHoles(stair)
                rs.DeleteObject(stringer)
                rs.DeleteObject(newStringer)
                rs.DeleteObjects(ptList)
                rs.DeleteObjects(self.segments)
                return stair
        
        
        def makeFireStair(rect, landingLevels):
            #HARD VARIABLES
            minGapSize = .2
            minTread = .260
            maxRiser = .180
            thickness = .15
            
            #(1)Determine Run Direction
            rs.SimplifyCurve(rect)
            rectSegments = rs.ExplodeCurves(rect)
            edge1 = rectSegments[0]
            edge3 = rectSegments[1]
            rs.DeleteObject(rectSegments[2])
            rs.DeleteObject(rectSegments[3])
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
            rs.CurveArrows(longEdge, 2)
            rs.CurveArrows(shortEdge, 2)
            
            #(2)Stair Width
            stairWidth = (rs.CurveLength(shortEdge)-minGapSize)/2
            
            #LandingRect
            landing1Plane = rs.PlaneFromFrame(rs.CurveStartPoint(shortEdge), shortVecRev, longVecRev)
            landing1 = rs.AddRectangle(landing1Plane, rs.CurveLength(shortEdge), stairWidth)
            landing2Plane = rs.PlaneFromFrame(rs.CurveEndPoint(longEdge), shortVec, longVec)
            landing2 = rs.AddRectangle(landing2Plane, rs.CurveLength(shortEdge), stairWidth)
            
            #(3)Run Length
            runLength = rs.CurveLength(longEdge) - (stairWidth*2)
            
            #RunRects
            run1Plane = rs.PlaneFromFrame(rs.CurveEditPoints(landing1)[3], shortVecRev, longVecRev)
            run1Rect = rs.AddRectangle(run1Plane, stairWidth, runLength)
            run2Plane = rs.PlaneFromFrame(rs.CurveEditPoints(landing2)[3], shortVec, longVec)
            run2Rect = rs.AddRectangle(run2Plane, stairWidth, runLength)
            
            #(4)Num Flights between Landings
            numLevels = len(landingLevels)
            deltaLevels = []
            runsPerLevel = []
            maxRisersPerRun = math.floor(runLength/minTread)
            numRuns = 0
            
            for i in range(0, numLevels-1):
                deltaLevels.append(landingLevels[i+1]-landingLevels[i])
                minNumRisers = math.ceil(deltaLevels[i]/maxRiser)
                runsPerLevel.append(math.ceil(minNumRisers/maxRisersPerRun))
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
                runs.append(Run(listOfRuns[i], runsDeltaHeight[i], numRisersPerRun[i]))
                stairGeo.append(runs[i].make())
            
            finalGeo = rs.BooleanUnion(stairGeo, delete_input = True)
            #Cleanup
            rs.DeleteObjects(listOfRuns)
            rs.DeleteObjects(rectSegments)
            rs.DeleteObject(landing1)
            rs.DeleteObject(landing2)
            rs.DeleteObject(run1Rect)
            rs.DeleteObject(run2Rect)
            print"done"
            return finalGeo
        
        def main(rect, lvls):
            rs.EnableRedraw(False)
            landingLevels = lvls
            finalGeo = makeFireStair(rect, landingLevels)
            rs.EnableRedraw(True)
            return finalGeo
        
        geo = main(rect, lvls)
        
        # return outputs if you have them; here I try it for you:
        return geo
