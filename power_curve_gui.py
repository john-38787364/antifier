import ant, os, usb.core, time, binascii, T1932_calibration, sys, os
from Tkinter import *
import threading

class Window(Frame):
  
  def __init__(self, master=None):
     Frame.__init__(self,master)
     self.master = master
     self.init_window()

  def init_window(self):
    self.grid()
    self.StartText = StringVar()
    self.StartText.set(u"Start")
    Label(self, text="Step 1: Rundown test").grid(row=1,column=1, sticky="E")
    Label(self, text="Step 2: Calibrate power meter").grid(row=2,column=1, sticky="E")
    Label(self, text="Step 3: Runpower curve").grid(row=3,column=1, sticky="E")
    Label(self, text="Trainer Status: ").grid(row=4,column=1, sticky="E")
    Label(self, text="ANT+ Status: ").grid(row=5,column=1, sticky="E")
    Label(self, text="Calibrated: ").grid(row=6,column=1, sticky="E")
    Label(self, text="Resistance Level: ").grid(row=7,column=1, sticky="E")
    Label(self, text="Speed: ").grid(row=8,column=1, sticky="E")
    Label(self, text="Power: ").grid(row=9,column=1, sticky="E")
    Label(self, text="Instructions: ").grid(row=10,column=1, sticky="E")
    
    self.InstructionsVariable = StringVar()
    label = Label(self,textvariable=self.InstructionsVariable,anchor=W)
    label.grid(row=11,column=1,sticky=E, columnspan=2)
    
    RunoffButton = Button(self,height=1, width=15,text="Start Runoff",command=self.StartRunoff)
    RunoffButton.grid(column=2,row=1)
    
    FindHWbutton = Button(self,height=1, width=15,textvariable=self.StartText,command=self.ScanForHW)
    FindHWbutton.grid(column=2,row=3)
    
    self.TrainerStatusVariable = StringVar()
    label = Label(self,textvariable=self.TrainerStatusVariable,anchor="w")
    label.grid(row=4,column=2,sticky='EW')
    
    self.ANTStatusVariable = StringVar()
    label = Label(self,textvariable=self.ANTStatusVariable,anchor="w")
    label.grid(row=5,column=2,sticky='EW')   
    
    self.CalibratedVariable = StringVar()
    label = Label(self,textvariable=self.CalibratedVariable,anchor="w")
    label.grid(row=6,column=2,sticky='EW') 
    self.CalibratedVariable.set("False")
    
    self.ResistanceVariable = StringVar()
    label = Label(self,textvariable=self.ResistanceVariable,anchor="w")
    label.grid(row=7,column=2,sticky='EW')
    
    self.SpeedVariable = StringVar()
    label = Label(self,textvariable=self.SpeedVariable,anchor="w")
    label.grid(row=8,column=2,sticky='EW')
    
    self.PowerVariable = StringVar()
    label = Label(self,textvariable=self.PowerVariable,anchor="w")
    label.grid(row=9,column=2,sticky='EW')
    
  
  def StartRunoff(self):
    #dev = ant.get_trainer()
    #if not dev:
      #self.TrainerStatusVariable.set("Trainer not detected")
      #thread_running = False
      #return
    #else:
      #self.TrainerStatusVariable.set("Trainer detected")
    #ant.initialise_trainer(dev)#initialise trainer
    running = True
    self.InstructionsVariable.set('''
CALIBRATION TIPS: Tyre pressure 100psi (unloaded and cold)
aim for 7.2s rolloff
Warm up for 2 mins, then cycle 30kph-40kph for 30s 
Speed up to above 40kph then stop pedalling and freewheel
Rolldown timer will start automatically when 
you hit 40kph, so stop pedalling quickly!
''')
    #while running:#loop every 100ms
      #last_measured_time = time.time() * 1000
      
      
  
  def ScanForHW(self):
    global thread_running, simulate_trainer
    
    def run():
      global thread_running
      
      #find trainer
      if simulate_trainer:
	self.TrainerStatusVariable.set("Simulated Trainer")
      else:
	dev = ant.get_trainer()
	if not dev:
	  self.TrainerStatusVariable.set("Trainer not detected")
	  thread_running = False
	  return
	else:
	  self.TrainerStatusVariable.set("Trainer detected")
      
      #find ANT stick
      dev_ant, msg = ant.get_ant()
      self.ANTStatusVariable.set(msg)
      if not dev_ant:
        print "no ANT"
        thread_running = False
        return
      
      if not simulate_trainer:
	ant.initialise_trainer(dev)#initialise trainer
      ant.calibrate(dev_ant)#calibrate ANT+ dongle
      ant.powerdisplay(dev_ant)#calibrate as power display
      
      ###################DATA LOOP FROM ANT STICK###################
      while self.StartText.get()=="Stop":
        last_measured_time = time.time() * 1000
        try:
          #get power data
          if os.name == 'posix': read_val = binascii.hexlify(dev_ant.read(size=256))
          elif os.name == 'nt': read_val = binascii.hexlify(dev_ant.read(0x81,64))
          if read_val[8:10]=="10":#a4 09 4e 00 10 ec ff 00 be 4e 00 00 10 #10 power page be 4e accumulated power 00 00 iunstant power
            power = int(read_val[22:24],16)*16 + int(read_val[20:22],16)
            self.PowerVariable.set(power)
            
          #receive data from trainer
          if simulate_trainer: 
	    data = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,30,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
	  else:
	    data = dev.read(0x82,64) #get data from device
	  if len(data)>40:
	    fs = int(data[33])<<8 | int(data[32])
	  speed = round(fs/2.8054/100,1)#speed kph
	  self.SpeedVariable.set(speed)
	  
        except usb.core.USBError:#nothing from stick
            pass
        time_to_process_loop = time.time() * 1000 - last_measured_time
        sleep_time = 0.25 - (time_to_process_loop)/1000
        if sleep_time < 0: sleep_time = 0
        time.sleep(sleep_time)
      ###################END DATA LOOP FROM ANT STICK###############
      #ant.send(["a4 01 4a 00 ef 00 00"],dev_ant, False)#reset ANT+ dongle
      
          
          
    if self.StartText.get()=="Start":
      self.StartText.set(u"Stop")
      t1 = threading.Thread(target=run)
      t1.start()
      
    else:
      self.StartText.set(u"Start")

simulate_trainer = True
root = Tk()
root.geometry("600x300")
app = Window(root)
if __name__ == "__main__":
  root.mainloop()
