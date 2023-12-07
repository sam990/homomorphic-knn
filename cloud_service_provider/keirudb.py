from enum import Enum
from threading import Timer, Condition

class IncNonce:
    def __init__(self):
        self.nonce = 0
    def get(self):
        self.nonce += 1
        return self.nonce


class State(Enum):
    WAITING = 1
    FINISHED = 2

class Keiru:
    '''Keiru is a in-memory deatabase that stores data for a limited time and then destroys it'''
    def __init__(self, timer=60):
        self.destroy_time = timer
        self.database = {}
        
    def cleardb(self):
        self.database = {}

    def destroy(self, queryid):
        if queryid in self.database:
            del self.database[queryid]
    
    def add(self, queryid, newdb):
        self.finishpush(queryid, newdb)
        self.database[queryid]['db'] = newdb
        self.database[queryid]['state'] = State.FINISHED
        timer = Timer(self.destroy_time, self.destroy, args=[queryid])
        timer.start()
    
    def startpush(self, queryid, nonce):
        self.database[queryid] = {'db': [], 'state': State.WAITING, 'cv': Condition(), 'nonce': nonce }
    
    def finishpush(self, queryid, newdb, nonce):
        if queryid not in self.database or self.database[queryid]['nonce'] != nonce:
            return False
        self.database[queryid]['db'] = newdb
        self.database[queryid]['state'] = State.FINISHED
        if self.database[queryid]['cv'] is not None:
            with self.database[queryid]['cv']:
                self.database[queryid]['cv'].notify_all()
        timer = Timer(self.destroy_time, self.destroy, args=[queryid])
        timer.start()
        return True
    
    def getdata(self, queryid):
        if queryid not in self.database:
            return None
        
        while self.database[queryid]['state'] == State.WAITING:
            with self.database[queryid]['cv']:
                self.database[queryid]['cv'].wait()
        
        return self.database[queryid]['db']
        