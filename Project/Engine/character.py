from random import randint
from action import *

class CharacterProxy:
    def __init__(self, cid :str, teamid :str, life :int, strength :int, armor :int, speed :int):
        self._id = cid
        self._teamid = teamid
        #self._name = name
        self._life = life
        self._strength = strength
        self._armor = armor
        self._speed = speed
        self._action = None
        self._target = None
        #self._id = self._name + str(randint(0, 1000))
        self._dead = False

    def isDead(self):
        return self._dead

    def isId(self, cid):
        return self._id == cid

    def getId(self):
        return self._id

    def getLife(self):
        return self._life

    def getStrength(self):
        return self._strength

    def getArmor(self):
        return self._armor

    def getSpeed(self):
        return self._speed

    def getAction(self):
        if self._action == ACTION.HIT or self._action == ACTION.FLY:
            return self._action, self._target
        return self._action, None

    def setLife(self, value):
        self._life = value
        if value <= 0:
            self._dead = True

    def setStrength(self, value):
        self._strength = value

    def setArmor(self, value):
        self._armor = value

    def setSpeed(self, value):
        self._speed = value

    def setAction(self, value):
        self._action = value
    
    def setTarget(self, value):
        self._target = value

    def __str__(self):
        s = "------------\n"
        s += "cid : " + self._id + ",\n"
        s += "life : " + str(self._life) + "\n"
        s += "strength : " + str(self._strength) + "\n"
        s += "armor : " + str(self._armor) + "\n"
        s += "speed : " + str(self._speed) + "\n"
        s += "------------\n"
        return s

    def toDict(self):
        cDict = {}
        cDict["cid"] = self._id
        cDict["teamid"] = self._teamid
        cDict["life"] = self._life
        cDict["strength"] = self._strength
        cDict["armor"] = self._armor
        cDict["speed"] = self._speed
        cDict["action"] = actionToStr(self._action)
        cDict["target"] = str(self._target)
        cDict["dead"] = self._dead
        return cDict
