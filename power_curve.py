import ant, os, usb.core, time, binascii, T1932_calibration, sys
import Tkinter as tkinter

def update_status(label, status):
  label.config(text=status)
  window.update_idletasks()
  window.update()

window = tkinter.Tk()
window.title("Tacx calibration")
window.geometry("600x300")
tkinter.Label(window, text="Status: ").grid(row=1,column=1, sticky="E")
tkinter.Label(window, text="Calibrated: ").grid(row=2,column=1, sticky="E")
tkinter.Label(window, text="Resistance Level: ").grid(row=3,column=1, sticky="E")
tkinter.Label(window, text="Speed: ").grid(row=4,column=1, sticky="E")
tkinter.Label(window, text="Power: ").grid(row=5,column=1, sticky="E")
tkinter.Label(window, text="Instructions: ").grid(row=6,column=1, sticky="E")

status_label = tkinter.Label(window, text="None")
status_label.grid(row=1,column=2, sticky="W")

calibrated_label = tkinter.Label(window, text="False")
calibrated_label.grid(row=2,column=2, sticky="W")

resistance_label = tkinter.Label(window, text="None")
resistance_label.grid(row=3,column=2, sticky="W")

speed_label = tkinter.Label(window, text="None")
speed_label.grid(row=4,column=2, sticky="W")

power_label = tkinter.Label(window, text="None")
power_label.grid(row=5,column=2, sticky="W")

instructions_label = tkinter.Label(window, text="None")
instructions_label.grid(row=6,column=2, sticky="W")

window.update_idletasks()
window.update()

product=0
idpl = [0x1932, 0x1942]#iflow, fortius
for idp in idpl:
  dev = usb.core.find(idVendor=0x3561, idProduct=idp) #find iflow device
  if dev != None:
    product=idp
    break

if product == 0:
  print "Trainer not found"
  sys.exit()

#initialise TACX USB device
byte_ints = [2,0,0,0] # will not read cadence until initialisation byte is sent
byte_str = "".join(chr(n) for n in byte_ints)
dev.write(0x02,byte_str)
time.sleep(1)

###windows###
if os.name == 'nt':
  found_available_ant_stick= True
  try:
    dev_ant = usb.core.find(idVendor=0x0fcf, idProduct=0x1009) #get ANT+ stick (garmin)
    dev_ant.set_configuration() #set active configuration
    try:#check if in use
      stringl=["a4 01 4a 00 ef 00 00"]#reset system
      ant.send(stringl, dev_ant, debug)
      print "Using Garmin dongle..."
    except usb.core.USBError:
      print "Garmin Device is in use"
      found_available_ant_stick = False
  except AttributeError:
    print "No Garmin Device found"
    found_available_ant_stick = False

  if found_available_ant_stick == False:
    found_available_ant_stick = True
    try:
      dev_ant = usb.core.find(idVendor=0x0fcf, idProduct=0x1008) #get ANT+ stick (suunto)
      dev_ant.set_configuration() #set active configuration   
      try:#check if in use
        stringl=["a4 01 4a 00 ef 00 00"]#reset system
        ant.send(stringl, dev_ant, False)
        print "Using Suunto dongle..."
      except usb.core.USBError:
        print "Suunto Device is in use"
        found_available_ant_stick = False
    except AttributeError:  
      print "No Suunto Device found"
      found_available_ant_stick = False

  if found_available_ant_stick == False:
    print "No available ANT+ device. Retry after quitting Garmin Express or other application that uses ANT+. If still fails then remove dongles for 10s then reinsert"
    sys.exit()
  

###Linux###
elif os.name == 'posix':
  #Find ANT+ USB stick on serial (Linux)
  ant_stick_found = False
  for p in glob.glob('/dev/ttyUSB*'):
    dev_ant = serial.Serial(p, 19200, rtscts=True,dsrdtr=True)
    dev_ant.timeout = 0.1
    dev_ant.write(binascii.unhexlify("a4014a00ef0000")) #probe with reset command
    reply = binascii.hexlify(dev_ant.read(size=256))
    if reply == "a4016f20ea" or reply == "a4016f00ca":#found ANT+ stick
      serial_port=p
      ant_stick_found = True
    else: dev_ant.close()#not correct reply to reset
    if ant_stick_found == True  : break

  if ant_stick_found == False:
    print 'Could not find ANT+ device. Check output of "lsusb | grep 0fcf" and "ls /dev/ttyUSB*"'
    sys.exit()
    
  
else:
  print "OS not Supported"
  sys.exit() 

ant.calibrate(dev_ant)#calibrate ANT+ dongle

#calibrate as power sensor
string=[
"a4 03 42 00 00 00 e5 00 00", #42 assign channel
"a4 05 51 00 00 00 0b 00 fb 00 00", #51 set channel id, 0b device=power sensor
"a4 02 45 00 39 da 00 00", #45 channel freq
"a4 03 43 00 f6 1f 0d 00 00", #43 msg period
"a4 02 71 00 00 d7 00 00", #71 Set Proximity Search chann number 0 search threshold 0
"a4 02 63 00 0a cf 00 00", #63 low priority search channel number 0 timeout 0
"a4 02 44 00 02 e0 00 00", #44 Host Command/Response 
"a4 01 4b 00 ee 00 00" #4b ANT_OpenChannel message ID channel = 0 D00001229_Fitness_Modules_ANT+_Application_Note_Rev_3.0.pdf
]
ant.send(string, dev_ant, True)

power_meter = False
calibrated = False
packets_rx=0
resistance_level=0
target_power=0
power=0
speed=0

try:
  while True:
    reply = {}
    last_measured_time = time.time() * 1000
    #add wait so we only send every 250ms
    try:
      #get power data
      read_val = binascii.hexlify(dev_ant.read(0x81,64))
      if read_val[8:10]=="10":#a4 09 4e 00 10 ec ff 00 be 4e 00 00 10 #10 power page be 4e accumulated power 00 00 iunstant power
        power = int(read_val[22:24],16)*16 + int(read_val[20:22],16)
        print read_val, power
        power_meter = True
        
        
      elif read_val[0:10]=="a4094f0001":#calibration response
        if read_val[10:12]=="ac":
          update_status(status_label, "Calibration successful")
          update_status(instructions_label, "Resume pedalling")
          calibrated = True
          update_status(calibrated_label, "True")
        elif read_val[10:12]=="af":
          update_status(status_label, "Calibration failed")
        else:
          update_status(status_label, "Calibration unknown response")
      
      
      if power_meter:
        packets_rx += 1
        if not calibrated and packets_rx<40:
          update_status(status_label, "Power data received - waiting to calibrate")
          update_status(instructions_label, "Keep pedalling")
        if packets_rx == 40:
          update_status(status_label, "Starting calibration")
          update_status(instructions_label, "STOP PEDALLING- power meter calibration in 10 seconds.\nPut pedals into position as instructed by your power meter manufacturer")
        elif packets_rx == 80:
          update_status(status_label, "Calibrating...")
          update_status(instructions_label, "Do not pedal")
          ant.send(["a4 09 4f 00 01 aa ff ff ff ff ff ff 49 00 00"], dev_ant, True)
      else:
        update_status(status_label, "No data from power meter yet")
        update_status(instructions_label, "Keep pedalling")
      
      #receive data from trainer
      data = dev.read(0x82,64) #get data from device
      #print "TRAINER",data
      if len(data)>40:
        fs = int(data[33])<<8 | int(data[32])
        speed = round(fs/2.8054/100,1)#speed kph
        
        #send data to trainer
        r6=int(T1932_calibration.reslist[resistance_level])>>8 & 0xff #byte6
        r5=int(T1932_calibration.reslist[resistance_level]) & 0xff #byte 5
        #echo pedal cadence back to trainer
        if len(data) > 40:
          pedecho = data[42]
        else:
          pedecho = 0
        byte_ints = [0x01, 0x08, 0x01, 0x00, r5, r6, pedecho, 0x00 ,0x02, 0x52, 0x10, 0x04]
        byte_str = "".join(chr(n) for n in byte_ints)
        dev.write(0x02,byte_str)#send data to device
        
        if packets_rx % 50 == 0 and packets_rx > 150:
          target_power += 50
          if target_power == 500:
            target_power = 50
            resistance_level += 1
          if resistance_level == 14:
            print "Power calibration file created"
            sys.exit()
          update_status(status_label, "Creating calibration file")
          update_status(instructions_label, "Aim for a target power of %s watts. It doesn't matter if you don't hit it exactly or can't achieve it at all!" % target_power)              
          
        update_status(resistance_label, "%s" % resistance_level)
        update_status(speed_label, "%skph" % speed)
        update_status(power_label, "%sW" % power)
          
      else:
        update_status(status_label, "Trainer possibly not powered up")
    except usb.core.USBError:
      update_status(status_label, "No data received from power meter")
      update_status(instructions_label, "Start pedalling")
      power_meter = False
     
    time_to_process_loop = time.time() * 1000 - last_measured_time
    sleep_time = 0.25 - (time_to_process_loop)/1000
    if sleep_time < 0: sleep_time = 0
    time.sleep(sleep_time)
except KeyboardInterrupt: # interrupt power data sending with ctrl c, make sure script continues to reset device
    pass

ant.send(["a4 01 4a 00 ef 00 00"],dev_ant, False)#reset ANT+ dongle
