# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 14:31:12 2017

@author: feas
"""
from __future__ import print_function
import os,time,sys
from Tkinter import *
import Tkconstants, tkFileDialog
from ttk import Frame, Label, Entry, Separator
import threading
import Queue
import subprocess
from operator import itemgetter, attrgetter, methodcaller
import shutil
import unicodedata
import psutil
import signal
import logging
import datetime
import traceback
#from pathos.multiprocessing import ProcessPool
from win32api import GetSystemMetrics


###############################################################################
## INITIAL PARAMETERS #########################################################
###############################################################################

TopLocation     = 'E:\\Consult\\'

if os.path.isdir(TopLocation) != True:
    TopLocation = 'D:\\Consult\\'

defAbqVersion   = ['abq2018hf3','abq2018','abq2017','abq2016','abq6141']
defCpusNumb     = '6'
defGpusNumb     = '1'

# Logging errors to a separate file
logging.basicConfig(filename=TopLocation+'error_RunINPFile.log', 
                    filemode='a+', 
                    level=logging.DEBUG)
logger = logging.getLogger()
logger.info('\n\n\n'+'+'*50+'\n'+'+'*50+'\nStart Log: '+str(datetime.datetime.now()))




###############################################################################
## CLASSES DEFINITION #########################################################
###############################################################################

class ToolTip(object):
    """Enables to create small explanation windows when the mouse is dragged 
    over a widget"""

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        time.sleep(0.5)
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 27
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        try:
            # For Mac OS
            tw.tk.call("::tk::unsupported::MacWindowStyle",
                       "style", tw._w,
                       "help", "noActivates")
        except TclError:
            pass
        label = Label(tw, text=self.text, justify=LEFT,
                      background="#ffffe0", relief=SOLID, borderwidth=1,
                      font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def createToolTip(widget, text):
    toolTip = ToolTip(widget)
    def enter(event):
        toolTip.showtip(text)
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

class jobClass():
    """Class containing all the job specifications"""
    def __init__(self, jobValues):
        try:
            self.name = jobValues.split('||')[0]
            self.path = jobValues.split('||')[1]
            self.cpus = jobValues.split('||')[2]
            self.gpus = jobValues.split('||')[3]
            self.prio = jobValues.split('||')[4]
            self.res  = jobValues.split('||')[5]
        except:
            pass

class ThreadedTask(threading.Thread):
    """Class used to thread (execute in parallel) the loop looking and 
    executing the jobs"""
    def __init__(self, queue,root):
        threading.Thread.__init__(self)
        self.queue = queue
        self.root = root
    
    def run(self):
        def checkJobList(self):
            "- Read the FileList,\
             - Determine the job to be run"

            jobList = self.root.fileList.get("1.0",END)                         # Read the text box
            jobListSplitted = jobList.split('\n')                               # Split lines
            self.jobArray = []
            jobToRun = None
            for job in jobListSplitted:
                if job!='':
                    self.jobArray.append(jobClass(job))                         # Create list of jobs, entries of that list are instances of the Job class
            self.jobArraySorted = sorted(self.jobArray,                         # Sort the job list according to priority
                                         key=attrgetter('prio'))
            for job in self.jobArraySorted:
                #print('job= '+job.name)
                if (len(job.name.split('#'))<2 and jobToRun == None):
                    jobToRun = job
            return jobToRun

###############################################################################
################ MAIN LOOP OF THE PARALLEL THREAD #############################
###############################################################################
        Loop=True
        self.root.QueueRunning = True
        with open(TopLocation+'RunQueue.txt','w') as f:
            f.write(str(self.root.QueueRunning))
        resumedQueue = False
        
        abqVersion = self.root.abqVersion.get()
        
        ## Close the Log file if opened
        closeNotepadFile('LogFile.txt')
        
        if resumedQueue == False:
            with open(TopLocation+'LogFile.txt','a') as f:                      # Append in the log file
                f.write('+'*50+'\n'+'+'*50+
                    '\nQueue executed on '+
                    time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())+
                    '\n'+
                    '-'*50+'\n')
        else: 
            with open(TopLocation+'LogFile.txt','a') as f:                      # Append in the log file
                f.write('+'*50+'\n'+'+'*50+
                    '\nQueue resumed on '+
                    time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())+
                    '\n'+
                    '-'*50+'\n')
        # <>
        while Loop:                                                             # Main thread loop
        
            waitPreviousJobs=True
            try:
                del jobToRun
            except:
                pass
            
            
            
            # <<>>
            while waitPreviousJobs:                                             # If a job is already running, hang the queue until its completion
                waitPreviousJobInc=0
                with open(TopLocation+'JobList.txt','r') as f:                  # Compare the last job list with the jobs that are running
                    textFile = f.readlines()                                    # If the job that is running is in the job list
                processesList = psutil.pids()                                   # Wait until that/ job is completed
                for proc in processesList:
                    try:
                        p = psutil.Process(proc)
                        if (p.name()=='standard.exe' or p.name()=='explicit.exe' or p.name()=='pre.exe' or p.name()=='explicit_dp.exe'):
                            i=0
                            jobCpus='1'
                            jobGpus='0'
                            for line in p.cmdline():
                                if line == '-job':
                                    jobname=p.cmdline()[i+1]
                                elif line == '-indir':
                                    jobdir=p.cmdline()[i+1]
                                elif line == '-cpus':
                                    jobCpus=p.cmdline()[i+1]
                                elif line == '-gpus':
                                    jobGpus=p.cmdline()[i+1]
                                i+=1
                            for line in textFile:
                                if line=='#%s.inp||%s||%s||%s||1\n'%(jobname,jobdir.replace("\\", "/")+'/',jobCpus,jobGpus):
                                    jobToRun = jobClass(line)
                                    waitPreviousJobInc+=1
                                    
                                elif line=='#%s.inp||%s||%s||%s||2\n'%(jobname,jobdir.replace("\\", "/")+'/',jobCpus,jobGpus):
                                    jobToRun = jobClass(line)
                                    waitPreviousJobInc+=1
                                    
                                elif line=='#%s.inp||%s||%s||%s||3\n'%(jobname,jobdir.replace("\\", "/")+'/',jobCpus,jobGpus):
                                    jobToRun = jobClass(line)
                                    waitPreviousJobInc+=1
                    except: 
                        waitPreviousJobInc+=1
                if waitPreviousJobInc==0:
                    waitPreviousJobs=False
            # <>
            
            ## Buttons
            try:
                self.root.addFileButton.config(state=DISABLED)
            except:
                pass
            try:
                self.root.fileList.config(state=DISABLED)
            except:
                pass
            
            # Console
            try:
                jobList = self.root.fileList.get("1.0",END)                     # Read the console
            except:
                pass
            
            try:
                jobToRun = checkJobList(self)                                   # Determine the job to be run
            except:
                pass
            
            
            try:
                os.chdir(jobToRun.path)                                         # Set CWD to the job path
            except AttributeError:
                Loop=False                                                      # When no job anymore, break the loop
                break
            except UnboundLocalError:
                resumedQueue = True
                break
                pass
            
            
            
            newJobList = ''
            a = None
            
            for job in self.jobArraySorted:
                if (job.name == jobToRun.name and a == None):                   # Put a hash in front of the first job 
                    newJobList = newJobList+'#'+job.name+\
                        '||'+job.path+'||'+job.cpus+'||'+\
                        job.gpus+'||'+job.prio+'||'+job.res+'\n'                # corresponding to the job to run
                    a = 1
                else:
                    newJobList = newJobList+job.name+\
                        '||'+job.path+'||'+job.cpus+'||'+\
                        job.gpus+'||'+job.prio+'||'+job.res+'\n'


            ## Report
            print('\n\n'+jobToRun.name+ ' launched')
            
            ## Close the Log file if opened
            closeNotepadFile('LogFile.txt')
            with open(TopLocation+'LogFile.txt','a') as f:                      # Write in Report File (Log File)
                f.write('\n\n'+'-'*50+'\n'+jobToRun.name+
                    ' launched on '+
                    time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())+
                    '\n\n')
            
            try:
                self.root.fileList.config(state=NORMAL)
                self.root.fileList.delete(1.0,END)
                self.root.fileList.insert(END,newJobList)
                self.root.addFileButton.config(state='normal')
            except:
                pass


            ## Generate the running command
            if (jobToRun.res=='N'):
                cmd = '%s j=%s cpus=%s gpus=%s DOUBLE \
                    ask_delete=OFF int> %s.log'%(abqVersion, 
                                                 jobToRun.name.split('.inp')[0]+'.inp', jobToRun.cpus, 
                                                  jobToRun.gpus, jobToRun.name.split('.inp')[0])
            else:
                cmd = '%s j=%s oldjob=%s cpus=%s gpus=%s DOUBLE \
                    ask_delete=OFF int> %s.log'%(abqVersion, 
                                                 jobToRun.name.split('.inp')[0]+'.inp', 
                                                 jobToRun.res, jobToRun.cpus, 
                                                 jobToRun.gpus, jobToRun.name.split('.inp')[0])
            print(cmd)
            
            ## Launch the job
            self.root.proc = subprocess.Popen(cmd,                              # Submit the Job and pause the thread while its running
                                              cwd=jobToRun.path, 
                                              shell=True)
            
            
            pid = self.root.proc.pid                                            # Identify the process of the command
            
            ## Report
            print('The PID of the command is: %s'%pid)
            # Close the Log file if opened
            closeNotepadFile('LogFile.txt')
            with open(TopLocation+'LogFile.txt','a') as f:
                f.write('The PID of the command is: %s\n\n'%pid)
            
            time.sleep(1.)
            
            ## Identify the process of the launched job based on the parent process (command)
            p = psutil.Process(pid)
            childProcess = p.children()[0]
            incThresh=0
            while psutil.pid_exists(childProcess.pid) and childProcess.name()!='standard.exe' and childProcess.name()!='explicit.exe' and childProcess.name()!='explicit_dp.exe' and incThresh<100:
                try:
                    p = psutil.Process(childProcess.pid)
                    #print(p)
                    for process in p.children():
                        if process.name() == 'standard.exe' or process.name() == 'explicit.exe' or process.name() == 'explicit_dp.exe':
                            print('The PID of the: %s job is: %s'%(process.name(), process.pid))
                            childProcess = psutil.Process(process.pid)
                            # Write in the report file
                            with open(TopLocation+'LogFile.txt','a') as f:
                                f.write('The PID of the: %s job is: %s\n'%(process.name(), process.pid))
                            break
                        elif process.name()!='findIPAddress.exe' and process.name()!='eliT_CheckLicense.exe' and process.name()!='pre.exe' and process.name()!='eliT_DriverLM.exe':
                                childProcess = psutil.Process(process.pid)
                                time.sleep(1.)
                except psutil.NoSuchProcess:
                    incThresh+=1
                    pass
            
            return_code = self.root.proc.communicate()                          # Displays the Abaqus messages
            
            
            ## Report
            print(jobToRun.name+' has been run or was terminated')
            
            # Write in the report file (Log File)
            if (os.path.isfile(jobToRun.name.split('.inp')[0]+'.sta')==True):   # If a sta file exists, report it's last line
                with open(jobToRun.name.split('.inp')[0]+'.sta') as f:
                    staFile= f.readlines()
                with open(TopLocation+'LogFile.txt','a') as f:
                    f.write(staFile[-1])
            elif (os.path.isfile(jobToRun.name.split('.inp')[0]+'.log')==True): # If a log file exists, report it's last line
                with open(jobToRun.name.split('.inp')[0]+'.log') as f:
                    logFile= f.readlines()
                logFileLines = ''
                for line in logFile:
                    logFileLines = logFileLines + line
                with open(TopLocation+'LogFile.txt','a') as f:
                    if logFile[-1] != '\n':
                        f.write(logFile[-1])
                    else:
                        f.write(logFile[-2])
        # <>
        self.root.QueueRunning = False
        with open(TopLocation+'RunQueue.txt','w') as f:
            f.write(str(self.root.QueueRunning))
        
        if resumedQueue == False:
            self.queue.put("Task finished")                                     # End the threaded task
            
            try:
                if (newJobList!='' or jobList!=''):
                    tempVar=1
            except UnboundLocalError:
                with open(TopLocation+'LogFile.txt','a') as f:
                    f.write('The job queue was empty.')
            
            # Write in the report file
            with open(TopLocation+'LogFile.txt','a') as f:
                f.write('\n\n'+'-'*50+'\nTask finished on '+
                        time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())+
                        '\n'+'+'*50+'\n\n')
            
            # Close the Log file if opened
            closeNotepadFile('LogFile.txt')
            try:
                if (newJobList!='' or jobList!=''):
                    subprocess.Popen("Notepad "+TopLocation+'LogFile.txt')               # Open the report file in a window
            except UnboundLocalError:
                print('The job queue was empty.')
                pass
            
            # Set the buttons back to 'clickable'
            try:
                self.root.runQueueButton.config(state='normal', text='Run the Queue')
                self.root.addFileButton.config(state='normal')
                self.root.fileList.config(state='normal')
            except:
                pass


###############################################################################
############################# MAIN CLASS ######################################
###############################################################################
class App(Frame):
    """Main class instantiating the GUI and associating the buttons"""
    def __init__(self, parent):
        
        
        Frame.__init__(self,parent)
        
        incrementLoc    = 0
        
        self.parent     = parent
        frame           = Frame(parent)
        frame.pack()
        
        frameGen        = self.parent.title("Run INP")
        self.pack(fill=BOTH, expand=True)
        
        ## options for Buttons
        button_opt      = {'fill':Tkconstants.BOTH, 'padx': 5, 'pady': 5}
        
        # define options for opening or saving a file
        self.file_opt = options     = {}
        options['defaultextension'] = '.inp'
        options['filetypes']        = [('all files', '.inp')]
        options['initialdir']       = TopLocation
        options['initialfile']      = 'myjob.inp'
        options['parent']           = parent
        options['title']            = 'This is a title'
        
        # define options for opening or saving a folder
        self.folder_opt = options   = {}
        options['defaultextension'] = '.inp'
        options['filetypes']        = [('all files', '.inp')]
        options['initialdir']       = TopLocation
        options['initialfile']      = 'myjob.inp'
        options['parent']           = parent
        options['title']            = 'This is a title'
        
        self.QueueRunning = False
        
        with open(TopLocation+'RunQueue.txt','w') as f:
            f.write('False')
        
        
        ## File list:
        # Label
        fileListLabel   = Label(self, text="File List: [Job name, path, cpus, gpus, priority, restart]")
        fileListLabel.grid(row=incrementLoc, column=0,pady=4, columnspan=5)
        # Text
        incrementLoc=incrementLoc+1
        self.fileList   = Text(self)
        self.fileList.insert(INSERT, '')
        self.fileList.grid(row=incrementLoc, column=0, columnspan=5, padx=5, 
                           sticky=E+W+S+N)
        createToolTip(self.fileList, 
                      "This text field represents the queue to be run. It can be modified here or there: %sJobList.txt while the queue is running."%TopLocation)
        
        
        with open(TopLocation+'JobList.txt','r') as f:                          # Open Job list
            textFile = f.readlines()
            self.fileList.delete(1.0,END)
        processesList = psutil.pids()
        for proc in processesList:
            p = psutil.Process(proc)
            try:
                p.name()
            except psutil.AccessDenied:
                continue
            if (p.name()=='standard.exe' or p.name()=='explicit.exe' or p.name()=='pre.exe' or p.name()=='explicit_dp.exe'):
                i=0
                jobCpus='1'
                jobGpus='0'
                for line in p.cmdline():
                    if line     == '-job':
                        jobname = p.cmdline()[i+1]
                    elif line   == '-indir':
                        jobdir  = p.cmdline()[i+1]
                    elif line   == '-cpus':
                        jobCpus = p.cmdline()[i+1]
                    elif line   == '-gpus':
                        jobGpus = p.cmdline()[i+1]
                    i+=1
                for line in textFile:
                    if line[0]!='#' and line[0]!='\n':
                        self.fileList.insert(END,line)
                    elif (line=='#%s.inp||%s||%s||%s||1\n'%(jobname,jobdir.replace("\\", "/")+'/',jobCpus,jobGpus) 
                            or 
                            line=='#%s.inp||%s||%s||%s||2\n'%(jobname,jobdir.replace("\\", "/")+'/',jobCpus,jobGpus) 
                            or
                            line=='#%s.inp||%s||%s||%s||3\n'%(jobname,jobdir.replace("\\", "/")+'/',jobCpus,jobGpus)):
                        self.fileList.insert(END,line)
        
        ## Add File
        # Label
        incrementLoc = incrementLoc+1
        addFileLabel = Label(self, text="Add Job: ")
        addFileLabel.grid(row=incrementLoc, column=0, padx = 1, ipadx=1)
        # Select File
        self.selectFileButton = Button(self, 
                                       text='Select INP File', 
                                       command=self.selectFileFunc)
        self.selectFileButton.grid(row=incrementLoc, column=1,columnspan=4, 
                                   ipadx=212, ipady=1, pady=5, padx=5)
        # Select Options
        incrementLoc=incrementLoc+1
        self.cpusSelectLabel = Label(self, 
                                     text="Cpus     = ")
        self.cpusSelectLabel.grid(row=incrementLoc, column=1, sticky='w', padx=5)
        self.cpusSelect = Entry(self)
        self.cpusSelect.insert(END,defCpusNumb)
        self.cpusSelect.grid(row=incrementLoc, column=2, pady=5)
        
        self.gpusSelectLabel = Label(self, 
                                     text="Gpus    = ")
        self.gpusSelectLabel.grid(row=incrementLoc, column=3, sticky='w', padx=5)
        self.gpusSelect = Entry(self)
        self.gpusSelect.insert(END,defGpusNumb)
        self.gpusSelect.grid(row=incrementLoc, column=4)
        
        
        incrementLoc=incrementLoc+1
        self.priorityLabel = Label(self, text="Priority = (1,2,3)")
        self.priorityLabel.grid(row=incrementLoc, column=1, sticky='w', padx=5)
        createToolTip(self.priorityLabel, 
                      "Jobs assigned with a priority of 1 will be executed first")
        self.prioritySelect = Entry(self)
        self.prioritySelect.insert(END,'3')
        self.prioritySelect.grid(row=incrementLoc, column=2)
        createToolTip(self.prioritySelect, 
                      "Jobs assigned with a priority of 1 will be executed first")
        
        self.restartSelectLabel = Label(self, text="Restart = (oldjob, N)")
        self.restartSelectLabel.grid(row=incrementLoc, column=3, sticky='w', padx=5)
        self.restartSelect = Entry(self)
        self.restartSelect.insert(END, 'N')
        self.restartSelect.grid(row=incrementLoc, column=4)
        
        # Button
        incrementLoc=incrementLoc+1
        self.addFileButton = Button(self, 
                               text='Add Job to the list', 
                               command=self.addJobFunc)
        self.addFileButton.grid(row=incrementLoc, column=1, columnspan=4, 
                                ipadx=202, pady=10, ipady=1, padx=5)
        
        
        # Separator
        incrementLoc = incrementLoc+1
        Separator(self,orient=HORIZONTAL).grid(row=incrementLoc, columnspan=5,
                sticky="ew", pady=0)
        
        ## Abaqus version
        # Label
        incrementLoc = incrementLoc+1
        abqVersionLabel = Label(self, text='Abaqus version: ')
        abqVersionLabel.grid(row=incrementLoc, column=0, pady=10, ipady=1)
        createToolTip(abqVersionLabel, 
                      "Version of Abaqus to be used: "+', '.join(defAbqVersion))
       # Select Version
        self.abqVersion = Entry(self)
        self.abqVersion.insert(END, defAbqVersion[0])
        self.abqVersion.grid(row=incrementLoc, column=1)
        createToolTip(self.abqVersion, 
                      "Version of Abaqus to be used: "+', '.join(defAbqVersion))
        
        ## Run all file in Folder
        # Button
        self.runAllFilesButton = Button(self,
                                    text='Run all files in Folder',
                                    command=self.runAllFiles)
        self.runAllFilesButton.grid(row=incrementLoc, column=2, columnspan=3, 
                                    ipadx=100, pady=5, ipady=1, padx=5, 
                                    sticky="e")
        
        Separator(self,orient=VERTICAL).grid(row=incrementLoc, rowspan=1, 
                column=2, sticky="nsw", padx=17, ipady=0)
        
        # Separator
        incrementLoc = incrementLoc+1
        Separator(self,orient=HORIZONTAL).grid(row=incrementLoc, columnspan=5, 
                sticky="ew", pady=0)
        
        ## Run Queue
        # Button
        incrementLoc=incrementLoc+1
        self.runQueueButton = Button(self, 
                                     text='Run the Queue', 
                                     command=self.runQueueFunc)
        self.runQueueButton.grid(row=incrementLoc, column=0, ipadx=50, 
                                 pady=10, sticky=N, padx=5)
        
#        ## Terminate Job
#        # Button
#        self.termCurrJobButton = Button(self, 
#                                         text='Terminate Current Job', 
#                                         command=self.termCurrJob, 
#                                         state=DISABLED)
#        self.termCurrJobButton.grid(row=incrementLoc, column=1, 
#                                    columnspan=3,ipadx=20)
        
        ## Quit
        # Button
        quitButton = Button(self, 
                            text = "QUIT", 
                            fg="red", 
                            command=self.quit_pressed)
        quitButton.grid(row=incrementLoc, column=4, 
                        ipadx=50, sticky='e', padx=5)
        createToolTip(quitButton, 
                      "If a job is running, it will keep running but the rest of the queue WILL NOT be executed.")
        
        
        # Separator
        incrementLoc = incrementLoc+1
        Separator(self,orient=HORIZONTAL).grid(row=incrementLoc, columnspan=5,
            sticky="ew", pady=2)
        
        ## Tail .MSG File
        # Button
        incrementLoc=incrementLoc+1
        self.tailMsgFileButton = Button(self, text='Msg File',
                                        command=lambda: self.tailMsgFile('msg'),)
        self.tailMsgFileButton.grid(row=incrementLoc, column=0, 
                                    columnspan=3, ipadx=20, pady=4)
            
        
        ## Tail .STA File
        # Button
        self.tailStaFileButton = Button(self, text='Sta File',
                                        command=lambda: self.tailMsgFile('sta'),)
        self.tailStaFileButton.grid(row=incrementLoc, column=1, columnspan=3, 
                                    ipadx=20, pady=4)
        
        ## Tail .LOG File
        # Button
        self.tailLogFileButton = Button(self, text='Log File',
                                        command=self.tailLogFile,)
        self.tailLogFileButton.grid(row=incrementLoc, column=2, columnspan=3, 
                                    ipadx=20, pady=4)
        createToolTip(self.tailLogFileButton, 
                      "Displays the Log file: %sLogFile.txt"%TopLocation)
        
        # Separator
        incrementLoc = incrementLoc+1
        Separator(self,orient=HORIZONTAL).grid(row=incrementLoc, columnspan=5,
            sticky="ew", pady=2)
        
        ## Kill job via PID
        # Label
        incrementLoc = incrementLoc+1
        killPidJobLabel = Label(self, 
                                     text="List of the jobs running on this machine")
        killPidJobLabel.grid(row=incrementLoc, column=0, padx=5)
        # Text
        incrementLoc = incrementLoc+1
        self.runningJobs = Text(self,height=5)
        self.runningJobsListBuffer=[]
        self.jobListTextBoxBuffer=''
        self.jobListTextFileBuffer=''
        self.runningQueueTextFileBuffer = ''
        self.q = Queue.Queue()
        t = threading.Thread(target=self.jobsRunning, args=[self.q])
        t.daemon = True
        t.start()
        self.update(self.q)
        self.runningJobs.grid(ipadx=4, padx=4, ipady=4, 
                              pady=4, columnspan=5, rowspan=4, 
                              sticky='nwe', row=incrementLoc)
        
        # Button
        incrementLoc = incrementLoc +1 +5
        self.killPidJobButton = Button(self, 
                                       text="Kill job via PID",
                                       command=self.killPidJob)
        self.killPidJobButton.grid(row=incrementLoc, column=0,
                                   ipadx=50, sticky='e', padx=5, pady=5)
        
        ## Terminate Jobs
        # Button
        self.termJobsButton = Button(self, 
                                         text='Terminate Jobs', 
                                         command=self.termJobs, 
                                         state=DISABLED)
        self.termJobsButton.grid(row=incrementLoc, column=1, 
                                    columnspan=3,ipadx=20)

        if self.fileList.get("1.0",END)!='\n':
            self.runQueueFunc()




###############################################################################
# FUNCTION ASSOCIATED WITH THE BUTTONS ########################################
###############################################################################

###############################################################################
    def selectFileFunc(self):
        """Returns an opened file in read mode."""
        self.selectedFile = tkFileDialog.askopenfilename(**self.file_opt)       # Dialog Box
        
        pathComplete=''
        for pathPart in range(0,len(self.selectedFile.split('/'))-1):
            pathComplete = pathComplete+self.selectedFile.split('/')[pathPart]+'/'
        self.selectedFilePath = pathComplete
        self.selectedFileName = self.selectedFile.split('/')[-1]
        
        if (self.selectedFilePath!='' and self.selectedFileName!=''):
            #print('Path = '+self.selectedFilePath)
            #print('Name = '+self.selectedFileName)
            tempVar = 1
        else:
            print('No file selected')
        
        if self.selectedFileName != '':
            self.selectFileButton.config(text='Change INP File | '+self.selectedFileName)
            self.selectFileButton.grid(row=2, column=1,columnspan=4, ipadx=20, ipady=1, pady=5)
        else: 
            self.selectFileButton.config(text='Select INP File')
            self.selectFileButton.grid(row=2, column=1,columnspan=4, 
                                   ipadx=212, ipady=1, pady=5, padx=5)


###############################################################################
    def addJobFunc(self):
        """Adding the selected file to the File List"""
        try:
            int(self.cpusSelect.get())                                          # Convert cpus and gpus input to integer
            int(self.gpusSelect.get())
            
            if self.selectedFileName!='' or self.selectedFilePath!='':
                jobList =self.fileList.get("1.0",END)                           # Read the File List
                if jobList == '\n':
                    self.fileList.delete(1.0,END)                               # Delete the console
                    self.fileList.insert(INSERT, self.selectedFileName+'||'+
                                            self.selectedFilePath+'||'+
                                            self.cpusSelect.get()+'||'+
                                            self.gpusSelect.get()+'||'+
                                            self.prioritySelect.get()+'||'+
                                            self.restartSelect.get())
                else:
                    self.fileList.delete(1.0,END)                               # Delete the console
                    self.fileList.insert(INSERT, jobList+
                                            self.selectedFileName+'||'+
                                            self.selectedFilePath+'||'+
                                            self.cpusSelect.get()+'||'+
                                            self.gpusSelect.get()+'||'+
                                            self.prioritySelect.get()+'||'+
                                            self.restartSelect.get())
                self.selectFileButton.config(text='Select INP File')
                self.selectFileButton.grid(row=2, column=1,columnspan=4, 
                                   ipadx=212, ipady=1, pady=5, padx=5)
                print('Job %s added to the queue'%self.selectedFileName)
            else:
                self.displayErrorWindow('Please select a file, CPUS number, GPUS number and Priority')
        except AttributeError:
            self.displayErrorWindow('Please select a file, CPUS number, GPUS number and Priority')
        except ValueError:
             self.displayErrorWindow('Please select a valid number of cpus and gpus to be used. And priority number.')

###############################################################################
    def runQueueFunc(self):
        """Run the Files written in the File List"""
        if (self.abqVersion.get() in defAbqVersion):
            
            self.runQueueButton.config(state=DISABLED,text='Queue Running')
            self.queue  = Queue.Queue()
            
            jobList     =self.fileList.get("1.0",END)                           # Read the console
            ThreadedTask(self.queue,self).start()                               # Instantiate and launch the parallel thread
            self.master.after(100, self.process_queue)
        else:
            self.displayErrorWindow('Please select a valid abaqus version: \n '+', '.join(defAbqVersion))

###############################################################################
    def process_queue(self):
        """Internal function handling the parallel thread"""
        try:
            msg = self.queue.get(0)
            print(msg)
        except Queue.Empty:
            try:
                self.master.after(100,self.process_queue)
            except SystemError:
                print('System Error: '+self.process_queue)

###############################################################################
    def quit_pressed(self):
        """Kill the GUI and the associated threads"""
        self.parent.destroy()

###############################################################################
    def displayErrorWindow(self,errorMess,destroy=True):
        """Creating a separate windows to display a message"""
        if destroy==True:
            try:
                self.errWindow.destroy()
            except:
                pass
        self.errWindow  = Toplevel(self)
        self.errWindow.geometry('+%d+%d'%(10,10))
        
        addErrorLabel   = Label(self.errWindow, text=errorMess)
        addErrorLabel.pack(padx = 10,pady = 10)
        
        okButton        = Button(self.errWindow, text='OK',
                         command=self.errWindow.destroy)
        okButton.pack(padx=10,pady=10)

###############################################################################
    def termCurrJob(self):
        """Kill the job that is running"""
        currJob = self.termCurrJobButton['text']
        msgFileCreated = False
        i = 0
        while msgFileCreated==False and i<10:
            if (os.path.isfile(currJob.split('Terminate: ')[1]+'.msg')==False 
                and os.path.isfile(currJob.split('Terminate: ')[1]+'.sta')==False):
                print('The script will wait until a .msg or a .sta file is created for this job')
                i=i+1
                time.sleep(3)
            else:
                msgFileCreated = True
            
        cmd = "%s job=%s terminate"%(self.abqVersion.get(), 
                                     currJob.split('Terminate: ')[1])
        print(cmd)
        currPath = os.getcwd()
        os.chdir(currPath)
        try:
            p = subprocess.Popen(cmd, 
                                 cwd=currPath, 
                                 shell = True, 
                                 stdout=subprocess.PIPE)
            print(p.stdout.read())
            time.sleep(2.)
            p.kill()
            self.runQueueButton.config(state='normal', text='Run the Queue')
            self.addFileButton.config(state='normal')
        except OSError as e:
            print(e)
            print('The Job couldnt be killed! Please kill it from the console')
        except Error as e:
            print(e)

###############################################################################
    def termJobs(self):
        """Select the jobs to be terminated"""
        
        self.termJobsWindow = Toplevel(self)
        i=0
        self.var=[]
        jobsCheckboxes = []
        for job in self.runningJobsListDict:
            self.var.append(StringVar())
            jobsCheckboxes.append(Checkbutton(self.termJobsWindow, 
                                     text       = '%s\%s.inp'%(self.runningJobsListDict[i]['dir'],self.runningJobsListDict[i]['inp']),
                                     variable   = self.var[i], 
                                     onvalue    = '%s\%s'%(self.runningJobsListDict[i]['dir'],self.runningJobsListDict[i]['inp']), 
                                     offvalue   = 'not'))
            jobsCheckboxes[i].select()
            jobsCheckboxes[i].pack(padx=20,pady=20)
            i+=1
        
        OkButton = Button(self.termJobsWindow, text='Kill Jobs', command=self.termSelectedJobs)
        OkButton.pack(pady=5)
        CancelButton = Button(self.termJobsWindow, text='Cancel',command=self.termJobsWindow.destroy)
        CancelButton.pack(pady=5)

###############################################################################
    def termSelectedJobs(self):
        """Terminate the selected jobs"""
        
        for job in self.var:
            if job.get()!='not':
                print(job.get())
                directoryPath   = '\\'.join(job.get().split('\\')[:-1])
                inpFile         = job.get().split('\\')[-1]
                print('Directory path: %s'%directoryPath)
                print('Inp file name: %s'%inpFile)
                os.chdir(directoryPath)
                cmd = "%s job=%s terminate"%(self.abqVersion.get(), 
                                         inpFile)
                print(cmd)
                try:
                    p = subprocess.Popen(cmd,
                                         cwd=directoryPath,
                                         shell=True,
                                         stdout=subprocess.PIPE)
                    print(p.stdout.read())
                    time.sleep(2.)
                    p.kill()
                except OSError as e:
                    print(e)
                    print('The Job couldnt be killed! Please kill it from the console')
                except Error as e:
                    print(e)
        self.termJobsButton.config(state=DISABLED)
        self.termJobsWindow.destroy()

###############################################################################
    def tailMsgFile(self,ext):
        """Read the Msg file of the jobs that are running"""
        
        try:
            for window in self.dispMsgFileWindow:
                window.destroy()
        except:
            pass
        try:
            self.errWindow.destroy()
        except:
            pass
        
        if self.runningJobsListDict==[]:
            self.displayErrorWindow('No msg file could be found. Please make sure that at least one job is running and that its msg file has been created')
        else:
            self.dispMsgFileWindow = []
            self.incrementMsgFile = 0
            for proc in self.runningJobsListDict:
                if proc['kind']=='standard.exe':
                    inpFileStr=''
                    try:
                        with open(proc['dir']+'\\'+proc['inp']+'.'+ext) as f:
                            inpFile = f.readlines()
                            for line in inpFile:
                                inpFileStr = inpFileStr+line
                        self.dispMsgFile(inpFileStr,ext,proc['dir'],proc['inp'])
                    except IOError:
                        self.displayErrorWindow('Please wait for %s.%s to be created'%(proc['inp'],ext),destroy=False)
                elif proc['kind']=='explicit.exe' or proc['kind']=='explicit_dp.exe':
                    inpFileStr=''
                    try:
                        with open(proc['dir']+'\\'+proc['inp']+'.sta') as f:
                            inpFile = f.readlines()
                            for line in inpFile:
                                inpFileStr = inpFileStr+line
                        self.dispMsgFile(inpFileStr,'sta',proc['dir'],proc['inp'])
                    except IOError:
                        self.displayErrorWindow('Please wait for %s.sta to be created'%proc['inp'],destroy=False)
                elif proc['kind']=='pre.exe':
                    self.displayErrorWindow('Please wait for %s.msg or %s.sta to be created'%(proc['inp'],proc['inp']),destroy=False)

###############################################################################
    def tailLogFile(self):
        """Read the log file"""
        
        try:
            for window in self.dispMsgFileWindow:
                window.destroy()
        except:
            pass
        
        logFileStr=''
        self.dispMsgFileWindow = []
        if (os.path.isfile(TopLocation+'LogFile.txt')==True):
            with open(TopLocation+'LogFile.txt') as f:
                logFile= f.readlines()
                for line in logFile:
                    logFileStr = logFileStr+line
                self.dispMsgFile(logFileStr,'log','')
        else:
            with open(TopLocation+'LogFile.txt','w') as f:
                f.write('')
            self.dispMsgFile(logFileStr,'log','')
            
            
            
###############################################################################
    def clearLogFile(self):
        """Erase the content of the log file"""
        
        try:
            for window in self.dispMsgFileWindow:
                window.destroy()
        except:
            pass
        
        with open(TopLocation+'LogFile.txt','w') as f:
            f.write('')
        self.dispMsgFile('','log','')
        
###############################################################################
    def dispMsgFile(self, msgFileStr,fileType,Path,fileName='File'):
        """Display the content of the msg file, sta file or log file"""
        
        
        # Create the window
        self.dispMsgFileWindow.append(Toplevel(self))
        try:
            self.dispMsgFileWindow[self.incrementMsgFile].title('Job Name: %s'%fileName)
        except AttributeError:
            self.incrementMsgFile = 0
        except IndexError:
            self.incrementMsgFile = 0
        self.dispMsgFileWindow[self.incrementMsgFile].geometry(str(GetSystemMetrics(0)/2)+'x'+str(GetSystemMetrics(1)-75)+'+0+0')
        
        scrollbar   = Scrollbar(self.dispMsgFileWindow[self.incrementMsgFile])
        scrollbar.pack(side=RIGHT, fill=Y)
        
        self.listbox = []
        self.listbox.append(Text(self.dispMsgFileWindow[self.incrementMsgFile], yscrollcommand=scrollbar.set, height='25', width='100'))
        self.listbox[-1].insert(INSERT, msgFileStr)
        self.listbox[-1].see(END)
        self.listbox[-1].pack(side=LEFT, fill=BOTH)
        scrollbar.config(command=self.listbox[-1].yview)
        inc = self.incrementMsgFile
        okButton    = Button(self.dispMsgFileWindow[inc], text='OK',
                             command= lambda: self.destroyTailedFile(inc))
        okButton.pack(padx=10,pady=10)
        
        # Fill the window with the texts
        if fileType     =='sta':
            updateButton = Button(self.dispMsgFileWindow[self.incrementMsgFile], text='Tail STA',
                command=lambda: self.buttonFunc(fileType,Path,fileName,inc))
            updateButton.pack(padx=10,pady=10)
        elif fileType   =='msg':
            updateButton = Button(self.dispMsgFileWindow[self.incrementMsgFile], text='Tail MSG',
                command=lambda: self.buttonFunc(fileType,Path,fileName,inc))
            updateButton.pack(padx=10,pady=10)
        elif fileType   =='log':
            updateButton = Button(self.dispMsgFileWindow[self.incrementMsgFile], text='Update',
                command=self.tailLogFile)
            updateButton.pack(padx=10,pady=10)
            
            clearButton = Button(self.dispMsgFileWindow[self.incrementMsgFile], text='Clear Log', command=self.clearLogFile)
            clearButton.pack(padx=10,pady=200)
            
        self.incrementMsgFile += 1 

###############################################################################
    def runAllFiles(self):
        """Write all the INP files caontained in the selected \
        folder in the console"""
        
        self.dirname = str(tkFileDialog.askdirectory(parent=self, 
                                    initialdir = '%s'%TopLocation))             # Get the directory
        
        # If cancel is selected
        if not self.dirname:
            print('No folder selected')
            return
        
        print(self.dirname)
        
        try:
            int(self.cpusSelect.get())                                          # Convert cpus and gpus input to integer
            int(self.gpusSelect.get())
            
            filesInDir = os.listdir(self.dirname)
            self.selectedFileName = 'empty'
            
            for fileStr in filesInDir:
                if fileStr.split('.')[-1] == 'inp':
                    print(fileStr)
                    self.selectedFileName = fileStr
                    self.selectedFilePath = self.dirname
                else:
                    if self.selectedFileName=='empty':
                        self.displayErrorWindow('The folder does not contain any inp file')
                    self.selectedFileName = ''
                    self.selectedFilePath = ''
                if self.selectedFileName!='' or self.selectedFilePath!='':
                    jobList =self.fileList.get("1.0",END)                       # Read the File List
                    if jobList == '\n':
                        self.fileList.delete(1.0,END)                           # Delete the console
                        self.fileList.insert(INSERT, self.selectedFileName+'||'+
                                                self.selectedFilePath+'||'+
                                                self.cpusSelect.get()+'||'+
                                                self.gpusSelect.get()+'||'+
                                                self.prioritySelect.get()+'||'+
                                                self.restartSelect.get())
                    else:
                        self.fileList.delete(1.0,END)                           # Delete the console
                        self.fileList.insert(INSERT, jobList+
                                                self.selectedFileName+'||'+
                                                self.selectedFilePath+'||'+
                                                self.cpusSelect.get()+'||'+
                                                self.gpusSelect.get()+'||'+
                                                self.prioritySelect.get()+'||'+
                                                self.restartSelect.get())
                    self.selectFileButton.config(text='Select INP File')
                    self.selectFileButton.grid(row=2, column=1,columnspan=4, ipadx=200, ipady=1, pady=5, padx=5)
                    print('job added')
        except AttributeError as e:
            self.displayErrorWindow('Please select a file, CPUS number, GPUS number and Priority\n%s'%e)
        except ValueError:
             self.displayErrorWindow('Please select a valid number of cpus and gpus to be used. And priority number.')
        except WindowsError as e:
            self.displayErrorWindow('Please select a Folder containing at least 1 .inp file.')

###############################################################################
    def killPidJob(self):
        """Creating a separate Window"""
        try:
            self.killWindow.destroy()
        except:
            pass
        self.killWindow = Toplevel(self)
        self.killWindow.geometry('+%d+%d'%(10,10))
        killLabel = Label(self.killWindow, text='Please enter the Pid of the job to be killed: ')
        killLabel.pack(padx = 10,pady = 10)
        runningProc =[]
        processesList = psutil.pids()
        for proc in processesList:
            try:
                p = psutil.Process(proc)
                if (p.name()=='standard.exe' or p.name()=='explicit.exe' or p.name()=='pre.exe' or p.name()=='explicit_dp.exe'):
                    runningProc.append(Label(self.killWindow, text=str(p)))
                    runningProc[-1].pack(padx = 10,pady = 10)
            except psutil.NoSuchProcess:
                self.killWindow.destroy()
                time.sleep(0.1)
                self.killPidJob()
                pass
        self.killText = Text(self.killWindow, height=1,width=20)
        self.killText.insert(INSERT, '')
        self.killText.pack()
        killButton = Button(self.killWindow, text='Kill',
                            command=self.killJob)
        killButton.pack(padx=10, pady=10)
        
        killWindowButton = Button(self.killWindow, text="Cancel",
                                       command=self.killWindow.destroy)
        killWindowButton.pack(padx=10,pady=10)

###############################################################################
    def killJob(self):
        """Kill the process of the selected job"""
        
        pid = self.killText.get("1.0",END)
        print(pid)
        try:
            os.kill(int(pid), signal.SIGTERM)
        except WindowsError:
            self.displayErrorWindow("The process that you selected is no longer in use.")
        self.killWindow.destroy()
    
###############################################################################
    def jobsRunning(self,parent):
        self.q.put('')
    
###############################################################################
    def update(self,parent):
        """ - Read the list of the running processes on the machine\
            - Identify the processes that correspond to a job\
            - Write them in the second console\
            
            - Synchronize the job list of the first console and the job list of the text file\
            """
        
        try:
            msgInQueue = self.q.get(0)
            self.after(40, self.update, self.q)
        except Queue.Empty:
            
            self.runningJobsListStr=[]
            self.runningJobsListDict=[]
            self.processesList = psutil.pids()
            jobname=''
            for proc in self.processesList:
                try:
                    p = psutil.Process(proc)
                    if (p.name()=='standard.exe' or p.name()=='explicit.exe' or p.name()=='pre.exe' or p.name()=='explicit_dp.exe'):
                        
                        i=0
                        jobCpus='1'
                        jobGpus='0'
                        sameJob = False
                        for line in p.cmdline():
                            if line == '-job':
                                if jobname==p.cmdline()[i+1]:
                                    sameJob = True
                                else:
                                    sameJob=False
                                jobname=p.cmdline()[i+1]
#                                print(jobname)
                            elif line == '-indir':
                                jobdir=p.cmdline()[i+1]
#                                print(jobdir)
                            elif line == '-cpus':
                                jobCpus=p.cmdline()[i+1]
#                                print(jobCpus)
                            elif line == '-gpus':
                                jobGpus=p.cmdline()[i+1]
#                                print(jobGpus)
                            i+=1
                        if sameJob!=True:
                            self.runningJobsListDict.append({'inp':jobname,'dir':jobdir,'kind':p.name(),'cpus':jobCpus,'gpus':jobGpus})
                            self.runningJobsListStr.append('-  PID: %s  |  Job type: %s  |  %s  |  %s  |  CPUS: %s  |  GPUS: %s\n'%(str(p.pid), str(p.name()),str(jobname),str(jobdir), str(jobCpus), str(jobGpus)))
                            self.termJobsButton.config(state='normal')
                except:
#                    time.sleep(0.1)
#                    self.termJobsButton.config(state=DISABLED)
                    pass
            if self.runningJobsListBuffer != self.runningJobsListStr:
                self.runningJobs.delete(1.0,END)
                for proc in self.runningJobsListStr:
                    self.runningJobs.insert(END, proc)
                    self.runningJobs.see(END)
            
            with open(TopLocation+'RunningJobList.txt','w') as f:
                for proc in self.runningJobsListStr:
                    f.write(proc)                    
            
            textBoxChanged=False
            try:
                self.jobListTextBox = self.fileList.get("1.0",END)              # Read the console
                if self.jobListTextBoxBuffer != self.jobListTextBox:
                    with open(TopLocation+'JobList.txt','w') as f:              # Import the job list in the text file
                        f.write(self.jobListTextBox)
                        textBoxChanged=True
                self.jobListTextBoxBuffer=self.jobListTextBox
                
            except:
                pass
            
            try:
                with open(TopLocation+'JobList.txt','r') as f:
                    self.jobListTextFile = f.read()
                if self.jobListTextFileBuffer != self.jobListTextFile and textBoxChanged==False:
                    self.fileList.delete(1.0,END)
                    self.fileList.insert(END,self.jobListTextFile)
                self.jobListTextFileBuffer = self.jobListTextFile
                time.sleep(0.1)
            except:
                pass
            
            if self.runningJobs.get('1.0',END)=='\n':
                try:
                    self.killPidJobButton.config(state=DISABLED)
                    self.termJobsButton.config(state=DISABLED)
                except:
                    pass
            else:
                try:
                    self.killPidJobButton.config(state='normal')
                    self.termJobsButton.config(state='normal')
                except:
                    pass
            
            # Read the run queue text file
            try:
                with open(TopLocation+'RunQueue.txt','r') as f:
                    self.runningQueueTextFile = f.read()
                    if self.QueueRunning == False and eval(self.runningQueueTextFile) == True:
                        self.runQueueFunc()
            except IOError:
                with open(TopLocation+'RunQueue.txt','w') as f:                 # If the runQueue file doesnt exist, create it
                    f.write('Not running')
            
            self.runningJobsListBuffer=self.runningJobsListStr
            self.after(40,self.update, self.q)
            
###############################################################################
    def destroyTailedFile(self,inc):
        self.dispMsgFileWindow[inc].destroy()
        
###############################################################################
    def buttonFunc(self,fileType,Path,fileName,inc):
        self.p=threading.Thread(target=self.updateFileFunc, args=[fileType,Path,fileName,inc])
        self.p.daemon = True
        self.p.start()
###############################################################################
    def updateFileFunc(self,fileType,Path,fileName,inc):
        upLines=''
        with open(Path+'\\'+fileName+'.'+fileType,'r') as f:
            Doc = f.read()
        self.listbox[inc].delete(1.0,END)
        self.listbox[inc].insert(END, Doc)
        self.listbox[inc].see(END)
        while 1:
            with open(Path+'\\'+fileName+'.'+fileType,'r') as f:
                newDoc=f.read()
                upLines = newDoc[len(Doc):]
                newDoc=newDoc+upLines
                Doc=newDoc
                time.sleep(0.5)
                try:
                    self.listbox[inc].insert(END, upLines)
                    self.listbox[inc].see(END)
                except:
                    self.destroyTailedFile(inc)
                    break
                upLines=''
            
##################################################s#############################
# Handles the exceptions in the general code
    def my_handler(type,value,tb):
        logger.exception("Uncaught exception at line %s: \n%s: %s"%(traceback.extract_tb(tb)[-1][1],type.__name__,value))
        print("Uncaught exception at line %s: %s: %s"%(traceback.extract_tb(tb)[-1][1],type.__name__,value))
    sys.excepthook = my_handler
    
def closeNotepadFile(textFile):
    pList=psutil.pids()
    for proc in pList:
        p=psutil.Process(proc)
        if p.name()=='notepad.exe' and p.cmdline()[1]==TopLocation+textFile:
                os.kill(int(proc), signal.SIGTERM)
    
def main():
###############################################################################
# Handles the exceptions in the TkInter instance
    def handle_TkInter_exception(type,value,tb):
        logger.exception("Uncaught exception at line %s: \n%s: %s"%(traceback.extract_tb(tb)[-1][1],type.__name__,value))
        print("Uncaught exception at line %s: \n%s: %s"%(traceback.extract_tb(tb)[-1][1],type.__name__,value))
    root = Tk()
    app = App(root)
    root.report_callback_exception=handle_TkInter_exception                     # Report the callback when an exception is raised
    root.mainloop()
    
if __name__ == '__main__':
        main()



