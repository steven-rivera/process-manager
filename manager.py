import sys
import re
from structs import PCB, RCB, RL




class Manager:

    def __init__(self):
        # This Manager can support 16 processes
        self.MAX_PROCESSES = 16
        
        # Resource i conatins RESOURCES[i] units
        self.RESOURCES = [1, 1, 2, 3]

        # Keep track of how many times init is called
        self.initCalls = 0

    


    def runShell(self, inputFile=None) -> None:
        
        # Pattern used to determine if valid command is given
        pattern = re.compile(r"^(?P<command>all|in|to|cr (?P<priorityLevel>\d+)|de (?P<pcbIndex>\d+)|r[ql] (?P<resource>\d+) (?P<numUnits>\d+))$")
        
        
        def runCommand(command: str) -> None:
            if command == "": return
            
            try:
                match = pattern.match(command)
 
                if match == None:
                    print("-1", end=" ")
                    return
                
                if match["command"].startswith("in"):
                    self.init()
                
                if match["command"].startswith("to"):
                    self.timeout()
                
                if match["command"].startswith("cr"):
                    self.createProcess( priority=int(match["priorityLevel"]) )   
                
                if match["command"].startswith("de"):
                    self.destroyProcess( pcbIndex=int(match["pcbIndex"]) )
                
                if match["command"].startswith("rq"):
                    self.requestResource( pcbIndex=self.RL.getRunningProcess(), 
                                          rcbIndex=int(match["resource"]), 
                                          numUnits=int(match["numUnits"]) )
                
                if match["command"].startswith("rl"):
                    self.releaseResource( pcbIndex=self.RL.getRunningProcess(), 
                                          rcbIndex=int(match["resource"]), 
                                          numUnits=int(match["numUnits"]) )
            
            except AssertionError:
                print("-1", end=" ")

            else:
                self.scheduler()

        
        # Read commands from .txt file if provided
        if inputFile != None:
            with open(inputFile, "r") as f:
                for command in f:
                    runCommand(command.strip())

        # Continuously read commands from stdin
        else:
            while True:
                command = input().strip()
                runCommand(command)
                
        
        
    




    def init(self) -> None:
        self.initCalls += 1

        # Print subsequent init sessions on new line
        if self.initCalls != 1: print()

        # None represents a free PCB entry
        self.PCBs = [None] * self.MAX_PROCESSES
        self.RCBs = [RCB(inventory=inventory) for inventory in self.RESOURCES] 
        self.RL   = RL()
  
    
        # Initialize process 0 with priority 0 and no parent
        self.PCBs[0] = PCB(state=PCB.READY_STATE, priority=0, parent=None)
        

        # Add process 0 to ready list
        self.RL.insert(pcbIndex=0, priority=self.PCBs[0].getPriority())
    
    
    
    
    def createProcess(self, priority: int) -> None:
    
        childPCBIndex = self._getFreePCBIndex()

        assert priority in [1, 2], "PRIORITY MUST BE 1 or 2"    
        assert childPCBIndex >= 0, "MAX NUMBER OF PROCESSES ALREADY CREATED"
        
        
        runningPCBIndex = self.RL.getRunningProcess()
        
        # Create child process who's parent is currently running process
        childProcess = PCB(state=PCB.READY_STATE, priority=priority, parent=runningPCBIndex)
    
        # Save new PCB into free slot of PCB array
        self.PCBs[childPCBIndex] = childProcess

        # Add child process into parents' list of children
        self.PCBs[runningPCBIndex].addChild(childPCBIndex)
        
        # Add child into ready list
        self.RL.insert(pcbIndex=childPCBIndex, priority=priority)
        
    
    

    def destroyProcess(self, pcbIndex: int) -> None:

        def recursiveDestroy(pcbIndex: int) -> int: 
            process = self.PCBs[pcbIndex]
            
            numDestroyed = 0
            # Recursively destroy the children of the process currently being destroyed
            for childIndex in process.getChildren():
                numDestroyed += recursiveDestroy(childIndex)        
         
            parentPCBIndex = process.getParent()
            self.PCBs[parentPCBIndex].removeChild(pcbIndex)

            if process.isReady():
                # Remove the process from ready list if it is in READY state
                self.RL.remove(pcbIndex, process.getPriority())
            else:
                # If process is blocked on a resource remove it from the RCB's waitlist
                rcbIndex, numUnits = process.getBlockedOn()
                self.RCBs[rcbIndex].waitListRemove(pcbIndex, numUnits)
                
        
            # Release all of the resources the process was holding
            for resource in process.iterResources():
                rcbIndex, numUnits = resource
                self.releaseResource(pcbIndex, rcbIndex, numUnits)

            # Free up the PCB slot 
            self.PCBs[pcbIndex] = None

            return numDestroyed + 1
    
    
        # Cannot destroy process 0
        assert pcbIndex != 0, "CANNOT DESTROY PROCESS 0"

        # Check that pcbIndex contains a PCB
        assert self._processExists(pcbIndex), "PROCESS DOES NOT EXISTS"

        
        runningPCBIndex = self.RL.getRunningProcess()

        # Currently running process can only destroy iteself or one of its descendants
        assert ( (runningPCBIndex == pcbIndex) or (self._hasDescendant(runningPCBIndex, pcbIndex)) ), "CAN NOT DESTROY A NON DESCENDANT PROCESS"

        
        numDestroyed = recursiveDestroy(pcbIndex)
        # print(numDestroyed, end=" ")

       


    def requestResource(self, pcbIndex: int, rcbIndex: int, numUnits: int) -> None:
       
        assert pcbIndex != 0, "PROCESS 0 CANNOT REQUEST RESOURCE"
        assert 0 <= rcbIndex < len(self.RESOURCES), "INVALID RESOURCE"
        
        
        # Get the corresping rcb and pcb
        resource = self.RCBs[rcbIndex]
        process = self.PCBs[pcbIndex]

        assert process.numHeld(rcbIndex) + numUnits <= resource.unitsTotal(), "CANNOT REQUEST MORE THAN TOTAL INVENTORY"


        # Make sure there are enough units of resource to allocate
        if numUnits <= resource.unitsFree():
            resource.allocate(numUnits)
            process.addResource(rcbIndex, numUnits)

        # If not the block the process and add to waitlist of resource
        else:
            process.setToBlockedState(rcbIndex, numUnits)
            self.RL.remove(pcbIndex, process.getPriority())
            resource.waitListEnqueue(pcbIndex, numUnits)

    

    
    def releaseResource(self, pcbIndex: int, rcbIndex: int, numUnits: int) -> None:

        assert 0 <= rcbIndex < len(self.RESOURCES), "INVALID RESOURCE"
        
        # Get the corresping rcb and pcb
        resource = self.RCBs[rcbIndex]
        process = self.PCBs[pcbIndex]

        assert numUnits <= process.numHeld(rcbIndex), "CANNOT RELEASE MORE UNITS THAN CURRENTLY ACQUIRED"

        resource.free(numUnits) 
        process.removeResource(rcbIndex, numUnits)

        # Attempt to allocate remaining inventory of resource to processes in the waitlist 
        while ( resource.waitListSize() > 0 ) and ( resource.unitsFree() > 0 ):
            
            # Get the next processIndex next in line for the resource
            waitingPcbIndex, waitingNumUnits = resource.waitListHead()
            
            if waitingNumUnits <= resource.unitsFree():
                
                # Remove process from the waitlist
                resource.waitListDequeue()
                
                resource.allocate(waitingNumUnits)
                waitingPCB = self.PCBs[waitingPcbIndex]
                waitingPCB.addResource(rcbIndex, waitingNumUnits)

                # Process is no longer blocked on this resource
                waitingPCB.setToReadyState()
                    
                # Insert process into ready list
                self.RL.insert(pcbIndex=waitingPcbIndex, priority=waitingPCB.getPriority())




    def timeout(self) -> None:
        # Mimics preemptive scheduling
        self.RL.moveHeadToEnd()




    def scheduler(self) -> None:
        print(self.RL.getRunningProcess(), end=" ")




    def _getFreePCBIndex(self) -> int:
        for index, pcb in enumerate(self.PCBs):
            if pcb == None:
                return index
        return -1

    
    def _hasDescendant(self, pcbIndex: int, descendant: int) -> bool:
        
        while True:
            descendantPCB = self.PCBs[descendant]
            parentIndex = descendantPCB.getParent()

            if parentIndex == pcbIndex:
                return True

            if parentIndex == 0:
                return False

            descendant = parentIndex


    def _processExists(self, pcbIndex) -> bool:
        if (pcbIndex < 0) or (pcbIndex >= self.MAX_PROCESSES):
            return False
        
        return self.PCBs[pcbIndex] != None




if __name__ == "__main__":
    try:
        fileName = sys.argv[1]
    except IndexError:
        # If no input file is given, then shell will read commands from stdin 
        Manager().runShell()
    else:
        # If input file is given, shell will read commands from file
        Manager().runShell(inputFile=fileName)


