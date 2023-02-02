## About
I built a process and resource manager that simulates the creation and destruction of processes as well as the
acquisition and releasing of resources. I created three data structures, a Process Control Block, a Resource 
Control Block, and Readly List, that are all utilized  by the manager to simulate the management of processes 
and resources within an Operating System.

Processes are represented by a process control block or PCB. PCBs store information about a process such as its 
state, priority, and resources it holds. Resources are represented by a resource control block or RCB. RCB's 
store information such as the remaining resources available as well as a waitlist of processes waiting to acquire 
this resource. The Ready List or RL is used by the manager to keep track of processes in the ready state as well 
as to schedule processes based on their priority level. 

## Requirements
- python - version 3.9.6+
 

## How to Run

- **Option 1: With input file** 
    - `python manager.py <inputs.txt>`
        - Each command in `<inputs.txt>` should be on its own line. Output will be printed to *stdout*

- **Option 2: Manual inputs**
    - `python manager.py`
        - Commands will be read from *stdin* one at a time. Output will be printed to *stdout*

## Supported Commands
- `in`
    - Restore the system to its initial state. First command must be init command.


- `cr <p>`
    - Invoke function createProcess(), which creates a new process at the priority level `<p>`. `<p>` can 
    have a value of 1 or 2 (0 is reserved for init process). This manager supports a maximum of 16 processes 
    including the init process.


- `de <i>`
    - Invoke the function destroyProcess(), which destroy the process identified by the PCB index `<i>`, and 
    all of its descendants


- `rq <r> <n>`
    - Invoke the function requestResource(), which requests `<n>` units of resource `<r>`. `<r>` can be 0, 1, 
    2, or 3. Resource `<r>=0` and `<r>=1` have an inventory of **1** unit, resource `<r>=2` has an inventory 
    of **2** units, and resource `<r>=3` has an inventory of **3** units

- `rl <r> <n>`
    - Invoke the function releaseResource(), which releases the resource `<r>`. `<r>` can be 0, 1, 2, or 3.
     `<n>` gives the number of units to be released. `<n>` must be less than or equal to the number of units 
     the currently running process is holding

- `to`
    - Invokes the function timeout() which simulates preemptive scheduling. 


## Output

- For each input command, the output will be the index of the process running next. If a command results 
in an error, **-1** will be outputted.