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
    FindHWbutton = Button(self,height=1, width=15,textvariable=self.StartText,command=self.ScanForHW)
    FindHWbutton.grid(column=1,row=0)
    
    Label(self, text="Trainer Status: ").grid(row=2,column=1, sticky="E")
    self.TrainerStatusVariable = StringVar()
    label = Label(self,textvariable=self.TrainerStatusVariable,anchor="w")
    label.grid(row=2,column=2,sticky='EW')
    Label(self, text="ANT+ Status: ").grid(row=3,column=1, sticky="E")
    self.ANTStatusVariable = StringVar()
    label = Label(self,textvariable=self.ANTStatusVariable,anchor="w")
    label.grid(row=3,column=2,sticky='EW')
    Label(self, text="Calibrated: ").grid(row=4,column=1, sticky="E")
    Label(self, text="Resistance Level: ").grid(row=5,column=1, sticky="E")
    Label(self, text="Speed: ").grid(row=6,column=1, sticky="E")
    Label(self, text="Power: ").grid(row=7,column=1, sticky="E")
    Label(self, text="Instructions: ").grid(row=8,column=1, sticky="E")
    
    self.ResistanceVariable = StringVar()
    label = Label(self,textvariable=self.ResistanceVariable,anchor="w")
    label.grid(row=5,column=2,sticky='EW')
    self.SpeedVariable = StringVar()
    label = Label(self,textvariable=self.SpeedVariable,anchor="w")
    label.grid(row=6,column=2,sticky='EW')
    self.PowerVariable = StringVar()
    label = Label(self,textvariable=self.PowerVariable,anchor="w")
    label.grid(row=7,column=2,sticky='EW')

  def ScanForHW(self):
    global thread_running
    
    def run():
      global thread_running
      
      #find trainer
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
      
      ant.initialise_trainer(dev)#initialise trainer
      ant.calibrate(dev_ant)#calibrate ANT+ dongle
      ant.powerdisplay(dev_ant)#calibrate as power display
      
      ###################DATA LOOP FROM ANT STICK###################
      while thread_running:
        last_measured_time = time.time() * 1000
        try:
          #get power data
          if os.name == 'posix': read_val = binascii.hexlify(dev_ant.read(size=256))
          elif os.name == 'nt': read_val = binascii.hexlify(dev_ant.read(0x81,64))
          if read_val[8:10]=="10":#a4 09 4e 00 10 ec ff 00 be 4e 00 00 10 #10 power page be 4e accumulated power 00 00 iunstant power
            power = int(read_val[22:24],16)*16 + int(read_val[20:22],16)
            self.PowerVariable.set(power)
        except usb.core.USBError:#nothing from stick
            pass
        time_to_process_loop = time.time() * 1000 - last_measured_time
        sleep_time = 0.25 - (time_to_process_loop)/1000
        if sleep_time < 0: sleep_time = 0
        time.sleep(sleep_time)
      ###################END DATA LOOP FROM ANT STICK###############
      ant.send(["a4 01 4a 00 ef 00 00"],dev_ant, False)#reset ANT+ dongle
          
          
          
    if not thread_running:
      thread_running = True
      t1 = threading.Thread(target=run)
      t1.start()

thread_running = False
root = Tk()
root.geometry("600x300")
app = Window(root)
if __name__ == "__main__":
  root.mainloop()