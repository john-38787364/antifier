#based on T1932 protocol
import usb.core
import time
import ant, trainer
import sys
import binascii
import struct
import platform, glob
import os
import threading
import Tkinter
from Tkinter import *
from tkMessageBox import *

from datetime import datetime
import argparse


if os.name == 'posix':
  import serial

#powerfactor = 1
#debug = False
#simulatetrainer = False
parser = argparse.ArgumentParser(description='Program to broadcast data from USB Tacx trainer, and to receive resistance data for the trainer')
parser.add_argument('-d','--debug', help='Show debugging data', required=False, action='store_true')
parser.add_argument('-s','--simulate-trainer', help='Simulated trainer to test ANT+ connectivity', required=False, action='store_true')
parser.add_argument('-p','--power-factor', help='Adjust broadcasted power data by multiplying measured power by this factor', required=False, default="1")
args = parser.parse_args()
powerfactor = args.power_factor
debug = args.debug
simulatetrainer = args.simulate_trainer

switch = True



filename = "Head_unit_setup.txt"

try:
  f = open(filename, 'r')
except IOError:
  f= open(filename,"w+")
  f.write("This file contains information regarding Head Unit buttons and Zwift keyboard shortcuts mapping \r\n")
  f.write("PGUP \r\n")
  f.write("PGDOWN \r\n")
  f.write("0 \r\n")
  f.write("SB \r\n")
  f.close()

f.close()

f = open(filename, 'r')
fileAsList = f.readlines()

UP = fileAsList[1] 
DOWN = fileAsList[2] 
ENTER = fileAsList[3]
CANCEL = fileAsList[4]

f.close()


class PowerFactor_Window:
  def __init__(self, master):
    self.master = master
    self.frame = Tkinter.Frame(self.master)

    ###Setup GUI buttons and labels for entering power factor###

    self.buttonPwrFact = Tkinter.Button(self.frame,height=1, width=20,text=u"Set power factor",command=self.serPwrFactorbutton)
    self.buttonPwrFact.grid(column=0,row=0)

    self.PwrFactVariable = Tkinter.StringVar()
    self.entry = Tkinter.Entry(self.frame,textvariable=self.PwrFactVariable)
    self.entry.grid(column=0,row=1,sticky='EW')

    self.frame.pack()


  def serPwrFactorbutton(self):
    global powerfactor
    powerfactor = self.PwrFactVariable.get() 
    self.master.destroy()


   
class HeadUnit_Window:
  def __init__(self, master):
    self.master = master
    self.frame = Tkinter.Frame(self.master)

    ###Setup GUI buttons and labels###

    label = Tkinter.Label(self.frame,height=1, width=10,text="UP button")
    label.grid(column=0,row=0,sticky='EW')

    self.UPVariable = Tkinter.StringVar()
    self.entry = Tkinter.Entry(self.frame,textvariable=self.UPVariable)
    self.entry.grid(column=1,row=0,sticky='EW')
    self.UPVariable.set(UP)


    label = Tkinter.Label(self.frame,height=1, width=10,text="DOWN button")
    label.grid(column=0,row=1,sticky='EW')

    self.DOWNVariable = Tkinter.StringVar()
    self.entry = Tkinter.Entry(self.frame,textvariable=self.DOWNVariable)
    self.entry.grid(column=1,row=1,sticky='EW')
    self.DOWNVariable.set(DOWN)


    label = Tkinter.Label(self.frame,height=1, width=10,text="ENTER button")
    label.grid(column=0,row=2,sticky='EW')

    self.ENTERVariable = Tkinter.StringVar()
    self.entry = Tkinter.Entry(self.frame,textvariable=self.ENTERVariable)
    self.entry.grid(column=1,row=2,sticky='EW')
    self.ENTERVariable.set(ENTER)


    label = Tkinter.Label(self.frame,height=1, width=10,text="CANCEL button")
    label.grid(column=0,row=3,sticky='EW')

    self.CANCELVariable = Tkinter.StringVar()
    self.entry = Tkinter.Entry(self.frame,textvariable=self.CANCELVariable)
    self.entry.grid(column=1,row=3,sticky='EW')
    self.CANCELVariable.set(CANCEL)


    self.buttonHeadUnit = Tkinter.Button(self.frame,height=1, width=20,text=u"Update Head Unit",command=self.setHEADUNITbutton)
    self.buttonHeadUnit.grid(column=0,row=4)

    self.buttonNeedHelp = Tkinter.Button(self.frame,height=1, width=20,text=u"Need Help?",command=self.NEEDHELPbutton)
    self.buttonNeedHelp.grid(column=1,row=4)

    self.frame.pack()



  def setHEADUNITbutton(self):
    global UP,DOWN,ENTER,CANCEL
    
    UP = self.UPVariable.get()
    DOWN = self.DOWNVariable.get()
    ENTER = self.ENTERVariable.get()
    CANCEL = self.CANCELVariable.get()

    f = open(filename, 'w+')
    f.write("This file contains information regarding Head Unit buttons and Zwift keyboard shortcuts mapping \r\n")
    f.write(UP + '\n')
    f.write(DOWN + '\n')
    f.write(ENTER + '\n')
    f.write(CANCEL + '\n')
    f.close()

    self.master.destroy()

  def NEEDHELPbutton(self):
    os.startfile('Zwift_shortcuts.txt')


        
class Window(Frame):
  def __init__(self, master=None):
    Frame.__init__(self,master)
    self.master = master
    self.init_window()


  def init_window(self):
    self.grid()

    ###Setup menu content###

    self.master.title("Antifier")
    self.master.option_add('*tearOff', False)

    # allowing the widget to take the full space of the root window
    self.pack(fill=BOTH, expand=1)

    # creating a menu instance
    menu = Menu(self.master)
    self.master.config(menu=menu)

    # create the Setup object)
    Setup = Menu(menu)

    # add commands to the Setup option
    Setup.add_command(label="Head Unit", command=self.HeadUnit_window)

    subSetup = Menu(Setup)
    subSetup.add_command(label='iFlow')
    subSetup.add_command(label='Fortius')
    Setup.add_cascade(label='Power_Curve', menu=subSetup)

    Setup.add_separator()
    Setup.add_command(label="Exit", command=self.EXITbutton)

    #added "Setup" to our menu
    menu.add_cascade(label="Setup", menu=Setup)


    # create the Options object)
    Options = Menu(menu)

    # add commands to the Options option
    Options.add_command(label="Debug", command=self.DebugButton)
    Options.add_command(label="Simulate Trainer", command=self.Simulatebutton)
    Options.add_command(label="Power Factor", command=self.PowerFactor_Window)

    #added "Options" to our menu
    menu.add_cascade(label="Options", menu=Options)



    # create the Help object
    Help = Menu(menu)

    # adds a command to the Help option.
    Help.add_command(label="Readme", command=self.Readme)
    Help.add_command(label="Zwift shortcuts", command=self.Zwift_shortcuts)

    #added "Help" to our menu
    menu.add_cascade(label="Help", menu=Help)



    ###Setup GUI buttons and labels###

    self.FindHWbutton = Tkinter.Button(self,height=1, width=15,text=u"Locate HW",command=self.ScanForHW)
    self.FindHWbutton.grid(column=0,row=0)


    label = Tkinter.Label(self,height=1, width=10,text="Trainer")
    label.grid(column=0,row=1,sticky='EW')

    self.trainerVariable = Tkinter.StringVar()
    label = Tkinter.Label(self,textvariable=self.trainerVariable,anchor="w",fg="black",bg="grey")
    label.grid(column=1,row=1,columnspan=2,sticky='EW')



    label = Tkinter.Label(self,height=1, width=10,text="ANT+")
    label.grid(column=0,row=2,sticky='EW')

    self.ANTVariable = Tkinter.StringVar()
    label = Tkinter.Label(self,textvariable=self.ANTVariable,anchor="w",fg="black",bg="grey")
    label.grid(column=1,row=2,columnspan=2,sticky='EW')


    label = Tkinter.Label(self,text="Power factor")
    label.grid(column=0,row=3,sticky='EW')

    self.PowerFactorVariable = Tkinter.StringVar()
    label = Tkinter.Label(self,textvariable=self.PowerFactorVariable,anchor="w",fg="black",bg="grey")
    label.grid(column=1,row=3,columnspan=2,sticky='EW')


    StartAPPbutton = Tkinter.Button(self,height=1, width=15,text=u"Start script",command=self.Start)
    StartAPPbutton.grid(column=0,row=4)

    StopAPPbutton = Tkinter.Button(self,height=1, width=15,text=u"Stop script",command=self.Stop)
    StopAPPbutton.grid(column=1,row=4)

    label = Tkinter.Label(self,text="Speed")
    label.grid(column=0,row=5,sticky='EW')

    self.SpeedVariable = Tkinter.StringVar()
    label = Tkinter.Label(self,textvariable=self.SpeedVariable,anchor="w",fg="black",bg="grey")
    label.grid(column=1,row=5,columnspan=2,sticky='EW')
    self.SpeedVariable.set(u"0")


    label = Tkinter.Label(self,text="Heartrate")
    label.grid(column=0,row=6,sticky='EW')

    self.HeartrateVariable = Tkinter.StringVar()
    label = Tkinter.Label(self,textvariable=self.HeartrateVariable,anchor="w",fg="black",bg="grey")
    label.grid(column=1,row=6,columnspan=2,sticky='EW')
    self.HeartrateVariable.set(u"0")

    label = Tkinter.Label(self,text="Cadence")
    label.grid(column=0,row=7,sticky='EW')

    self.CadenceVariable = Tkinter.StringVar()
    label = Tkinter.Label(self,textvariable=self.CadenceVariable,anchor="w",fg="black",bg="grey")
    label.grid(column=1,row=7,columnspan=2,sticky='EW')
    self.CadenceVariable.set(u"0")


    label = Tkinter.Label(self,text="Power")
    label.grid(column=0,row=8,sticky='EW')

    self.PowerVariable = Tkinter.StringVar()
    label = Tkinter.Label(self,textvariable=self.PowerVariable,anchor="w",fg="black",bg="grey")
    label.grid(column=1,row=8,columnspan=2,sticky='EW')
    self.PowerVariable.set(u"0")

    label = Tkinter.Label(self,text="Slope")
    label.grid(column=0,row=9,sticky='EW')

    self.SlopeVariable = Tkinter.StringVar()
    label = Tkinter.Label(self,textvariable=self.SlopeVariable,anchor="w",fg="black",bg="grey")
    label.grid(column=1,row=9,columnspan=2,sticky='EW')
    self.SlopeVariable.set(u"0")



  def PowerFactor_Window(self):
    self.PowerFactor_Window = Tkinter.Toplevel(self.master)
    self.app = PowerFactor_Window(self.PowerFactor_Window)

  def HeadUnit_window(self):
    self.HeadUnitWindow = Tkinter.Toplevel(self.master)
    self.app = HeadUnit_Window(self.HeadUnitWindow)


  def Readme(self):
    os.startfile('README.txt')

  def Zwift_shortcuts(self):
    os.startfile('Zwift_shortcuts.txt')

  def EXITbutton(self):
    self.destroy()
    exit()
    
  def DebugButton(self):
    global debug
    debug = True
 
  def Simulatebutton(self):
    global simulatetrainer
    simulatetrainer = True

  def Stop(self):
    global switch  
    switch = False  


  def ScanForHW(self):
    global dev_trainer, dev_ant, simulatetrainer
    #get ant stick
    print "get ant stick"
    if not dev_ant:
      dev_ant, msg = ant.get_ant(debug)
      if not dev_ant:
        self.ANTVariable.set(u"no ANT dongle found")
        return
    self.ANTVariable.set(u"ANT dongle found")


    self.PowerFactorVariable.set(powerfactor)
    print "get trainer"
    #find trainer model for Windows and Linux
    if not dev_trainer:
      #find trainer
      if simulatetrainer:
        self.trainerVariable.set(u"Simulated Trainer")
      else:
        dev_trainer = trainer.get_trainer()
        if not dev_trainer:
          self.trainerVariable.set("Trainer not detected")
          return
        else:
          self.trainerVariable.set("Trainer detected")
          trainer.initialise_trainer(dev_trainer)#initialise trainer
          print "reset ant stick"
    ant.antreset(dev_ant)#reset dongle
    print "calibrate ant stick"
    ant.calibrate(dev_ant)#calibrate ANT+ dongle
    print "calibrate ant stick FE-C"
    ant.master_channel_config(dev_ant)#calibrate ANT+ channel FE-C
    print "calibrate ant stick HR"
    ant.second_channel_config(dev_ant)#calibrate ANT+ channel HR





  def Start(self):
  
    def run():
      global dev_ant, dev_trainer, simulatetrainer
      resistance=0#set initial resistance level
      speed,cadence,power,heart_rate=(0,)*4#initialise values
      grade = 0
      accumulated_power = 0
      heart_beat_event_time = time.time() * 1000
      heart_beat_event_time_start_cycle = time.time() * 1000
      heart_toggle = 0
      heart_beat_count = 0

      eventcounter=0
      #p.44 [10] general fe data, [19] eqpt type trainer, [89] acc value time since start in 0.25s r/over 64s, [8c] acc value time dist travelled in m r/over 256m, 
      #[8d] [20] speed lsb msb 0.001m/s, [00] hr, [30] capabilities bit field
      accumulated_time = time.time()*1000
      distance_travelled = 0
      last_dist_time = time.time()*1000
      
      #p.60 [19] specific trainer data, [10] counter rollover 256, [5a] inst cadence, [b0] acc power lsb, [47] acc power msb (r/over 65536W), [1b] inst power lsb, 
      #[01] bits 0-3 inst power MSB bits 4-7 trainer status bit, [30] flags bit field

      while switch == True:  
        #print "Running"
        last_measured_time = time.time() * 1000
        if eventcounter >= 256:
          eventcounter = 0
        ####################GET DATA FROM TRAINER####################
        if simulatetrainer: 
          speed, pedecho, heart_rate, calc_power, cadence = 20, 0, 70, 200, 90
        else:
          speed, pedecho, heart_rate, calc_power, cadence = trainer.receive(dev_trainer) #get data from device
        if debug == True: print speed, pedecho, heart_rate, calc_power, cadence
        
        ####################SEND DATA TO TRAINER####################
        #send resistance data to trainer   
        if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"GRADE", grade*2,"%"
        if not simulatetrainer:
          trainer.send(dev_trainer, grade, pedecho)
        
        ####################BROADCAST AND RECEIVE ANT+ data####################
        if calc_power >= 4094:
          calc_power = 4093
        accumulated_power += calc_power
        if accumulated_power >= 65536:
          accumulated_power = 0

        if (eventcounter + 1) % 66 == 0 or eventcounter % 66 == 0:#send first and second manufacturer's info packet
          newdata = "a4 09 4e 00 50 ff ff 01 0f 00 85 83 bb 00 00"
          
        elif (eventcounter+32) % 66 == 0 or (eventcounter+33) % 66 == 0:#send first and second product info packet
          newdata = "a4 09 4e 00 51 ff ff 01 01 00 00 00 b2 00 00"
        
        elif eventcounter % 3 == 0:#send general fe data every 3 packets
          accumulated_time_counter = int((time.time()*1000 - accumulated_time)/1000/0.25)# time since start in 0.25 seconds
          if accumulated_time_counter >= 256:#rollover at 64 seconds (256 quarter secs)
            accumulated_time_counter = 0
            accumulated_time = time.time()*1000
          newdata = '{0}{1}{2}'.format('a4 09 4e 00 10 19 ', hex(accumulated_time_counter)[2:].zfill(2), ' 8c 8d 20 00 30 72 00 00') # set time
          distance_travelled_since_last_loop = (time.time()*1000 - last_dist_time)/1000 * speed * 1000/3600#speed reported in kph- convert to m/s
          last_dist_time = time.time()*1000#reset last loop time
          distance_travelled += distance_travelled_since_last_loop
          if distance_travelled >= 256:#reset at 256m
            distance_travelled = 0
          newdata = '{0}{1}{2}'.format(newdata[:21], hex(int(distance_travelled))[2:].zfill(2), newdata[23:]) # set distance travelled  
          hexspeed = hex(int(speed*1000*1000/3600))[2:].zfill(4)
          newdata = '{0}{1}{2}{3}{4}'.format(newdata[:24], hexspeed[2:], ' ' , hexspeed[:2], newdata[29:]) # set speed
          newdata = '{0}{1}{2}'.format(newdata[:36], ant.calc_checksum(newdata), newdata[38:])#recalculate checksum
          if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"FE DATA",newdata
        
        else:#send specific trainer data
          newdata = '{0}{1}{2}'.format('a4 09 4e 00 19 ', hex(eventcounter)[2:].zfill(2), ' 5a b0 47 1b 01 30 6d 00 00') # increment event count
          if cadence >= 254:
            cadence=253
          newdata = '{0}{1}{2}'.format(newdata[:18], hex(cadence)[2:].zfill(2), newdata[20:])#instant cadence
          hexaccumulated_power = hex(int(accumulated_power))[2:].zfill(4)
          newdata = '{0}{1}{2}{3}{4}'.format(newdata[:21], hexaccumulated_power[2:], ' ' , hexaccumulated_power[:2], newdata[26:]) # set accumulated power
          hexinstant_power = hex(int(calc_power))[2:].zfill(4)
          hexinstant_power_lsb = hexinstant_power[2:]
          newdata = '{0}{1}{2}'.format(newdata[:27], hexinstant_power_lsb, newdata[29:])#set power lsb byte
          hexinstant_power_msb = hexinstant_power[:2]
          bits_0_to_3 = bin(int(hexinstant_power_msb,16))[2:].zfill(4)
          power_msb_trainer_status_byte = '0000' + bits_0_to_3
          newdata = '{0}{1}{2}'.format(newdata[:30], hex(int(power_msb_trainer_status_byte))[2:].zfill(2), newdata[32:])#set mixed trainer data power msb byte
          newdata = '{0}{1}{2}'.format(newdata[:36], ant.calc_checksum(newdata), newdata[38:])#recalculate checksum
        
        if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"TRAINER DATA",newdata
        reply = ant.send_ant([newdata], dev_ant, debug)
        #
        #if rv[6:8]=="33":
        #rtn = {'grade' : int(rv[18:20]+rv[16:18],16) * 0.01 - 200} #7% in zwift = 3.5% grade in ANT+  
        matching = [s for s in reply if "a4094f0033" in s]#a4094f0033ffffffff964ffff7 is gradient message
        if matching:
          grade = int(matching[0][20:22]+matching[0][18:20],16) * 0.01 - 200
          
        ####################HR#######################
        #HR format
        #D00000693_-_ANT+_Device_Profile_-_Heart_Rate_Rev_2.1.pdf
        #[00][FF][FF][FF][55][03][01][48]p. 18 [00] bits 0:6 data page no, bit 7 toggle every 4th message, [ff][ff][ff] (reserved for page 0), [55][03] heart beat event time [lsb][ msb] rollover 64s, [01] heart beat count rollover 256, [instant heart rate]max 256
        #[00][FF][FF][FF][55][03][01][48]
        #[00][FF][FF][FF][AA][06][02][48]
        #[00][FF][FF][FF][AA][06][02][48]
        #[80][FF][FF][FF][AA][06][02][48]
        #[80][FF][FF][FF][AA][06][02][48]
        #[80][FF][FF][FF][FF][09][03][48]
        #[80][FF][FF][FF][FF][09][03][48]
        #[00][FF][FF][FF][FF][09][03][48]
        #[00][FF][FF][FF][54][0D][04][48]
        #[00][FF][FF][FF][54][0D][04][48]
        #[00][FF][FF][FF][54][0D][04][48]
        
        #every 65th message send manufacturer and product info -apge 2 and page 3
        #[82][0F][01][00][00][3A][12][48] - [82] page 2 with toggle on (repeat 4 times)
        #[83][01][01][33][4F][3F][13][48] - [83] page 3 with toggle on 
        
        #if eventcounter > 40: heart_rate = 100 #comment out in production
        if heart_rate>0:#i.e. heart rate belt attached
          if eventcounter % 4 == 0:#toggle bit every 4 counts
            if heart_toggle == 0: heart_toggle = 128
            else: 
              heart_toggle = 0
          
          #check if heart beat has occurred as tacx only reports instanatenous heart rate data
          #last heart beat is at heart_beat_event_time
          #if now - heart_beat_event_time > time taken for hr to occur, trigger beat. 70 bpm = beat every 60/70 seconds
          if (time.time()*1000 - heart_beat_event_time) > (60 / heart_rate)*1000:
            heart_beat_count += 1#increment heart beat count
            heart_beat_event_time = time.time()*1000#reset last time of heart beat
            
          if heart_beat_event_time - heart_beat_event_time_start_cycle >= 64000:#rollover every 64s
            heart_beat_event_time = time.time()*1000#reset last heart beat event
            heart_beat_event_time_start_cycle = time.time()*1000#reset start of cycle
            
          if heart_beat_count >= 256:
            heart_beat_count = 0
          
          if heart_rate >= 256:
            heart_rate = 255
          
          hex_heart_beat_time = int((heart_beat_event_time - heart_beat_event_time_start_cycle)*1.024) # convert ms to 1/1024 of a second
          hex_heart_beat_time = hex(hex_heart_beat_time)[2:].zfill(4)
          
          hr_byte_4 = hex_heart_beat_time[2:]
          hr_byte_5 = hex_heart_beat_time[:2]
          hr_byte_6 = hex(heart_beat_count)[2:].zfill(2)
          hr_byte_7 = hex(heart_rate)[2:].zfill(2)
          
          
          if (eventcounter + 1) % 66 == 0 or eventcounter % 66 == 0:#send first and second manufacturer's info packet
            hr_byte_0 = hex(2 + heart_toggle)[2:].zfill(2)
            hr_byte_1 = "0f"
            hr_byte_2 = "01"
            hr_byte_3 = "00"
            #[82][0F][01][00][00][3A][12][48]
          elif (eventcounter+32) % 66 == 0 or (eventcounter+33) % 66 == 0:#send first and second product info packet
            hr_byte_0 = hex(3 + heart_toggle)[2:].zfill(2)
            hr_byte_1 = "01"
            hr_byte_2 = "01"
            hr_byte_3 = "33"      
            #[83][01][01][33][4F][3F][13][48]
            
          else:#send page 0
            hr_byte_0 = hex(0 + heart_toggle)[2:].zfill(2)
            hr_byte_1 = "ff"
            hr_byte_2 = "ff"
            hr_byte_3 = "ff"
            
          hrdata = "a4 09 4e 01 "+hr_byte_0+" "+hr_byte_1+" "+hr_byte_2+" "+hr_byte_3+" "+hr_byte_4+" "+hr_byte_5+" "+hr_byte_6+" "+hr_byte_7+" 02 00 00"
          hrdata = "a4 09 4e 01 "+hr_byte_0+" "+hr_byte_1+" "+hr_byte_2+" "+hr_byte_3+" "+hr_byte_4+" "+hr_byte_5+" "+hr_byte_6+" "+hr_byte_7+" "+ant.calc_checksum(hrdata)+" 00 00"
          time.sleep(0.125)# sleep for 125ms
          if debug == True: print datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],"HEART RATE",hrdata
          ant.send_ant([hrdata], dev_ant, debug)
        ####################wait ####################

        #add wait so we only send every 250ms
        time_to_process_loop = time.time() * 1000 - last_measured_time
        sleep_time = 0.25 - (time_to_process_loop)/1000
        if sleep_time < 0: sleep_time = 0
        time.sleep(sleep_time)
        eventcounter += 1

        self.SpeedVariable.set(speed)
        self.HeartrateVariable.set(heart_rate)
        self.CadenceVariable.set(cadence)
        self.PowerVariable.set(calc_power)
        self.SlopeVariable.set(grade)

      if os.name == 'posix':#close serial port to ANT stick on Linux
        dev_ant.close()

    self.FindHWbutton.config(state="disabled")
    thread = threading.Thread(target=run)  
    thread.start() 

dev_trainer = False
dev_ant = False

# root window created. Here, that would be the only window, but
# you can later have windows within windows.
root = Tk()

#root.geometry("30x220")
#frame = Frame(root)
#frame.pack()

#creation of an instance
app = Window(root)


if __name__ == "__main__":
     root.mainloop()
