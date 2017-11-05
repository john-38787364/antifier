import ant, os, usb.core, time, binascii, trainer, sys, os, pickle
from Tkinter import *
import threading
import numpy as np
#from scipy.optimize import curve_fit

def produce_power_curve_file(save_data):#res, speed, power
  #produce custom power curve calibration file
  m="#grade:multiplier,additional\n"
  valid_levels = 0
  for res in range(0,14):
    #x=[]
    #y=[]
    nx=[]
    ny=[]
    for val in save_data:
      #if val[0] == 6:
      #  print "%s,%s" % (val[1],val[2])
      if val[0] == res:
        #print res,val[1],val[2]
        #x.append(val[1])
        #y.append(val[2])
        nx.append([val[1],1])
        ny.append(val[2])
    if len(nx)>0:
      #npx = np.array(x)
      #npy = np.array(y)
      #try:
        #params = curve_fit(fit_func, npx, npy)
      #except:
        #pass
      #[a, b] = params[0]
      #print a, b
      lsq = np.linalg.lstsq(nx, ny)
      [a, b] = lsq[0]
      #print a, b
      valid_levels += 1
      
      #power = speed x a + b
      reqspeed = 35
      reqpower= reqspeed * a + b
      res=[]
      for s in range (-100,100):#produce list of speeds at various slopes
        test_slope = s/10.0
        res.append(float(get_speed(reqpower, 0.25, 0.01, 80, test_slope ,0,0)*3.6))
  

      closest = min(res, key=lambda x:abs(x-reqspeed))#get nearest speed to requires and work out slope required to get speed at that power
      ind = res.index(closest)#get nearest slope
      slope = (-100 + ind)/10.0

      m+="%s:%s,%s\n" % (slope*3+2,a,b) # times by 3 and add 2 to slope to get general zwift range
  
  if valid_levels != 14:
    msg = "Not enough data- try again" 
  else:
    msg = "Power curve generated OK"
  calibration_file=open('power_calc_factors_custom.txt','w')
  calibration_file.write(m)
  calibration_file.close()
  return msg

def fit_func(x, a, b):
  return a*x + b

def get_speed(power,Cx,f,W,slope,headwind,elevation):
    # slope in percent
    # headwind in m/s at 10 m high
    # elevation in meters
    air_pressure = 1 - 0.000104 * elevation
    Cx = Cx*air_pressure
    G = 9.81
    headwind = (0.1**0.143) * headwind
    roots = np.roots([Cx, 2*Cx*headwind, Cx*headwind**2 + W*G*(slope/100.0+f), -power])
    roots = np.real(roots[np.imag(roots) == 0])
    roots = roots[roots>0]
    speed = np.min(roots)
    if speed + headwind < 0:
        roots = np.roots([-Cx, -2*Cx*headwind, -Cx*headwind**2 + W*G*(slope/100.0+f), -power])
        roots = np.real(roots[np.imag(roots) == 0])
        roots = roots[roots>0]
        if len(roots) > 0:
            speed = np.min(roots)  
    return speed
      
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
    Label(self, text="Step 3: Run power curve").grid(row=3,column=1, sticky="E")
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
      global dev_trainer
      self.RunoffButton.config(state="disabled")
      runoff_loop_running = True
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
      
      if not dev_trainer:#if trainer not already captured
        dev_trainer = trainer.get_trainer()
        if not dev_trainer:
          self.TrainerStatusVariable.set("Trainer not detected")
          self.RunoffButton.config(state="normal")
          return
        else:
          self.TrainerStatusVariable.set("Trainer detected")
          trainer.initialise_trainer(dev_trainer)#initialise trainer
        
      
      while runoff_loop_running:#loop every 100ms
        last_measured_time = time.time() * 1000
        
        #receive data from trainer
        speed, pedecho, heart_rate, force_index, cadence = trainer.receive(dev_trainer) #get data from device
        self.SpeedVariable.set(speed)
        if speed == "Not found":
          self.TrainerStatusVariable.set("Check trainer is powered on")
        
        #send data to trainer
        resistance_level = 6
        trainer.send(dev_trainer, resistance_level, pedecho)
        
        if speed > 40:#speed above 40, start rolldown
          self.InstructionsVariable.set("Rolldown timer started - STOP PEDALLING!")
          rolldown = True
        
        if speed <=40 and rolldown:#rolldown timer starts when dips below 40
          if rolldown_time == 0:
            rolldown_time = time.time()#set initial rolldown time
          self.InstructionsVariable.set("Rolldown timer started - STOP PEDALLING! %s " % ( round((time.time() - rolldown_time),1) ) )
          
        if speed < 0.1 and rolldown:#wheel stopped
          runoff_loop_running = False#break loop
          self.InstructionsVariable.set("Rolldown time = %s seconds (aim 7s)" % round((time.time() - rolldown_time),1))

        time_to_process_loop = time.time() * 1000 - last_measured_time
        sleep_time = 0.1 - (time_to_process_loop)/1000
        if sleep_time < 0: sleep_time = 0
        time.sleep(sleep_time)
      
      
      self.CalibrateButton.config(state="normal")
        #if speed > 40 or rolldown == True:
          #if rolldown_time == 0:
            #rolldown_time = time.time()#set initial rolldown time
          #self.InstructionsVariable.set("Rolldown timer started - STOP PEDALLING! %s " % ( round((time.time() - rolldown_time),1) ) )
          #rolldown = True
          #if speed < 0.1:#wheel stopped
            #running = False#break loop
            #if time.time() - rolldown_time > 7.5 : 
              #msg = "More pressure from trainer on tyre required"
            #elif time.time() - rolldown_time < 6.5 : 
              #msg = "Less pressure from trainer on tyre required"
            #else:
              #self.CalibrateButton.config(state="normal")
              #msg = "Pressure on tyre from trainer correct"
            #self.InstructionsVariable.set("Rolldown time = %s seconds\n%s" % (round((time.time() - rolldown_time),1), msg))
          
          #time_to_process_loop = time.time() * 1000 - last_measured_time
          #sleep_time = 0.1 - (time_to_process_loop)/1000
          #if sleep_time < 0: sleep_time = 0
          #time.sleep(sleep_time)
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
      ant.antreset(dev_ant, False)
      ant.calibrate(dev_ant, False)#calibrate ANT+ dongle
      ant.powerdisplay(dev_ant, False)#calibrate as power display
      self.ANTStatusVariable.set('ANT dongle initialised')
      self.InstructionsVariable.set('Place pedals in positions instructed by power meter manufacturer. Calibration will start in 5 seconds')
      time.sleep(5)
      self.ANTStatusVariable.set('Sending calibration request')
      ant.send_ant(["a4 09 4f 00 01 aa ff ff ff ff ff ff 49 00 00"], dev_ant, False)
      i=0
      while i< 40:#wait 10 seconds
        if i % 4 ==0:
          self.ANTStatusVariable.set('Sending calibration request %s' % (10 - (i/4)))
        read_val = ant.read_ant(dev_ant, False)
        matching = [s for s in read_val if "a4094f0001" in s] #calibration response
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
        self.ANTStatusVariable.set("No calibration data received- try again")
        self.CalibratedVariable.set("False")
      self.CalibrateButton.config(state="normal")
      self.InstructionsVariable.set("")
    
    t1 = threading.Thread(target=run)
    t1.start()
      
    
  def ScanForHW(self):#calibration loop

    def run():
      global dev_trainer, dev_ant
      power = 0
      resistance_level = 0
      save_data = []
      
      if not dev_trainer:#if trainer not already captured
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
        if not dev_ant:
          self.ANTStatusVariable.set(u"no ANT dongle found")
          return False
      self.ANTStatusVariable.set(u"ANT dongle found")

      
      ant.antreset(dev_ant, False)#reset dongle
      ant.calibrate(dev_ant, False)#calibrate ANT+ dongle
      ant.powerdisplay(dev_ant, False)#calibrate as power display
      
      iterations = 0
      rest = 1
      stop_loop = False
      
      ###################DATA LOOP FROM ANT STICK###################
      while self.StartText.get()=="Stop":
        #print iterations
        last_measured_time = time.time() * 1000
        if iterations == 240:#inc resistance level every 60s (240 iterations)
          iterations = 0
          rest = 1#go into rest mode
          resistance_level += 1
          if resistance_level == 14:
            stop_loop = True
        if stop_loop:
          self.StartText.set(u"Start")
          self.InstructionsVariable.set("Test finished. Please exit")
          break
        if rest > 0: 
          rest += 1
          self.InstructionsVariable.set("Rest for %s seconds at a slow spin in an easy gear" % int(round((40 - rest)/4)))
          if rest ==40:
            rest = 0
        else:
          iterations += 1
          self.InstructionsVariable.set("Over next %s seconds gradually increase your power from easy to near maximum" % int(round((240 - iterations)/4)))
        
        try:
          read_val = ant.read_ant(dev_ant, False)
          matching = [s for s in read_val if "a4094e0010" in s] #a4094e0010ecff00be4e000010 #10 power page be 4e accumulated power 00 00 iunstant power
          if matching:
            power = int(matching[0][22:24],16)*256 + int(matching[0][20:22],16)      
          #receive data from trainer
          speed, pedecho, heart_rate, calc_power, cadence = trainer.receive(dev_trainer) #get data from device
          if speed == "Not found":
            self.TrainerStatusVariable.set("Check trainer is powered on")
            speed = 0
          #send data to trainer
          trainer.send(dev_trainer, resistance_level, pedecho)
          
          self.PowerVariable.set(power)
          self.SpeedVariable.set(speed)
          self.ResistanceVariable.set(resistance_level)
          
          
          if rest == 0 and speed > 0:#in calibration mode and moving
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
      
      msg = produce_power_curve_file(save_data)
      self.InstructionsVariable.set(msg)
          
          
    if self.StartText.get()=="Start":
      self.StartText.set(u"Stop")
      t1 = threading.Thread(target=run)
      t1.start()
      
    else:
      self.StartText.set(u"Start")
      
dev_trainer = False
dev_ant = False

root = Tk()
#root.geometry("600x300")
app = Window(root)

if __name__ == "__main__":
  root.mainloop()
