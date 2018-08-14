# Abaqus-RunINPFiles
GUI to handle job queues in Abaqus

# Prerequisites:
  - Abaqus, PIP
  
# Customization: 
Please adapt lines 38 to 41 to match your preferences.

# Usage:
1. Add a job in the queue:
    - Via file selection: 
        - Click on Select INP File, navigate to the right INP File and select it.
        - Update the Cpus, Gpus, Priority and Restart fields according to your needs. 
        - Click on Add Job to the list.
    - Via folder selection:
        - Update the Cpus, Gpus, Priority and Restart fields according to your needs.
        - Click on Run all files in Folder, navigate to the folder containing the INP files to run, select it.
    - Via editing the File List manually:
        - In the text field, add a new line, type the INP file name, its path, the cpus number, the gpus number, the priority and if it is a restart job. Theses values must be separated by a comma ','.
2. Select the version of Abaqus to be used.
3. Run the Queue. 

  While the Queue is running, one can:
  - Display the MSG or STA File produced by Abaqus in order to follow the evolution of the analysis. 
  - Display the Log file to view the history of the jobs that have been running with this GUI.
  - Track the jobs that are currently running on the machine. (Even those that haven't been launched using the GUI)
  - Kill the job currently running. Via PID: kills the process. Via the Terminate Jobs: command "Abaqus j=YourINPFile terminate"
  - Close the GUI by clicking on QUIT. Please note that the current job will keep running but the rest of the queue won't be launched.


# Side Features: 
1. Launching jobs remotely:
    - Make sure that the GUI is running.
    - Open the file "JobList.txt" located in the TopLocation of the target machine.
    - Edit the File List manually.
    - Save and Close.
    - Open the file "RunQueue.txt".
    - Change if need be the value to True, save and close. The queue is now running.
    - In order to check if the queue is actually running: 
        - Open the file "JobList.txt", "#" should have been appended to the first line.
        - Or check that a '.lck' file has been created for the first inp file.
    
2. Add new jobs to the queue. Follow one of the ways described above.    
