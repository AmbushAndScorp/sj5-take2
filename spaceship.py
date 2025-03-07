from direct.showbase.Loader import *
from CollideObjectBase import *
from panda3d.core import NodePath
from panda3d.core import Vec3
from direct.task import Task
from typing import Callable
from bullets import Missile
from direct.gui.OnscreenImage import OnscreenImage

class Spaceship (SphereCollideObject):
    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float, manager: Task, accept: Callable[[str, Callable], None]):
        super(Spaceship, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0,0,0), 1)
        #self.modelNode = loader.loadModel(modelPath)
        self.render = parentNode
        self.modelNode.reparentTo(parentNode)
        self.loader = Loader
        self.accept = accept
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.taskManager = manager

        self.reloadTime = 0.25
        self.missileDist = 4000
        self.missileBay = 1

        self.taskManager.add(self.CheckIntervals, 'checkMissiles', 34)

        self.keyBinds()
    
    def keyBinds(self):
        # all bindings for movement
        self.accept('space', self.Thrust, [1])
        self.accept('space-up', self.Thrust, [0])
        self.accept('a', self.LeftTurn, [1])
        self.accept('a-up', self.LeftTurn, [0])
        self.accept('d', self.RightTurn, [1])
        self.accept('d-up', self.RightTurn, [0])
        self.accept('w', self.LookUp, [1])
        self.accept('w-up', self.LookUp, [0])
        self.accept('s', self.LookDown, [1])
        self.accept('s-up', self.LookDown, [0])
        self.accept('arrow_left', self.RollLeft, [1])
        self.accept('arrow_left-up', self.RollLeft, [0])
        self.accept('arrow_right', self.RollRight, [1])
        self.accept('arrow_right-up', self.RollRight, [0])
        self.accept('f', self.Fire)
    
    def Thrust(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyThrust, 'forward-thrust') 
        else:
            self.taskManager.remove('forward-thrust')

    def ApplyThrust(self, task):
        rate = 5
        traj = self.render.getRelativeVector(self.modelNode, Vec3.forward())
        traj.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + traj * rate)

        return Task.cont
    
    def LeftTurn(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyLeftTurn, 'turn-left')
        else:
            self.taskManager.remove('turn-left')
    
    def ApplyLeftTurn(self, task):
        # half a degree every frame
        rate = .5
        self.modelNode.setH(self.modelNode.getH() + rate)
        return Task.cont
    
    def RightTurn(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyRightTurn, 'turn-right')
        else:
            self.taskManager.remove('turn-right')
    
    def ApplyRightTurn(self, task):
        rate = .5
        self.modelNode.setH(self.modelNode.getH() - rate)
        return Task.cont
    
    def LookUp(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyLookUp, 'look-up')
        else:
            self.taskManager.remove('look-up')
    
    def ApplyLookUp(self, task):
        rate = .5
        self.modelNode.setP(self.modelNode.getP() + rate)
        return Task.cont
    
    def LookDown(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyLookDown, 'look-down')
        else:
            self.taskManager.remove('look-down')
    
    def ApplyLookDown(self, task):
        rate = .5
        self.modelNode.setP(self.modelNode.getP() - rate)
        return Task.cont
    
    def RollLeft(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyRollLeft, 'left-roll')
        else:
            self.taskManager.remove('left-roll')
    
    def ApplyRollLeft(self, task):
        rate = 20
        traj = self.render.getRelativeVector(self.modelNode, Vec3.left())
        traj.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + traj * rate)
        return Task.cont
    
    def RollRight(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyRollRight, 'right-roll')
        else:
            self.taskManager.remove('right-roll')
    
    def ApplyRollRight(self, task):
        rate = 20
        traj = self.render.getRelativeVector(self.modelNode, Vec3.right())
        traj.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + traj * rate)
        return Task.cont
    
    def Fire(self):
        if self.missileBay:
            travRate = self.missileDist
            aim = self.render.getRelativeVector(self.modelNode, Vec3.forward())
            aim.normalize()
            fireSol = aim * travRate
            inFront = aim * 150
            travec = fireSol + self.modelNode.getPos()
            self.missileBay -= 1
            name = 'Missile' + str(Missile.missileCount)
            posVec = self.modelNode.getPos() + inFront
            currMissile = Missile(self.loader, 'Assets/Phaser/phaser.egg', self.render, name, posVec, 4.0)
            Missile.Intervals[name] = currMissile.modelNode.posInterval(2.0, travec, startPos = posVec, fluid = 1)
            Missile.Intervals[name].start()
        else:
            if not self.taskManager.hasTaskNamed('reload'):
                print("starting reload")
                self.taskManager.doMethodLater(0, self.Reload, 'reload')
                return Task.cont
            
    def Reload(self, task):
        if task.time > self.reloadTime:
            self.missileBay += 1
            print("reload complete")
            return Task.done
        elif task.time <= self.reloadTime:
            print("reload proceeding")
            return Task.cont
        if self.missileBay > 1:
            self.missileBay = 1
    
    def CheckIntervals(self, task):
        for i in Missile.Intervals:
            if not Missile.Intervals[i].isPlaying():
                Missile.cNodes[i].detachNode()
                Missile.fireModels[i].detachNode()

                del Missile.Intervals[i]
                del Missile.fireModels[i]
                del Missile.cNodes[i]
                del Missile.collisionSolids[i]
                print (i + " has reached the end of the fire solution")
                break
        return Task.cont
    
    def EnableHUD(self):
        self.hud = OnscreenImage("Assets/Hud/Reticle3b.png", pos = Vec3(0,0,0), scale = 0.1)
        self.hud.setTransparency(TransparencyAttrib.MAplha)