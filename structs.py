from collections import deque
from copy import copy



class PCB:

    """
    The Process Control Block is the data structure used to represent
    processes in an OS. In this implementation a process can be in one of two 
    states, READY or BLOCKED. 

    self._state: The state field represents the sate of the process.
    
    self._priority: The priority field stories an integer representing the
                    process' priority within the Ready List
    
    self._parent: The parent field stores an index into an array
                  of PCBs that correspond the parent process
                  
    self._children: The children field is a FIFO list of indexes of 
                    the process's children

    self._resources: The resources field stores the resources the
                     the process is currently holding where the key 
                     is an index into an array of RCBs and the value 
                     is the number of units of that resource that 
                     the process has
                     
    self._blockedOn: The blockedOn field stores a tuple in the form 
                     (rcbIndex, numUnits) when a process is the BLOCKED state
    
    """

    
    READY_STATE   = 1
    BLOCKED_STATE = 0

    def __init__(self, state: int, priority: int, parent: int):
        self._state     = state
        self._priority  = priority
        self._parent    = parent
        self._children  = deque()
        self._resources = dict()
        self._blockedOn = (None, None)


    def addChild(self, child: int) -> None:
        self._children.append(child)

    def removeChild(self, child: int) -> None:
        self._children.remove(child)

    def hasChild(self, child: int) -> bool:
        return child in self._children
    

    def iterResources(self) -> tuple[int, int]:
        for rcbIndex, numUnits in list(self._resources.items()):
            yield (rcbIndex, numUnits)
    
    
    def addResource(self, rcbIndex: int, numUnits: int):
        if rcbIndex in self._resources:
            self._resources[rcbIndex] += numUnits
        else:
            self._resources[rcbIndex] = numUnits


    def removeResource(self, rcbIndex: int, numUnits: int):
        if self._resources[rcbIndex] == numUnits:
            del self._resources[rcbIndex]
        else:
            self._resources[rcbIndex] -= numUnits
       
    

    def updatePriority(self, newPriority: int) -> None:
        self._priority = newPriority

    def updateParent(self, newParent: int) -> None:
        self._parent = newParent


      
    def setToReadyState(self) -> None:
        self._state = PCB.READY_STATE
        self._blockedOn = (None, None)

    def setToBlockedState(self, rcbIndex: int, numUnits: int) -> None:
        self._state = PCB.BLOCKED_STATE
        self._blockedOn = (rcbIndex, numUnits)

    
    
    def getPriority(self) -> int:
        return self._priority

    def getParent(self) -> int:
        return self._parent

    def getChildren(self) -> deque:
        return copy(self._children)

    def getResources(self) -> dict:
        return copy(self._resources)

    def getBlockedOn(self) -> tuple[int, int]:
        return self._blockedOn


    def isReady(self) -> bool:
        return self._state == PCB.READY_STATE
    
    def isBlocked(self) -> bool:
        return self._state == PCB.BLOCKED_STATE

    
    def numHeld(self, rcbIndex: int):
        """ 
        Return the number of units of a given resourse 
        the process holds. 
        """
        return self._resources.get(rcbIndex, 0)







class RCB:

    """
    The Resource Control Block is the data structure used to keep track of 
    resources in an OS. 
    
    self._inventory: The inventory field indicates how many units of a given resource exits. 
                     This value is static. 
    
    self._state: The state field keeps track of how many units of that resource are still 
                 available/unallocated. 
                 
                
    self._waitlist: The waitlist field stores a queue of tuples (process index, units requested)
                    that keeps tracks of processes blocked on the given resource. 

    """
    
    def __init__(self, inventory):
        self._inventory = inventory
        self._state     = inventory
        self._waitList  = deque()
        

    def waitListEnqueue(self, pcbIndex: int, numUnits: int) -> None:
        assert numUnits <= self._inventory
        self._waitList.append((pcbIndex, numUnits))

    def waitListDequeue(self) -> tuple[int, int]:
        return self._waitList.popleft()

    def waitListRemove(self, pcbIndex: int, numUnits: int) -> None:
        self._waitList.remove((pcbIndex, numUnits))



    def allocate(self, numUnits: int) -> None:
        assert numUnits <= self._state
        self._state -= numUnits

    def free(self, numUnits: int) -> None:
        self._state += numUnits


    def unitsFree(self) -> int:
        return self._state

    def unitsTotal(self) -> int:
        return self._inventory


    def waitListSize(self) -> int:
        return len(self._waitList)
    
    def waitListHead(self) -> tuple[int, int]:
        return self._waitList[0]








class RL:
    """
    The Ready List is the data structure used by the schedular to decide
    which process to run next on the CPU based on a process' priority level.
    
    
    self._levels: This level field segregates processes into THREE levels of 
                  FIFO lists according to their priorites where priority is the 
                  index into the array of FIFO lists. For example, self._levels[0] 
                  is the lowest priority level and self._levels[NUM_PRIORITY_LEVELS - 1] 
                  is the highest. Each FIFO list contains the index of the 
                  corresponding PCB in the PCB array.

    """
    
    
    NUM_PRIORITY_LEVELS = 3


    def __init__(self):
        self._levels = [deque() for _ in range(RL.NUM_PRIORITY_LEVELS)]

   
    def __iter__(self):
        def generator():
            for level in reversed(self._levels):
                for pcbIndex in level:
                    yield pcbIndex
        return generator()

    
    def insert(self, pcbIndex: int, priority: int) -> None:
        assert 0 <= priority < RL.NUM_PRIORITY_LEVELS, "INVALID PRIORITY LEVEL"    
        self._levels[priority].append(pcbIndex)


    def remove(self, pcbIndex: int, priority: int) -> None:
        assert 0 <= priority < RL.NUM_PRIORITY_LEVELS, "INVALID PRIORITY LEVEL"
        self._levels[priority].remove(pcbIndex)


    def getRunningProcess(self) -> int:
        """ 
        The running process is the first item of
        the highest non-empty priority level.
        """

        # Must reverse to get priority levels in decending order
        for level in reversed(self._levels):
            if len(level) > 0:
                return level[0]
    

    def moveHeadToEnd(self) -> None:
        # Must reverse to get priority levels in decending order
        for level in reversed(self._levels):
            if len(level) > 0:
                level.rotate(-1)
                return 