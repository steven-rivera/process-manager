import re
from structs import PCB, RCB, RL





class Manager:

    # This Managaer can support 16 processes
    MAX_PROCESSES = 16

    # Resource i conatins RESOURCES[i] units
    RESOURCES = [1, 1, 2, 3]


    def __init__(self):
        pass

    
    def runShell(self) -> None:
        
        # Pattern used to determine if valid command is given
        pattern = re.compile(r"^(?P<command>all|in|to|cr (?P<priorityLevel>\d+)|de (?P<pcbIndex>\d+)|r[ql] (?P<resource>\d+) (?P<numUnits>\d+))$")
        while ( line := input().strip() ) != "":
            
            try:
                command = pattern.match(line)

                if command == None:
                    print("INVALID COMMAND")
                    continue
                
                if command["command"].startswith("in"):
                    self.init()
                
                if command["command"].startswith("to"):
                    self.timeout()
                
                if command["command"].startswith("cr"):
                    self.createProcess( priority=int(command["priorityLevel"]) )   
                
                if command["command"].startswith("de"):
                    self.destroyProcess( pcbIndex=int(command["pcbIndex"]) )
                
                if command["command"].startswith("rq"):
                    self.requestResource( pcbIndex=self.RL.getRunningProcess(), 
                                          rcbIndex=int(command["resource"]), 
                                          numUnits=int(command["numUnits"]) )
                
                if command["command"].startswith("rl"):
                    self.releaseResource( pcbIndex=self.RL.getRunningProcess(), 
                                          rcbIndex=int(command["resource"]), 
                                          numUnits=int(command["numUnits"]) )
                
                if command["command"].startswith("all"):
                    print(f"PCBs: {[(pcb._children, pcb._resources) for pcb in self.PCBs if pcb != None]}")
                    print(f"RCBs: {[(rcb._state, rcb._waitList) for rcb in self.RCBs]}")
                    print(f"RL:   {self.RL._levels}")
            
            except AssertionError as e:
                print(f"ERROR: {e}")





    def init(self) -> None:
        # None represents a free PCB entry
        self.PCBs = [None] * Manager.MAX_PROCESSES
        self.RCBs = [RCB(inventory=inventory) for inventory in Manager.RESOURCES] 
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

        # Add child process index into list of children
        self.PCBs[runningPCBIndex].addChild(childPCBIndex)
        
        # Add child into ready list
        self.RL.insert(pcbIndex=childPCBIndex, priority=priority)
        
        print(f"process {childPCBIndex} created")
        self.scheduler()

    
    
    

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
    
        

        runningPCBIndex = self.RL.getRunningProcess()

        assert 0 <= pcbIndex < Manager.MAX_PROCESSES, "INVALID PCB INDEX"
        # Currently running process can only destroy iteself or one of its children
        assert ( (runningPCBIndex == pcbIndex) or (self.PCBs[runningPCBIndex].hasChild(pcbIndex)) ), "CAN NOT DESTROY A NON CHILD PROCESS"
        
            
        numDestroyed = recursiveDestroy(pcbIndex)
        print(f"{numDestroyed} processes destroyed")

       



    
    
    
    def requestResource(self, pcbIndex: int, rcbIndex: int, numUnits: int) -> None:
       
        # Get the corresping rcb and pcb
        resource = self.RCBs[rcbIndex]
        process = self.PCBs[pcbIndex]

        assert pcbIndex != 0, "PROCESS 0 CANNOT REQUEST RESOURCE"
        assert 0 <= rcbIndex < len(Manager.RESOURCES), "INVALID RESOURCE"
        assert process.numHeld(rcbIndex) + numUnits <= resource.unitsTotal(), "INVALID REQUEST"
        
        
        # Make sure there are enough units of resource to allocate
        if numUnits <= resource.unitsFree():
            resource.allocate(numUnits)
            process.addResource(rcbIndex, numUnits)

        # If not the block the process and add to waitlist of resource
        else:
            process.setToBlockedState(rcbIndex, numUnits)
            self.RL.remove(pcbIndex, process.getPriority())
            resource.waitListEnqueue(pcbIndex, numUnits)
            self.scheduler()

    


    
    def releaseResource(self, pcbIndex: int, rcbIndex: int, numUnits: int) -> None:

        assert rcbIndex in [0, 1, 2, 3], "INVALID RESOURCE"
        
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

        self.scheduler()
    




    def timeout(self) -> None:
        # Mimics preemptive scheduling
        self.RL.moveHeadToEnd()
        self.scheduler()



    def scheduler(self) -> None:
        print(f"process {self.RL.getRunningProcess()} running")



    def _getFreePCBIndex(self) -> int:
        for index, pcb in enumerate(self.PCBs):
            if pcb == None:
                return index
        return -1




if __name__ == "__main__":
    Manager().runShell()

