from action import *

class Arena:
    def __init__(self, data):
        self._playersList = []
        self._data = data

    def setActionTo(self, cid, action):
        flag = False
        for character in self._playersList:
            if character.isId(cid):
                if action == 0:
                    character.setAction(ACTION.HIT)
                    flag = True
                elif action == 1:
                    character.setAction(ACTION.BLOCK)
                    flag = True
                elif action == 2:
                    character.setAction(ACTION.DODGE)
                    flag = True
                elif action == 3:
                    character.setAction(ACTION.FLY)
                    flag = True
                self._data.addData("set_action", character.toDict())
        return flag

    def setTargetTo(self, cid, target):
        flag = False
        for character in self._playersList:
            if character.isId(cid):
                character.setTarget(target)
                self._data.addData("set_target", character.toDict())
                flag = True
        return flag

    def getTotalNbPlayer(self):
        return len(self._playersList)

    def getActiveNbPlayer(self):
        deadChars = 0
        for character in self._playersList:
            if character.isDead():
                deadChars += 1
        return len(self._playersList) - deadChars

    def getPlayerByIndex(self, index):
        return self._playersList[index]

    def getPlayerByName(self, id):
        for character in self._playersList:
            if character.isId(id):
                return character
        return None

    def updatePlayer(self, character):
        for i in range(len(self._playersList)):
            if self._playersList[i].isId(character.getId()):
                self._playersList[i] = character

    def addPlayer(self, character):
        self._playersList.append(character)

    def removePlayer(self, character):
        for i in range(len(self._playersList)):
            if character.isId(self._playersList[i].getId()):
                del self._playersList[i]
                self._data.addData("leave_arena", character.toDict())
                break

    # def removeAfkPlayers(self):
    #     for i in reversed(range(len(self._playersList))):
    #         cAction, cTarget = self._playersList[i].getAction()
    #         if cAction is None:
    #             self._data.addData("leave_arena", self._playersList[i].toDict())
    #             del self._playersList[i]

    def everyoneHasAnAction(self):
        for character in self._playersList:
            if not character.isDead():
                cAction, cTarget = character.getAction()
                if cAction == None or ((cAction == ACTION.HIT or cAction == ACTION.FLY)  and cTarget == None):
                    return False
        return True

    def toDict(self):
        d = {}
        d["arena"] = []
        for character in self._playersList:
            d["arena"].append(character.toDict())
        return d