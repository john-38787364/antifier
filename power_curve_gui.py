import ant, os, usb.core, time, binascii, trainer, sys, os, pickle
from Tkinter import *
import threading

class Window(Frame):
  
  def __init__(self, master=None):
     Frame.__init__(self, master)
     self.master = master
     self.init_window()

  def init_window(self):
    self.grid()
    self.grid_columnconfigure(1, minsize=200)
    self.grid_columnconfigure(2, minsize=200)
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
    label = Label(self,textvariable=self.InstructionsVariable,anchor=W, justify=LEFT, wraplength=400)
    label.grid(row=11,column=1,sticky=W, columnspan=2)
    
    self.RunoffButton = Button(self,height=1, width=15,text="Start Runoff",command=self.StartRunoff)
    self.RunoffButton.grid(column=2,row=1)
    
    self.CalibrateButton = Button(self,height=1, width=15,text="Calibrate",command=self.Calibrate)
    self.CalibrateButton.grid(column=2,row=2)
    #self.CalibrateButton.config(state="disabled")
    
    self.FindHWbutton = Button(self,height=1, width=15,textvariable=self.StartText,command=self.ScanForHW)
    self.FindHWbutton.grid(column=2,row=3)
    #self.FindHWbutton.config(state="disabled")
    
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
    def run():
      global simulate_trainer, dev_trainer
      self.RunoffButton.config(state="disabled")
      running = True
      running = True
      rolldown = False
      rolldown_time = 0
      speed = 0
      self.InstructionsVariable.set('''
  CALIBRATION TIPS: 
  1. Tyre pressure 100psi (unloaded and cold) aim for 7.2s rolloff
  2. Warm up for 2 mins, then cycle 30kph-40kph for 30s 
  3. Speed up to above 40kph then stop pedalling and freewheel
  4. Rolldown timer will start automatically when you hit 40kph, so stop pedalling quickly!
  ''')
      
      if not simulate_trainer:
        if not dev_trainer:#if trainer not already captured
          dev_trainer = trainer.get_trainer()
          if not dev_trainer:
            self.TrainerStatusVariable.set("Trainer not detected")
            return
          else:
            self.TrainerStatusVariable.set("Trainer detected")
            trainer.initialise_trainer(dev_trainer)#initialise trainer
      else:
        self.TrainerStatusVariable.set("Simulated trainer")
      while running:#loop every 100ms
        last_measured_time = time.time() * 1000
        
        #receive data from trainer
        if simulate_trainer: 
          speed, pedecho, heart_rate, calc_power, cadence= 41, 0, 70, 200, 90
        else:
          speed, pedecho, heart_rate, calc_power, cadence = trainer.receive(dev_trainer) #get data from device
          self.SpeedVariable.set(speed)
        if speed == "Not found":
          self.TrainerStatusVariable.set("Check trainer is powered on")
        
        #send data to trainer
        resistance_level = 6
        trainer.send(dev_trainer, 0, pedecho, resistance_level)
        
        if speed > 40 or rolldown == True:
          if rolldown_time == 0:
            rolldown_time = time.time()#set initial rolldown time
          self.InstructionsVariable.set("Rolldown timer started - STOP PEDALLING! %s " % ( round((time.time() - rolldown_time),1) ) )
          rolldown = True
          if simulate_trainer:
            speed = 0
            rolldown_time = time.time() - 7
          if speed < 0.1:#wheel stopped
            running = False#break loop
            if time.time() - rolldown_time > 7.5 : 
              msg = "More pressure from trainer on tyre required"
            elif time.time() - rolldown_time < 6.5 : 
              msg = "Less pressure from trainer on tyre required"
            else:
              self.CalibrateButton.config(state="normal")
              msg = "Pressure on tyre from trainer correct"
            self.InstructionsVariable.set("Rolldown time = %s seconds\n%s" % (round((time.time() - rolldown_time),1), msg))
          
          time_to_process_loop = time.time() * 1000 - last_measured_time
          sleep_time = 0.1 - (time_to_process_loop)/1000
          if sleep_time < 0: sleep_time = 0
          time.sleep(sleep_time)
      self.RunoffButton.config(state="normal")
      
    t1 = threading.Thread(target=run)
    t1.start()
  
  def Calibrate(self):
    def run():
      #self.CalibrateButton.config(state="disabled")
      global dev_ant
      #find ANT stick
      self.ANTStatusVariable.set('Looking for ANT dongle')
      dev_ant, msg = ant.get_ant(False)
      if not dev_ant:
        self.ANTStatusVariable.set('ANT dongle not found')
        return
      self.ANTStatusVariable.set('Initialising ANT dongle')
      ant.antreset(dev_ant)
      ant.calibrate(dev_ant)#calibrate ANT+ dongle
      ant.powerdisplay(dev_ant)#calibrate as power display
      self.ANTStatusVariable.set('ANT dongle initialised')
      self.InstructionsVariable.set('Place pedals in positions instructed by power meter manufacturer. Calibration will start in 5 seconds')
      time.sleep(5)
      self.ANTStatusVariable.set('Sending calibration request')
      ant.send_ant(["a4 09 4f 00 01 aa ff ff ff ff ff ff 49 00 00"], dev_ant, False)
      i=0
      while i< 40:#wait 10 seconds
        print i
        read_val = ant.read_ant(dev_ant)
        matching = [s for s in read_val if "a4094f0001" in s] #calibration response
        print matching
        if matching:
          if matching[0][10:12]=="ac":
            self.ANTStatusVariable.set("Calibration successful")
            self.CalibratedVariable.set("True")
            self.FindHWbutton.config(state="normal")
          elif matching[0][10:12]=="af":
            self.ANTStatusVariable.set("Calibration failed")
            self.CalibratedVariable.set("False")
          else:
            self.ANTStatusVariable.set("Unknown calibration response")
            self.CalibratedVariable.set("False")
          i=999
        i += 1
        time.sleep(0.25)
      if i == 40:#timeout
        self.ANTStatusVariable.set("No calibration data received")
        self.CalibratedVariable.set("False")
      self.CalibrateButton.config(state="normal")
      self.InstructionsVariable.set("")
    
    t1 = threading.Thread(target=run)
    t1.start()
      
    
  def ScanForHW(self):

    def run():
      global simulate_trainer, dev_trainer, dev_ant
      power = 0
      resistance_level = 0
      save_data = []
      if not dev_trainer:
        #find trainer
        if simulate_trainer:
          self.TrainerStatusVariable.set("Simulated Trainer")
        else:
          dev_trainer = trainer.get_trainer()
          if not dev_trainer:
            self.TrainerStatusVariable.set("Trainer not detected")
            return
          else:
            self.TrainerStatusVariable.set("Trainer detected")
            trainer.initialise_trainer(dev_trainer)#initialise trainer
      
      #find ANT stick
      if not dev_ant:
        dev_ant, msg = ant.get_ant(False)
        self.ANTStatusVariable.set(msg)
        if not dev_ant:
          print "no ANT"
          return
      
      ant.antreset(dev_ant)#reset dongle
      ant.calibrate(dev_ant)#calibrate ANT+ dongle
      ant.powerdisplay(dev_ant)#calibrate as power display
      
      iterations = 0
      effort_level = 0
      stop_loop = False
      ###################DATA LOOP FROM ANT STICK###################
      while self.StartText.get()=="Stop":
        #print iterations
        last_measured_time = time.time() * 1000
        if iterations % 40 == 0:#inc effort level every 10s (40 iterations)
          effort_level += 10
          self.InstructionsVariable.set("Try for %s%% of your max effort level" % effort_level)
        if iterations == 360:
          iterations = 0
          effort_level = 0
          resistance_level += 1
          if resistance_level == 14:
            stop_loop = True
        if stop_loop:
          break
        iterations += 1
        try:
          #get power data
          #if os.name == 'posix': read_val = binascii.hexlify(dev_ant.read(size=256))
          #elif os.name == 'nt': read_val = binascii.hexlify(dev_ant.read(0x81,64))
          read_val = ant.read_ant(dev_ant)
          matching = [s for s in read_val if "a4094e0010" in s] #a4 09 4e 00 10 ec ff 00 be 4e 00 00 10 #10 power page be 4e accumulated power 00 00 iunstant power
          if matching:
            power = int(matching[0][22:24],16)*16 + int(matching[0][20:22],16)
            
            
          #receive data from trainer
          if simulate_trainer: 
	    speed, pedecho, heart_rate, calc_power, cadence = 20, 0, 70, 200, 90
	  else:
	    speed, pedecho, heart_rate, calc_power, cadence = trainer.receive(dev_trainer) #get data from device
	  if speed == "Not found":
            self.TrainerStatusVariable.set("Check trainer is powered on")
	  #send data to trainer
	  trainer.send(dev_trainer, 0, pedecho, resistance_level)
	  
	  self.PowerVariable.set(power)
	  self.SpeedVariable.set(speed)
	  self.ResistanceVariable.set(resistance_level)
	  save_data.append([resistance_level,speed,power])
	  
	  
        except usb.core.USBError:#nothing from stick
            pass
        time_to_process_loop = time.time() * 1000 - last_measured_time
        sleep_time = 0.25 - (time_to_process_loop)/1000
        if sleep_time < 0: sleep_time = 0
        time.sleep(sleep_time)
      ###################END DATA LOOP FROM ANT STICK###############
      #ant.send(["a4 01 4a 00 ef 00 00"],dev_ant, False)#reset ANT+ dongle
      with open('calibration.pickle', 'wb') as handle:
        pickle.dump(save_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
      
          
          
    if self.StartText.get()=="Start":
      self.StartText.set(u"Stop")
      t1 = threading.Thread(target=run)
      t1.start()
      
    else:
      self.StartText.set(u"Start")
      
dev_trainer = False
dev_ant = False
simulate_trainer = False

root = Tk()
#root.geometry("600x300")
app = Window(root)
if __name__ == "__main__":
  root.mainloop()
